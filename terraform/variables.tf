###############################################################################
# Terraform Variables
###############################################################################

variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "eu-west-3"  # Paris region
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"

  validation {
    condition     = can(regex("^(dev|staging|prod)$", var.environment))
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "virtual-me-chatbot"
}

variable "llm_model" {
  description = "LLM model identifier (e.g., llama-3.2-3b for Bedrock)"
  type        = string
  default     = "llama-3.2-3b"
}

variable "embedding_model" {
  description = "Embedding model identifier (e.g., titan-embed-text-v2 for Bedrock)"
  type        = string
  default     = "titan-embed-text-v2"
}

variable "llm_temperature" {
  description = "LLM temperature for response generation (0.0-1.0)"
  type        = string
  default     = "0.3"

  validation {
    condition     = can(tonumber(var.llm_temperature)) && tonumber(var.llm_temperature) >= 0 && tonumber(var.llm_temperature) <= 1
    error_message = "Temperature must be a number between 0.0 and 1.0."
  }
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.log_retention_days)
    error_message = "Log retention days must be a valid CloudWatch retention period."
  }
}

###############################################################################
# Custom Domain Configuration
###############################################################################

variable "domain_name" {
  description = "Root domain name (e.g., lemaire.tel)"
  type        = string
  default     = "lemaire.tel"
}

variable "frontend_subdomain" {
  description = "Subdomain for frontend (e.g., chat)"
  type        = string
  default     = "chat"
}

variable "api_subdomain" {
  description = "Subdomain for API (e.g., api)"
  type        = string
  default     = "api"
}

variable "acm_certificate_arn" {
  description = "ARN of ACM certificate for *.lemaire.tel (must be in us-east-1 for CloudFront)"
  type        = string
  default     = ""  # You'll provide this in terraform.tfvars
}

variable "route53_zone_id" {
  description = "Route53 hosted zone ID for lemaire.tel"
  type        = string
  default     = ""  # You'll provide this in terraform.tfvars
}

variable "enable_custom_domain" {
  description = "Enable custom domain configuration"
  type        = bool
  default     = true
}

###############################################################################
# Deprecated Variables (kept for backward compatibility)
###############################################################################

variable "openai_api_key" {
  description = "DEPRECATED: OpenAI API key (not used in production with Bedrock)"
  type        = string
  sensitive   = true
  default     = ""
}
