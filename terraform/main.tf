# Virtual Me Chatbot - Terraform Configuration

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = local.common_tags
  }
}

# CloudFront needs certs in us-east-1
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
  default_tags {
    tags = local.common_tags
  }
}

# --- Data Sources ---

data "aws_caller_identity" "current" {}

data "aws_route53_zone" "main" {
  name         = var.domain_name
  private_zone = false
}

# --- Locals ---

locals {
  function_name = "${var.project_name}-${var.environment}"
  api_name      = "${var.project_name}-api-${var.environment}"
  s3_bucket     = "${var.project_name}-frontend-${var.environment}-${data.aws_caller_identity.current.account_id}"

  frontend_fqdn = "${var.frontend_subdomain}.${var.domain_name}"
  api_fqdn      = "${var.api_subdomain}.${var.domain_name}"
  frontend_url  = "https://${local.frontend_fqdn}"
  api_endpoint  = "https://${local.api_fqdn}/chat"

  common_tags = {
    Project     = "VirtualMe"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# --- Lambda Deployment Package ---

resource "null_resource" "lambda_dependencies" {
  triggers = {
    requirements   = filemd5("${path.module}/../requirements.txt")
    src_code       = sha256(join("", [for f in fileset("${path.module}/../src", "**/*.py") : filemd5("${path.module}/../src/${f}")]))
    knowledge_base = sha256(join("", [for f in fileset("${path.module}/../src/knowledge_base", "**/*.md") : filemd5("${path.module}/../src/knowledge_base/${f}")]))
  }

  # Build with Docker to get Linux-compatible binaries
  provisioner "local-exec" {
    command = <<-EOT
      cd ${path.module}/..
      rm -rf package deployment.zip
      mkdir -p package
      docker run --rm --platform linux/amd64 \
        -v "$PWD":/workspace \
        -w /workspace \
        python:3.11-slim \
        /bin/bash -c "pip install -r requirements.txt -t package/ --quiet"
      cp -r src/* package/
      cd package
      zip -q -r ../deployment.zip .
      cd ..
    EOT
  }
}

data "archive_file" "lambda_package" {
  type        = "zip"
  source_dir  = "${path.module}/../package"
  output_path = "${path.module}/../deployment.zip"
  depends_on  = [null_resource.lambda_dependencies]
}

# --- IAM ---

resource "aws_iam_role" "lambda_role" {
  name = "${local.function_name}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "${local.function_name}-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = [
          "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${local.function_name}",
          "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${local.function_name}:*"
        ]
      },
      {
        Effect = "Allow"
        Action = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"]
        Resource = [
          "arn:aws:bedrock:*::foundation-model/*",
          "arn:aws:bedrock:${var.aws_region}:${data.aws_caller_identity.current.account_id}:inference-profile/*"
        ]
      },
      {
        Effect   = "Allow"
        Action   = ["dynamodb:PutItem", "dynamodb:GetItem", "dynamodb:Scan", "dynamodb:Query", "dynamodb:BatchWriteItem"]
        Resource = ["arn:aws:dynamodb:${var.aws_region}:${data.aws_caller_identity.current.account_id}:table/${local.function_name}-vectors"]
      },
      {
        Effect   = "Allow"
        Action   = ["xray:PutTraceSegments", "xray:PutTelemetryRecords"]
        Resource = "*"
      }
    ]
  })
}

# --- S3 for Lambda Deployment ---

resource "aws_s3_bucket" "lambda_deployments" {
  bucket = "${local.function_name}-deployments-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_versioning" "lambda_deployments" {
  bucket = aws_s3_bucket.lambda_deployments.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_object" "lambda_package" {
  bucket = aws_s3_bucket.lambda_deployments.id
  key    = "deployment-${data.archive_file.lambda_package.output_md5}.zip"
  source = data.archive_file.lambda_package.output_path
  etag   = data.archive_file.lambda_package.output_md5
}

# --- Lambda Function ---

resource "aws_lambda_function" "virtual_me" {
  s3_bucket        = aws_s3_bucket.lambda_deployments.id
  s3_key           = aws_s3_object.lambda_package.key
  function_name    = local.function_name
  role             = aws_iam_role.lambda_role.arn
  handler          = "lambda_function.lambda_handler"
  source_code_hash = data.archive_file.lambda_package.output_base64sha256
  runtime          = "python3.11"
  timeout          = 30
  memory_size      = 512

  tracing_config {
    mode = "Active"
  }

  environment {
    variables = {
      LLM_BACKEND       = "bedrock"
      LLM_MODEL         = var.llm_model
      LLM_TEMPERATURE   = var.llm_temperature
      EMBEDDING_BACKEND = "bedrock"
      EMBEDDING_MODEL   = var.embedding_model
      DYNAMODB_TABLE    = aws_dynamodb_table.vectors.name
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic,
    null_resource.lambda_dependencies,
    aws_dynamodb_table.vectors
  ]
}

resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${local.function_name}"
  retention_in_days = var.log_retention_days
}

# --- API Gateway ---

resource "aws_apigatewayv2_api" "virtual_me_api" {
  name          = local.api_name
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = [local.frontend_url]
    allow_methods = ["POST", "OPTIONS"]
    allow_headers = ["content-type"]
    max_age       = 300
  }
}

resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id                 = aws_apigatewayv2_api.virtual_me_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.virtual_me.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "chat_route" {
  api_id    = aws_apigatewayv2_api.virtual_me_api.id
  route_key = "POST /chat"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_apigatewayv2_stage" "prod" {
  api_id      = aws_apigatewayv2_api.virtual_me_api.id
  name        = "prod"
  auto_deploy = true

  default_route_settings {
    throttling_burst_limit = 100
    throttling_rate_limit  = 50
  }

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_logs.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
    })
  }
}

resource "aws_cloudwatch_log_group" "api_logs" {
  name              = "/aws/apigateway/${local.api_name}"
  retention_in_days = var.log_retention_days
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.virtual_me.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.virtual_me_api.execution_arn}/*/*"
}

# --- S3 for Frontend ---

resource "aws_s3_bucket" "frontend" {
  bucket = local.s3_bucket
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket                  = aws_s3_bucket.frontend.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # New OAC access (modern)
      {
        Sid    = "AllowCloudFrontServicePrincipal"
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.frontend.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.frontend.arn
          }
        }
      }
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.frontend]
}

resource "aws_s3_object" "index_html" {
  bucket       = aws_s3_bucket.frontend.id
  key          = "index.html"
  content_type = "text/html"

  content = replace(
    file("${path.module}/../frontend/index.html"),
    "API_ENDPOINT_PLACEHOLDER",
    local.api_endpoint
  )

  etag = filemd5("${path.module}/../frontend/index.html")
}

resource "aws_s3_object" "deepchat_js" {
  bucket       = aws_s3_bucket.frontend.id
  key          = "deepChat.bundle.js"
  source       = "${path.module}/../frontend/deepChat.bundle.js"
  content_type = "application/javascript"
  etag         = filemd5("${path.module}/../frontend/deepChat.bundle.js")
}
