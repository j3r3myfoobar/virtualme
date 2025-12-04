#!/bin/bash
###############################################################################
# Setup Terraform Remote State Backend
#
# This script creates the S3 bucket and DynamoDB table required for
# Terraform remote state management.
#
# Usage:
#   ./scripts/setup-terraform-backend.sh
#
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================================================="
echo "Terraform Remote State Backend Setup"
echo "=========================================================================="
echo ""

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
if [ -z "$ACCOUNT_ID" ]; then
    echo -e "${RED}Error: Could not get AWS account ID. Is AWS CLI configured?${NC}"
    exit 1
fi

echo -e "${GREEN}AWS Account ID: ${ACCOUNT_ID}${NC}"

# Configuration
REGION="eu-west-3"
BUCKET_NAME="virtualme-terraform-state-${ACCOUNT_ID}"
TABLE_NAME="virtualme-terraform-locks"

echo ""
echo "Configuration:"
echo "  Region: ${REGION}"
echo "  S3 Bucket: ${BUCKET_NAME}"
echo "  DynamoDB Table: ${TABLE_NAME}"
echo ""

# Check if bucket already exists
if aws s3 ls "s3://${BUCKET_NAME}" 2>/dev/null; then
    echo -e "${YELLOW}S3 bucket already exists: ${BUCKET_NAME}${NC}"
else
    echo "Creating S3 bucket..."
    aws s3 mb "s3://${BUCKET_NAME}" --region ${REGION}

    # Enable versioning
    echo "Enabling S3 bucket versioning..."
    aws s3api put-bucket-versioning \
        --bucket ${BUCKET_NAME} \
        --versioning-configuration Status=Enabled

    # Enable encryption
    echo "Enabling S3 bucket encryption..."
    aws s3api put-bucket-encryption \
        --bucket ${BUCKET_NAME} \
        --server-side-encryption-configuration '{
            "Rules": [{
                "ApplyServerSideEncryptionByDefault": {
                    "SSEAlgorithm": "AES256"
                }
            }]
        }'

    # Block public access
    echo "Blocking public access..."
    aws s3api put-public-access-block \
        --bucket ${BUCKET_NAME} \
        --public-access-block-configuration \
        "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

    echo -e "${GREEN}✓ S3 bucket created and configured${NC}"
fi

# Check if DynamoDB table already exists
if aws dynamodb describe-table --table-name ${TABLE_NAME} --region ${REGION} 2>/dev/null; then
    echo -e "${YELLOW}DynamoDB table already exists: ${TABLE_NAME}${NC}"
else
    echo "Creating DynamoDB table for state locking..."
    aws dynamodb create-table \
        --table-name ${TABLE_NAME} \
        --attribute-definitions AttributeName=LockID,AttributeType=S \
        --key-schema AttributeName=LockID,KeyType=HASH \
        --billing-mode PAY_PER_REQUEST \
        --region ${REGION} \
        --tags Key=Project,Value=VirtualMe Key=ManagedBy,Value=Script

    echo "Waiting for table to be active..."
    aws dynamodb wait table-exists --table-name ${TABLE_NAME} --region ${REGION}

    echo -e "${GREEN}✓ DynamoDB table created${NC}"
fi

echo ""
echo "=========================================================================="
echo -e "${GREEN}Remote state backend setup complete!${NC}"
echo "=========================================================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Copy the backend configuration file:"
echo "   cd terraform"
echo "   cp backend.tf.example backend.tf"
echo ""
echo "2. Update backend.tf with your account ID:"
echo "   sed -i '' 's/YOUR-ACCOUNT-ID/${ACCOUNT_ID}/g' backend.tf"
echo ""
echo "3. Initialize Terraform with the new backend:"
echo "   terraform init -migrate-state"
echo ""
echo "4. Verify the state is stored remotely:"
echo "   aws s3 ls s3://${BUCKET_NAME}/virtualme/"
echo ""
