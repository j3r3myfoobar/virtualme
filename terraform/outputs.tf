###############################################################################
# Terraform Outputs
# These values are displayed after successful deployment
###############################################################################

output "deployment_summary" {
  description = "Complete deployment summary"
  value = {
    lambda = {
      function_name = aws_lambda_function.virtual_me.function_name
      function_arn  = aws_lambda_function.virtual_me.arn
      runtime       = aws_lambda_function.virtual_me.runtime
      memory_mb     = aws_lambda_function.virtual_me.memory_size
      timeout_sec   = aws_lambda_function.virtual_me.timeout
    }
    api = {
      # Use custom domain if enabled
      endpoint      = var.enable_custom_domain ? "https://${var.api_subdomain}.${var.domain_name}/chat" : "${aws_apigatewayv2_stage.prod.invoke_url}/chat"
      api_id        = aws_apigatewayv2_api.virtual_me_api.id
      stage_name    = aws_apigatewayv2_stage.prod.name
      custom_domain = var.enable_custom_domain ? "https://${var.api_subdomain}.${var.domain_name}" : "Not configured"
      default_url   = aws_apigatewayv2_stage.prod.invoke_url
    }
    frontend = {
      cloudfront_url = "https://${aws_cloudfront_distribution.frontend.domain_name}"
      custom_domain  = local.frontend_url
      bucket_name    = aws_s3_bucket.frontend.id
      note           = "Accessible via CloudFront only (S3 direct access blocked)"
    }
    monitoring = {
      lambda_logs = aws_cloudwatch_log_group.lambda_logs.name
      api_logs    = aws_cloudwatch_log_group.api_logs.name
    }
  }
}

output "quick_links" {
  description = "Quick access links"
  value = {
    # Frontend URLs
    chatbot_url    = local.frontend_url
    cloudfront_url = "https://${aws_cloudfront_distribution.frontend.domain_name}"

    # API URL (custom domain if enabled)
    api_url = var.enable_custom_domain ? "https://${var.api_subdomain}.${var.domain_name}/chat" : "${aws_apigatewayv2_stage.prod.invoke_url}/chat"

    # AWS Console links
    lambda_console     = "https://console.aws.amazon.com/lambda/home?region=${var.aws_region}#/functions/${aws_lambda_function.virtual_me.function_name}"
    api_console        = "https://console.aws.amazon.com/apigateway/home?region=${var.aws_region}#/apis/${aws_apigatewayv2_api.virtual_me_api.id}"
    cloudfront_console = "https://console.aws.amazon.com/cloudfront/v4/home#/distributions/${aws_cloudfront_distribution.frontend.id}"
    cloudwatch_logs    = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#logsV2:log-groups/log-group/${replace(aws_cloudwatch_log_group.lambda_logs.name, "/", "$252F")}"
    s3_console         = "https://s3.console.aws.amazon.com/s3/buckets/${aws_s3_bucket.frontend.id}"
  }
}

# Individual outputs for easy access
output "frontend_url" {
  description = "Frontend website URL (via CloudFront)"
  value       = local.frontend_url
}

output "api_endpoint" {
  description = "API endpoint URL"
  value       = var.enable_custom_domain ? "https://${var.api_subdomain}.${var.domain_name}/chat" : "${aws_apigatewayv2_stage.prod.invoke_url}/chat"
}

output "custom_domain_info" {
  description = "Custom domain configuration status"
  value = var.enable_custom_domain ? {
    api_domain = "https://${var.api_subdomain}.${var.domain_name}"
    status     = "Configured"
    note       = "API is accessible via custom domain"
    } : {
    status = "Not configured"
    note   = "Using default API Gateway URL"
  }
}
