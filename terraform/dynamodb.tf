###############################################################################
# DynamoDB Table for Vector Storage
# Replaces FAISS for persistent vector storage
###############################################################################

resource "aws_dynamodb_table" "vectors" {
  name         = "${local.function_name}-vectors"
  billing_mode = "PAY_PER_REQUEST"  # Serverless pricing

  hash_key = "id"

  attribute {
    name = "id"
    type = "S"
  }

  # Enable point-in-time recovery for data protection
  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name        = "Virtual Me Vector Storage"
    Purpose     = "Stores document embeddings for RAG"
    CostCenter  = "AI/ML"
  }
}

# Output the table name for reference
output "dynamodb_table_name" {
  description = "Name of the DynamoDB table for vectors"
  value       = aws_dynamodb_table.vectors.name
}

output "dynamodb_table_arn" {
  description = "ARN of the DynamoDB table"
  value       = aws_dynamodb_table.vectors.arn
}
