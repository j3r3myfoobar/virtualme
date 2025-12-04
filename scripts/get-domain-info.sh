#!/bin/bash

###############################################################################
# Get Domain Information for Terraform Configuration
# This script retrieves ACM certificate ARN and Route53 zone ID
###############################################################################

set -e

DOMAIN="lemaire.tel"
REGION_CLOUDFRONT="us-east-1"  # CloudFront requires certs in us-east-1
REGION_API="eu-west-3"          # API Gateway uses regional cert

echo "=========================================="
echo "Domain Information Retrieval"
echo "=========================================="
echo ""

# Get Route53 Hosted Zone ID
echo "1. Getting Route53 Hosted Zone ID for $DOMAIN..."
ZONE_ID=$(aws route53 list-hosted-zones-by-name \
    --query "HostedZones[?Name=='${DOMAIN}.'].Id" \
    --output text | cut -d'/' -f3)

if [ -z "$ZONE_ID" ]; then
    echo "❌ ERROR: No hosted zone found for $DOMAIN"
    echo "   Please create a Route53 hosted zone first"
    exit 1
fi

echo "✓ Route53 Zone ID: $ZONE_ID"
echo ""

# Get ACM Certificate ARN for CloudFront (us-east-1)
echo "2. Getting ACM Certificate for CloudFront (must be in us-east-1)..."
CERT_ARN_CLOUDFRONT=$(aws acm list-certificates \
    --region $REGION_CLOUDFRONT \
    --query "CertificateSummaryList[?DomainName=='${DOMAIN}' || DomainName=='*.${DOMAIN}'].CertificateArn" \
    --output text | head -1)

if [ -z "$CERT_ARN_CLOUDFRONT" ]; then
    echo "⚠️  WARNING: No ACM certificate found in us-east-1"
    echo "   CloudFront requires a certificate in us-east-1"
    echo ""
    echo "   To create one:"
    echo "   1. Go to AWS Console → ACM → us-east-1 region"
    echo "   2. Request a certificate for: *.lemaire.tel"
    echo "   3. Use DNS validation"
    echo ""
else
    echo "✓ CloudFront Certificate ARN: $CERT_ARN_CLOUDFRONT"
fi
echo ""

# Get ACM Certificate ARN for API Gateway (eu-west-3)
echo "3. Getting ACM Certificate for API Gateway (eu-west-3)..."
CERT_ARN_API=$(aws acm list-certificates \
    --region $REGION_API \
    --query "CertificateSummaryList[?DomainName=='${DOMAIN}' || DomainName=='*.${DOMAIN}'].CertificateArn" \
    --output text | head -1)

if [ -z "$CERT_ARN_API" ]; then
    echo "⚠️  WARNING: No ACM certificate found in eu-west-3"
    echo "   API Gateway custom domain requires a certificate in the same region"
    echo ""
    echo "   To create one:"
    echo "   1. Go to AWS Console → ACM → eu-west-3 region"
    echo "   2. Request a certificate for: *.lemaire.tel"
    echo "   3. Use DNS validation"
    echo ""
else
    echo "✓ API Gateway Certificate ARN: $CERT_ARN_API"
fi
echo ""

# Generate terraform.tfvars content
echo "=========================================="
echo "Terraform Configuration"
echo "=========================================="
echo ""
echo "Add the following to terraform/terraform.tfvars:"
echo ""
cat << EOF
# Domain Configuration
domain_name         = "lemaire.tel"
frontend_subdomain  = "chat"
api_subdomain       = "api"
route53_zone_id     = "$ZONE_ID"

# ACM Certificates
# CloudFront certificate (must be in us-east-1)
acm_certificate_arn = "$CERT_ARN_CLOUDFRONT"

# API Gateway certificate (eu-west-3) - will be fetched in Terraform
# acm_certificate_arn_api = "$CERT_ARN_API"

# AWS Configuration
aws_region    = "eu-west-3"
environment   = "prod"

# Model Configuration
llm_model       = "llama-3.2-3b"
embedding_model = "titan-embed-text-v2"
llm_temperature = "0.3"
EOF
echo ""

# Summary
echo "=========================================="
echo "Summary"
echo "=========================================="
echo ""
echo "Domain: $DOMAIN"
echo "Frontend will be: https://chat.$DOMAIN"
echo "API will be: https://api.$DOMAIN"
echo ""

if [ -n "$CERT_ARN_CLOUDFRONT" ] && [ -n "$CERT_ARN_API" ]; then
    echo "✅ All prerequisites found!"
    echo "   You can proceed with terraform apply"
elif [ -n "$CERT_ARN_CLOUDFRONT" ]; then
    echo "⚠️  CloudFront cert found, but need API Gateway cert in eu-west-3"
    echo "   You can still deploy, but API custom domain won't work yet"
else
    echo "❌ Missing ACM certificate(s)"
    echo "   Please create ACM certificates before deploying"
fi
echo ""
