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
    tags = {
      Project     = "VirtualMe"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

###############################################################################
# Local Variables
###############################################################################

locals {
  function_name = "${var.project_name}-${var.environment}"
  api_name      = "${var.project_name}-api-${var.environment}"
  s3_bucket     = "${var.project_name}-frontend-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

data "aws_caller_identity" "current" {}

###############################################################################
# Lambda Deployment Package
###############################################################################

# Create deployment package with dependencies
resource "null_resource" "lambda_dependencies" {
  triggers = {
    requirements = filemd5("${path.module}/../requirements.txt")
    lambda_code  = filemd5("${path.module}/../src/lambda_function.py")
    resume       = filemd5("${path.module}/../src/resume.md")
  }

  provisioner "local-exec" {
    command = <<-EOT
      cd ${path.module}/..
      rm -rf package deployment.zip
      mkdir -p package
      pip install -r requirements.txt -t package/ --quiet
      cp src/lambda_function.py package/
      cp src/resume.md package/
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

# Custom policy for additional permissions if needed
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
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

###############################################################################
# Lambda Function
###############################################################################

resource "aws_lambda_function" "virtual_me" {
  filename         = data.archive_file.lambda_package.output_path
  function_name    = local.function_name
  role            = aws_iam_role.lambda_role.arn
  handler         = "lambda_function.lambda_handler"
  source_code_hash = data.archive_file.lambda_package.output_base64sha256
  runtime         = "python3.11"
  timeout         = 30
  memory_size     = 512

  environment {
    variables = {
      OPENAI_API_KEY = var.openai_api_key
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic,
    null_resource.lambda_dependencies
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
    allow_origins = ["*"]
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

# Public access settings
resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# Bucket policy for public read
resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.frontend.arn}/*"
      }
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.frontend]
}

# Website configuration
resource "aws_s3_bucket_website_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "index.html"
  }
}

# Upload index.html with API endpoint injected
resource "aws_s3_object" "index_html" {
  bucket       = aws_s3_bucket.frontend.id
  key          = "index.html"
  content_type = "text/html"

  # Replace API endpoint placeholder in HTML
  content = replace(
    file("${path.module}/../frontend/index.html"),
    "API_ENDPOINT_PLACEHOLDER",
    "${aws_apigatewayv2_stage.prod.invoke_url}/chat"
  )

  etag = filemd5("${path.module}/../frontend/index.html")
}

###############################################################################
# Outputs
###############################################################################

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.virtual_me.function_name
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.virtual_me.arn
}

output "api_endpoint" {
  description = "API Gateway endpoint URL"
  value       = "${aws_apigatewayv2_stage.prod.invoke_url}/chat"
}

output "website_url" {
  description = "S3 website URL for the frontend"
  value       = "http://${aws_s3_bucket_website_configuration.frontend.website_endpoint}"
}

output "s3_bucket_name" {
  description = "Name of the S3 bucket hosting the frontend"
  value       = aws_s3_bucket.frontend.id
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group for Lambda function"
  value       = aws_cloudwatch_log_group.lambda_logs.name
}
