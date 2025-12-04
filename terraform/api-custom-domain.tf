###############################################################################
# API Gateway Custom Domain Configuration
# Sets up api.lemaire.tel for the API Gateway
###############################################################################

locals {
  api_domain_name = var.enable_custom_domain ? "${var.api_subdomain}.${var.domain_name}" : null
}

###############################################################################
# API Gateway Custom Domain
###############################################################################

resource "aws_apigatewayv2_domain_name" "api" {
  count = var.enable_custom_domain ? 1 : 0

  domain_name = local.api_domain_name

  domain_name_configuration {
    certificate_arn = var.acm_certificate_arn
    endpoint_type   = "REGIONAL"
    security_policy = "TLS_1_2"
  }
}

# API Mapping
resource "aws_apigatewayv2_api_mapping" "api" {
  count = var.enable_custom_domain ? 1 : 0

  api_id      = aws_apigatewayv2_api.virtual_me_api.id
  domain_name = aws_apigatewayv2_domain_name.api[0].id
  stage       = aws_apigatewayv2_stage.prod.id
}

###############################################################################
# Route53 DNS Record for API
###############################################################################

resource "aws_route53_record" "api" {
  count = var.enable_custom_domain ? 1 : 0

  zone_id = var.route53_zone_id
  name    = local.api_domain_name
  type    = "A"

  alias {
    name                   = aws_apigatewayv2_domain_name.api[0].domain_name_configuration[0].target_domain_name
    zone_id                = aws_apigatewayv2_domain_name.api[0].domain_name_configuration[0].hosted_zone_id
    evaluate_target_health = false
  }
}

###############################################################################
# Outputs
###############################################################################

output "api_custom_domain" {
  description = "Custom API domain name"
  value       = var.enable_custom_domain ? "https://${local.api_domain_name}" : null
}

output "api_custom_domain_status" {
  description = "Status of the custom domain"
  value       = var.enable_custom_domain ? aws_apigatewayv2_domain_name.api[0].domain_name_configuration[0].hosted_zone_id : "Custom domain disabled"
}
