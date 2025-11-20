#!/bin/bash

###############################################################################
# AWS Production Deployment Script for Virtual Me Chatbot
# Uses Terraform to provision infrastructure
###############################################################################

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Virtual Me - AWS Production Deployment${NC}"
echo -e "${BLUE}========================================${NC}"

# Check prerequisites
echo -e "\n${BLUE}[1/5]${NC} Checking prerequisites..."

# Check if Terraform is installed
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}Error: Terraform is not installed!${NC}"
    echo -e "Install it from: ${GREEN}https://www.terraform.io/downloads${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Terraform is installed ($(terraform version -json | grep -o '"terraform_version":"[^"]*' | cut -d'"' -f4))${NC}"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed!${NC}"
    echo -e "Install it from: ${GREEN}https://aws.amazon.com/cli/${NC}"
    exit 1
fi
echo -e "${GREEN}✓ AWS CLI is installed${NC}"

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}Error: AWS credentials are not configured!${NC}"
    echo -e "Configure them with: ${GREEN}aws configure${NC}"
    exit 1
fi
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✓ AWS credentials configured (Account: ${ACCOUNT_ID})${NC}"

# Check if terraform.tfvars exists
if [ ! -f "terraform.tfvars" ]; then
    echo -e "${YELLOW}Warning: terraform.tfvars not found!${NC}"
    echo -e "Creating from example..."
    cp terraform.tfvars.example terraform.tfvars
    echo -e "${YELLOW}Please edit terraform.tfvars and add your OpenAI API key, then run this script again.${NC}"
    exit 1
fi

# Check if OpenAI API key is set in tfvars
if grep -q "sk-proj-xxxxxxxxxxxxxxxxxxxxx" terraform.tfvars; then
    echo -e "${RED}Error: Please set your OpenAI API key in terraform.tfvars${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Configuration file found${NC}"

# Initialize Terraform
echo -e "\n${BLUE}[2/5]${NC} Initializing Terraform..."
terraform init -upgrade
echo -e "${GREEN}✓ Terraform initialized${NC}"

# Validate configuration
echo -e "\n${BLUE}[3/5]${NC} Validating Terraform configuration..."
terraform validate
echo -e "${GREEN}✓ Configuration is valid${NC}"

# Plan deployment
echo -e "\n${BLUE}[4/5]${NC} Planning deployment..."
terraform plan -out=tfplan
echo -e "${GREEN}✓ Plan created${NC}"

# Ask for confirmation
echo -e "\n${YELLOW}Review the plan above. Do you want to proceed with deployment?${NC}"
read -p "Type 'yes' to continue: " confirmation

if [ "$confirmation" != "yes" ]; then
    echo -e "${YELLOW}Deployment cancelled.${NC}"
    rm -f tfplan
    exit 0
fi

# Apply configuration
echo -e "\n${BLUE}[5/5]${NC} Deploying to AWS..."
terraform apply tfplan
rm -f tfplan

# Display outputs
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"

# Extract and display key outputs
echo -e "\n📋 ${BLUE}Deployment Summary:${NC}"
terraform output -json > outputs.json

WEBSITE_URL=$(terraform output -raw website_url 2>/dev/null || echo "N/A")
API_ENDPOINT=$(terraform output -raw api_endpoint 2>/dev/null || echo "N/A")
LAMBDA_NAME=$(terraform output -raw lambda_function_name 2>/dev/null || echo "N/A")

echo -e "\n🌐 ${GREEN}Chatbot URL:${NC}"
echo -e "   ${WEBSITE_URL}"

echo -e "\n🔗 ${GREEN}API Endpoint:${NC}"
echo -e "   ${API_ENDPOINT}"

echo -e "\n⚡ ${GREEN}Lambda Function:${NC}"
echo -e "   ${LAMBDA_NAME}"

echo -e "\n📊 ${GREEN}View Logs:${NC}"
echo -e "   aws logs tail /aws/lambda/${LAMBDA_NAME} --follow"

echo -e "\n🎉 ${GREEN}Next Steps:${NC}"
echo -e "   1. Open the chatbot URL in your browser"
echo -e "   2. Start chatting with your Virtual Me!"
echo -e "   3. Monitor logs in CloudWatch"

echo -e "\n💰 ${YELLOW}Cost Estimate:${NC}"
echo -e "   - Lambda: ~\$0.20 per 1M requests + compute time"
echo -e "   - API Gateway: ~\$1.00 per 1M requests"
echo -e "   - S3: ~\$0.023 per GB stored"
echo -e "   - OpenAI: ~\$0.15 per 1M tokens (GPT-4o-mini)"

rm -f outputs.json

echo ""
