#!/bin/bash

###############################################################################
# LocalStack Deployment Script for Virtual Me Chatbot
# This script deploys the Lambda function and API Gateway to LocalStack
###############################################################################

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Virtual Me - LocalStack Deployment${NC}"
echo -e "${BLUE}========================================${NC}"

# Configuration
FUNCTION_NAME="virtual-me-chatbot"
RUNTIME="python3.11"
HANDLER="lambda_function.lambda_handler"
ROLE_NAME="virtual-me-lambda-role"
API_NAME="virtual-me-api"
REGION="us-east-1"
LOCALSTACK_ENDPOINT="http://localhost:4566"

# Check if LocalStack is running
echo -e "\n${BLUE}[1/7]${NC} Checking LocalStack status..."
if ! curl -s ${LOCALSTACK_ENDPOINT}/_localstack/health > /dev/null; then
    echo -e "${RED}Error: LocalStack is not running!${NC}"
    echo -e "Please start LocalStack with: ${GREEN}docker-compose up -d${NC}"
    exit 1
fi
echo -e "${GREEN}✓ LocalStack is running${NC}"

# Check if OpenAI API key is set
echo -e "\n${BLUE}[2/7]${NC} Checking OpenAI API key..."
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}Error: OPENAI_API_KEY environment variable is not set!${NC}"
    echo -e "Please set it with: ${GREEN}export OPENAI_API_KEY=your-key-here${NC}"
    exit 1
fi
echo -e "${GREEN}✓ OpenAI API key is set${NC}"

# Create deployment package
echo -e "\n${BLUE}[3/7]${NC} Creating deployment package..."
rm -rf package deployment.zip
mkdir -p package

# Install dependencies
pip install -q -r requirements.txt -t package/

# Copy Lambda function and resume
cp lambda_function.py package/
cp resume.md package/

# Create zip file
cd package
zip -q -r ../deployment.zip .
cd ..
echo -e "${GREEN}✓ Deployment package created${NC}"

# Create IAM role (LocalStack doesn't enforce permissions, but we need an ARN)
echo -e "\n${BLUE}[4/7]${NC} Creating IAM role..."
ROLE_ARN=$(aws --endpoint-url=${LOCALSTACK_ENDPOINT} iam create-role \
    --role-name ${ROLE_NAME} \
    --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}' \
    --query 'Role.Arn' \
    --output text 2>/dev/null || \
    aws --endpoint-url=${LOCALSTACK_ENDPOINT} iam get-role \
    --role-name ${ROLE_NAME} \
    --query 'Role.Arn' \
    --output text)
echo -e "${GREEN}✓ IAM role created: ${ROLE_ARN}${NC}"

# Create or update Lambda function
echo -e "\n${BLUE}[5/7]${NC} Deploying Lambda function..."
if aws --endpoint-url=${LOCALSTACK_ENDPOINT} lambda get-function --function-name ${FUNCTION_NAME} &>/dev/null; then
    echo "Function exists, updating code..."
    aws --endpoint-url=${LOCALSTACK_ENDPOINT} lambda update-function-code \
        --function-name ${FUNCTION_NAME} \
        --zip-file fileb://deployment.zip \
        > /dev/null
else
    echo "Creating new function..."
    aws --endpoint-url=${LOCALSTACK_ENDPOINT} lambda create-function \
        --function-name ${FUNCTION_NAME} \
        --runtime ${RUNTIME} \
        --handler ${HANDLER} \
        --role ${ROLE_ARN} \
        --zip-file fileb://deployment.zip \
        --timeout 30 \
        --memory-size 512 \
        --environment Variables="{OPENAI_API_KEY=${OPENAI_API_KEY}}" \
        > /dev/null
fi
echo -e "${GREEN}✓ Lambda function deployed${NC}"

# Update Lambda environment variables
echo -e "\n${BLUE}[6/7]${NC} Updating environment variables..."
aws --endpoint-url=${LOCALSTACK_ENDPOINT} lambda update-function-configuration \
    --function-name ${FUNCTION_NAME} \
    --environment Variables="{OPENAI_API_KEY=${OPENAI_API_KEY}}" \
    > /dev/null
