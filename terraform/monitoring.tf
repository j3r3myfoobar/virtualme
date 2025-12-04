###############################################################################
# CloudWatch Alarms and Monitoring
###############################################################################

# SNS Topic for alarm notifications (optional - configure subscription manually)
resource "aws_sns_topic" "alarms" {
  name = "${local.function_name}-alarms"

  tags = {
    Name = "Virtual Me Alarms"
  }
}

###############################################################################
# Lambda CloudWatch Alarms
###############################################################################

# Alarm: Lambda Errors
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${local.function_name}-errors"
  alarm_description   = "Alert when Lambda function has errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 60
  statistic           = "Sum"
  threshold           = 5
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.virtual_me.function_name
  }

  alarm_actions = [aws_sns_topic.alarms.arn]
}

# Alarm: Lambda Throttles
resource "aws_cloudwatch_metric_alarm" "lambda_throttles" {
  alarm_name          = "${local.function_name}-throttles"
  alarm_description   = "Alert when Lambda function is throttled"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Throttles"
  namespace           = "AWS/Lambda"
  period              = 60
  statistic           = "Sum"
  threshold           = 0
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.virtual_me.function_name
  }

  alarm_actions = [aws_sns_topic.alarms.arn]
}

# Alarm: Lambda Duration (performance)
resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  alarm_name          = "${local.function_name}-duration"
  alarm_description   = "Alert when Lambda duration is consistently high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = 60
  statistic           = "Average"
  threshold           = 25000  # 25 seconds (close to 30s timeout)
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.virtual_me.function_name
  }

  alarm_actions = [aws_sns_topic.alarms.arn]
}

# Alarm: Lambda Concurrent Executions
resource "aws_cloudwatch_metric_alarm" "lambda_concurrent_executions" {
  alarm_name          = "${local.function_name}-concurrent-executions"
  alarm_description   = "Alert when concurrent executions are high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ConcurrentExecutions"
  namespace           = "AWS/Lambda"
  period              = 60
  statistic           = "Maximum"
  threshold           = 50
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.virtual_me.function_name
  }

  alarm_actions = [aws_sns_topic.alarms.arn]
}

###############################################################################
# API Gateway CloudWatch Alarms
###############################################################################

# Alarm: API Gateway 5xx Errors
resource "aws_cloudwatch_metric_alarm" "api_5xx_errors" {
  alarm_name          = "${local.api_name}-5xx-errors"
  alarm_description   = "Alert when API Gateway has server errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "5XXError"
  namespace           = "AWS/ApiGateway"
  period              = 60
  statistic           = "Sum"
  threshold           = 5
  treat_missing_data  = "notBreaching"

  dimensions = {
    ApiId = aws_apigatewayv2_api.virtual_me_api.id
  }

  alarm_actions = [aws_sns_topic.alarms.arn]
}

# Alarm: API Gateway 4xx Errors (client errors)
resource "aws_cloudwatch_metric_alarm" "api_4xx_errors" {
  alarm_name          = "${local.api_name}-4xx-errors"
  alarm_description   = "Alert when API Gateway has many client errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "4XXError"
  namespace           = "AWS/ApiGateway"
  period              = 300  # 5 minutes
  statistic           = "Sum"
  threshold           = 50  # Higher threshold for client errors
  treat_missing_data  = "notBreaching"

  dimensions = {
    ApiId = aws_apigatewayv2_api.virtual_me_api.id
  }

  alarm_actions = [aws_sns_topic.alarms.arn]
}

###############################################################################
# Outputs
###############################################################################

output "sns_topic_arn" {
  description = "SNS topic ARN for alarm notifications"
  value       = aws_sns_topic.alarms.arn
}

output "alarm_names" {
  description = "List of CloudWatch alarm names"
  value = [
    aws_cloudwatch_metric_alarm.lambda_errors.alarm_name,
    aws_cloudwatch_metric_alarm.lambda_throttles.alarm_name,
    aws_cloudwatch_metric_alarm.lambda_duration.alarm_name,
    aws_cloudwatch_metric_alarm.lambda_concurrent_executions.alarm_name,
    aws_cloudwatch_metric_alarm.api_5xx_errors.alarm_name,
    aws_cloudwatch_metric_alarm.api_4xx_errors.alarm_name,
  ]
}
