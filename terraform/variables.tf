###############################################################################
# Terraform Variables
###############################################################################

variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
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

variable "openai_api_key" {
  description = "OpenAI API key (optional - only needed if using OpenAI backend locally)"
  type        = string
  sensitive   = true
  default     = ""
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