echo -e "${GREEN}✓ Environment variables updated${NC}"

# Create API Gateway
echo -e "\n${BLUE}[7/7]${NC} Creating API Gateway..."

# Create HTTP API
API_ID=$(aws --endpoint-url=${LOCALSTACK_ENDPOINT} apigatewayv2 create-api \
    --name ${API_NAME} \
    --protocol-type HTTP \
    --query 'ApiId' \
    --output text 2>/dev/null || echo "")

if [ -z "$API_ID" ]; then
    # API might already exist, get its ID
    API_ID=$(aws --endpoint-url=${LOCALSTACK_ENDPOINT} apigatewayv2 get-apis \
        --query "Items[?Name=='${API_NAME}'].ApiId" \
        --output text)
fi

echo "API ID: ${API_ID}"

# Create integration
INTEGRATION_ID=$(aws --endpoint-url=${LOCALSTACK_ENDPOINT} apigatewayv2 create-integration \
    --api-id ${API_ID} \
    --integration-type AWS_PROXY \
    --integration-uri arn:aws:lambda:${REGION}:000000000000:function:${FUNCTION_NAME} \
    --payload-format-version 2.0 \
    --query 'IntegrationId' \
    --output text)

echo "Integration ID: ${INTEGRATION_ID}"

# Create route for POST /chat
aws --endpoint-url=${LOCALSTACK_ENDPOINT} apigatewayv2 create-route \
    --api-id ${API_ID} \
    --route-key 'POST /chat' \
    --target integrations/${INTEGRATION_ID} \
    > /dev/null

# Create route for OPTIONS (CORS)
aws --endpoint-url=${LOCALSTACK_ENDPOINT} apigatewayv2 create-route \
    --api-id ${API_ID} \
    --route-key 'OPTIONS /chat' \
    --target integrations/${INTEGRATION_ID} \
    > /dev/null

# Create stage
aws --endpoint-url=${LOCALSTACK_ENDPOINT} apigatewayv2 create-stage \
    --api-id ${API_ID} \
    --stage-name prod \
    --auto-deploy \
    > /dev/null

API_ENDPOINT="${LOCALSTACK_ENDPOINT}/restapis/${API_ID}/prod/_user_request_/chat"

echo -e "${GREEN}✓ API Gateway created${NC}"

# Test the Lambda function
echo -e "\n${BLUE}Testing Lambda function...${NC}"
TEST_PAYLOAD='{"body": "{\"messages\": [{\"role\": \"user\", \"text\": \"What is your main expertise?\"}]}"}'
TEST_RESPONSE=$(aws --endpoint-url=${LOCALSTACK_ENDPOINT} lambda invoke \
    --function-name ${FUNCTION_NAME} \
    --payload "${TEST_PAYLOAD}" \
    response.json > /dev/null 2>&1 && cat response.json || echo "Error")

if [[ $TEST_RESPONSE == *"error"* ]]; then
    echo -e "${RED}⚠ Lambda test failed. Check logs with: docker logs virtualme-localstack${NC}"
else
    echo -e "${GREEN}✓ Lambda function is responding${NC}"
fi

# Cleanup
rm -rf package deployment.zip response.json

# Print summary
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n📋 Deployment Summary:"
echo -e "  Function Name: ${GREEN}${FUNCTION_NAME}${NC}"
echo -e "  API Endpoint:  ${GREEN}${API_ENDPOINT}${NC}"
echo -e "\n🔧 Next Steps:"
echo -e "  1. Update ${GREEN}index.html${NC} with the API endpoint above"
echo -e "  2. Open ${GREEN}index.html${NC} in your browser"
echo -e "  3. Start chatting with your Virtual Me!"
echo -e "\n📊 View Logs:"
echo -e "  ${GREEN}docker logs -f virtualme-localstack${NC}"
echo -e "\n🧪 Test Lambda directly:"
echo -e "  ${GREEN}aws --endpoint-url=${LOCALSTACK_ENDPOINT} lambda invoke --function-name ${FUNCTION_NAME} --payload '\$TEST_PAYLOAD' output.json${NC}"
echo ""
