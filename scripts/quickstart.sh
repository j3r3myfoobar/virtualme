#!/bin/bash

###############################################################################
# Quick Start Script for Virtual Me Chatbot
# This script helps you quickly set up and test locally
###############################################################################

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Virtual Me - Quick Start${NC}"
echo -e "${BLUE}========================================${NC}"

# Check if OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "\n${YELLOW}OpenAI API key not found in environment.${NC}"
    read -p "Enter your OpenAI API key: " api_key
    export OPENAI_API_KEY="$api_key"
fi

# Check Python
echo -e "\n${BLUE}[1/3]${NC} Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python is installed${NC}"

# Install dependencies
echo -e "\n${BLUE}[2/3]${NC} Installing dependencies..."
pip install -q -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Run test
echo -e "\n${BLUE}[3/3]${NC} Testing Lambda function..."
cd src && python lambda_function.py
echo -e "\n${GREEN}✓ Test completed!${NC}"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Quick Start Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n🎯 ${BLUE}Next Steps:${NC}"
echo -e "  ${GREEN}Option 1 - Deploy to LocalStack:${NC}"
echo -e "    1. docker-compose up -d"
echo -e "    2. ./scripts/localstack-deploy.sh"
echo -e ""
echo -e "  ${GREEN}Option 2 - Deploy to AWS:${NC}"
echo -e "    1. cd terraform"
echo -e "    2. cp terraform.tfvars.example terraform.tfvars"
echo -e "    3. Edit terraform.tfvars with your API key"
echo -e "    4. ../scripts/aws-deploy.sh"
echo ""
