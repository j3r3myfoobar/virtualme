###############################################################################
# Virtual Me Chatbot - Terraform Configuration
# Provisions AWS Lambda, API Gateway, S3, and IAM resources
###############################################################################

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

# Provider for us-east-1 (required for CloudFront ACM certificates)
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"

  default_tags {
    tags = local.common_tags
  }
}

###############################################################################
# Data Sources
###############################################################################

data "aws_caller_identity" "current" {}

# Route53 Zone for domain
data "aws_route53_zone" "main" {
  name         = var.domain_name
  private_zone = false
}

###############################################################################
# Local Variables
###############################################################################

locals {
  # Resource naming
  function_name = "${var.project_name}-${var.environment}"
  api_name      = "${var.project_name}-api-${var.environment}"
  s3_bucket     = "${var.project_name}-frontend-${var.environment}-${data.aws_caller_identity.current.account_id}"

  # Domain configuration (computed from variables)
  frontend_fqdn = "${var.frontend_subdomain}.${var.domain_name}"
  api_fqdn      = "${var.api_subdomain}.${var.domain_name}"
  frontend_url  = "https://${local.frontend_fqdn}"
  api_endpoint  = "https://${local.api_fqdn}/chat"

  # Common tags for providers
  common_tags = {
    Project     = "VirtualMe"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

###############################################################################
# Lambda Deployment Package
###############################################################################

# Create deployment package with dependencies
resource "null_resource" "lambda_dependencies" {
  triggers = {
    requirements   = filemd5("${path.module}/../requirements.txt")
    lambda_code    = filemd5("${path.module}/../src/lambda_function.py")
    knowledge_base = filemd5("${path.module}/../src/knowledge_base/resume.md")
  }

  provisioner "local-exec" {
    command = <<-EOT
      cd ${path.module}/..
      rm -rf package deployment.zip
      mkdir -p package
      # Use Docker to build with Linux binaries for Lambda compatibility
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

  depends_on = [null_resource.lambda_dependencies]
}

###############################################################################
# IAM Role for Lambda
###############################################################################

resource "aws_iam_role" "lambda_role" {
  name = "${local.function_name}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Attach basic Lambda execution policy
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Custom policy for Lambda permissions
resource "aws_iam_role_policy" "lambda_policy" {
  name = "${local.function_name}-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = [
          "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${local.function_name}",
          "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${local.function_name}:*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = [
          # Allow access to foundation models in all regions (inference profiles may route to different regions)
          "arn:aws:bedrock:*::foundation-model/*",
          # Allow access to inference profiles in the deployment region
          "arn:aws:bedrock:${var.aws_region}:${data.aws_caller_identity.current.account_id}:inference-profile/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:Scan",
          "dynamodb:Query",
          "dynamodb:BatchWriteItem"
        ]
        Resource = [
          "arn:aws:dynamodb:${var.aws_region}:${data.aws_caller_identity.current.account_id}:table/${local.function_name}-vectors"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords"
        ]
        Resource = "*"
      }
    ]
  })
}

###############################################################################
# S3 Bucket for Lambda Deployment Package
###############################################################################

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

###############################################################################
# Lambda Function
###############################################################################

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

  # Enable X-Ray tracing for debugging and performance monitoring
  tracing_config {
    mode = "Active"
  }

  environment {
    variables = {
      # LLM Configuration
      LLM_BACKEND     = "bedrock"
      LLM_MODEL       = var.llm_model
      LLM_TEMPERATURE = var.llm_temperature

      # Embedding Configuration
      EMBEDDING_BACKEND = "bedrock"
      EMBEDDING_MODEL   = var.embedding_model

      # DynamoDB Configuration (for vector storage)
      DYNAMODB_TABLE = aws_dynamodb_table.vectors.name

      # Note: AWS_REGION and AWS_DEFAULT_REGION are automatically set by Lambda runtime
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic,
    null_resource.lambda_dependencies,
    aws_dynamodb_table.vectors
  ]
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${local.function_name}"
  retention_in_days = var.log_retention_days
}

###############################################################################
# API Gateway HTTP API
###############################################################################

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

# Lambda Integration
resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id           = aws_apigatewayv2_api.virtual_me_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.virtual_me.invoke_arn

  payload_format_version = "2.0"
}

# POST /chat route
resource "aws_apigatewayv2_route" "chat_route" {
  api_id    = aws_apigatewayv2_api.virtual_me_api.id
  route_key = "POST /chat"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

# Production stage
resource "aws_apigatewayv2_stage" "prod" {
  api_id      = aws_apigatewayv2_api.virtual_me_api.id
  name        = "prod"
  auto_deploy = true

  # Throttling configuration
  default_route_settings {
    throttling_burst_limit = 100 # Maximum concurrent requests
    throttling_rate_limit  = 50  # Requests per second
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

# CloudWatch Log Group for API Gateway
resource "aws_cloudwatch_log_group" "api_logs" {
  name              = "/aws/apigateway/${local.api_name}"
  retention_in_days = var.log_retention_days
}

# Lambda permission for API Gateway
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.virtual_me.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.virtual_me_api.execution_arn}/*/*"
}

###############################################################################
# S3 Bucket for Static Website Hosting
###############################################################################

resource "aws_s3_bucket" "frontend" {
  bucket = local.s3_bucket
}

# Block all public access - CloudFront OAI will access privately
resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Bucket policy - Only allow CloudFront OAI to read objects
resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "CloudFrontReadGetObject"
        Effect = "Allow"
        Principal = {
          AWS = aws_cloudfront_origin_access_identity.frontend.iam_arn
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.frontend.arn}/*"
      }
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.frontend]
}

# Upload index.html with API endpoint injected
resource "aws_s3_object" "index_html" {
  bucket       = aws_s3_bucket.frontend.id
  key          = "index.html"
  content_type = "text/html"

  # Replace API endpoint placeholder (handles all occurrences)
  content = replace(
    file("${path.module}/../frontend/index.html"),
    "API_ENDPOINT_PLACEHOLDER",
    local.api_endpoint
  )

  etag = filemd5("${path.module}/../frontend/index.html")
}

# Outputs are defined in outputs.tf
