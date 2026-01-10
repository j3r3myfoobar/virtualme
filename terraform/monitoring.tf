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
# Alarm Configuration
###############################################################################

locals {
  # Lambda alarm configurations
  lambda_alarms = {
    errors = {
      description        = "Alert when Lambda function has errors"
      metric_name        = "Errors"
      statistic          = "Sum"
      threshold          = 5
      evaluation_periods = 2
      period             = 60
    }
    throttles = {
      description        = "Alert when Lambda function is throttled"
      metric_name        = "Throttles"
      statistic          = "Sum"
      threshold          = 0
      evaluation_periods = 1
      period             = 60
    }
    duration = {
      description        = "Alert when Lambda duration is consistently high"
      metric_name        = "Duration"
      statistic          = "Average"
      threshold          = 25000 # 25 seconds (close to 30s timeout)
      evaluation_periods = 3
      period             = 60
    }
    concurrent-executions = {
      description        = "Alert when concurrent executions are high"
      metric_name        = "ConcurrentExecutions"
      statistic          = "Maximum"
      threshold          = 50
      evaluation_periods = 2
      period             = 60
    }
  }

  # API Gateway alarm configurations
  api_alarms = {
    "5xx-errors" = {
      description        = "Alert when API Gateway has server errors"
      metric_name        = "5XXError"
      statistic          = "Sum"
      threshold          = 5
      evaluation_periods = 2
      period             = 60
    }
    "4xx-errors" = {
      description        = "Alert when API Gateway has many client errors"
      metric_name        = "4XXError"
      statistic          = "Sum"
      threshold          = 50 # Higher threshold for client errors
      evaluation_periods = 2
      period             = 300 # 5 minutes
    }
  }
}

###############################################################################
# Lambda CloudWatch Alarms
###############################################################################

resource "aws_cloudwatch_metric_alarm" "lambda" {
  for_each = local.lambda_alarms

  alarm_name          = "${local.function_name}-${each.key}"
  alarm_description   = each.value.description
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = each.value.evaluation_periods
  metric_name         = each.value.metric_name
  namespace           = "AWS/Lambda"
  period              = each.value.period
  statistic           = each.value.statistic
  threshold           = each.value.threshold
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.virtual_me.function_name
  }

  alarm_actions = [aws_sns_topic.alarms.arn]
}

###############################################################################
# API Gateway CloudWatch Alarms
###############################################################################

resource "aws_cloudwatch_metric_alarm" "api" {
  for_each = local.api_alarms

  alarm_name          = "${local.api_name}-${each.key}"
  alarm_description   = each.value.description
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = each.value.evaluation_periods
  metric_name         = each.value.metric_name
  namespace           = "AWS/ApiGateway"
  period              = each.value.period
  statistic           = each.value.statistic
  threshold           = each.value.threshold
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
  value = concat(
    [for k, v in aws_cloudwatch_metric_alarm.lambda : v.alarm_name],
    [for k, v in aws_cloudwatch_metric_alarm.api : v.alarm_name]
  )
}
