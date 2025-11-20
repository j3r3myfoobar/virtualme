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
      endpoint   = "${aws_apigatewayv2_stage.prod.invoke_url}/chat"
      api_id     = aws_apigatewayv2_api.virtual_me_api.id
      stage_name = aws_apigatewayv2_stage.prod.name
    }
    frontend = {
      website_url = "http://${aws_s3_bucket_website_configuration.frontend.website_endpoint}"
      bucket_name = aws_s3_bucket.frontend.id
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
    chatbot_url      = "http://${aws_s3_bucket_website_configuration.frontend.website_endpoint}"
    lambda_console   = "https://console.aws.amazon.com/lambda/home?region=${var.aws_region}#/functions/${aws_lambda_function.virtual_me.function_name}"
    api_console      = "https://console.aws.amazon.com/apigateway/home?region=${var.aws_region}#/apis/${aws_apigatewayv2_api.virtual_me_api.id}"
    cloudwatch_logs  = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#logsV2:log-groups/log-group/${replace(aws_cloudwatch_log_group.lambda_logs.name, "/", "$252F")}"
  }
}
