#!/bin/bash

###############################################################################
# Domain Setup Script
# Retrieves domain info and creates ACM certificates if needed
###############################################################################

set -e

DOMAIN="lemaire.tel"
REGION_CLOUDFRONT="us-east-1"  # CloudFront requires certs in us-east-1
REGION_API="eu-west-3"          # API Gateway uses regional cert

echo "==========================================="
echo "Domain Setup for Virtual Me"
echo "==========================================="
echo ""
echo "Domain: $DOMAIN"
echo "Frontend: https://chat.$DOMAIN"
echo "API: https://api.$DOMAIN"
echo ""

# Step 1: Get Route53 Hosted Zone ID

echo "1. Getting Route53 Hosted Zone ID..."
ZONE_ID=$(aws route53 list-hosted-zones-by-name \
    --query "HostedZones[?Name=='${DOMAIN}.'].Id" \
    --output text | cut -d'/' -f3)

if [ -z "$ZONE_ID" ]; then
    echo "   ERROR: No hosted zone found for $DOMAIN"
    echo "   Please create a Route53 hosted zone first"
    exit 1
fi

echo "   Route53 Zone ID: $ZONE_ID"
echo ""

# Step 2: Check/Create CloudFront Certificate (us-east-1)

echo "2. Checking ACM Certificate for CloudFront (us-east-1)..."
CERT_ARN_CLOUDFRONT=$(aws acm list-certificates \
    --region $REGION_CLOUDFRONT \
    --query "CertificateSummaryList[?DomainName=='${DOMAIN}' || DomainName=='*.${DOMAIN}'].CertificateArn" \
    --output text | head -1)

if [ -z "$CERT_ARN_CLOUDFRONT" ]; then
    echo "   No certificate found. Creating one..."

    # Request certificate
    CERT_ARN_CLOUDFRONT=$(aws acm request-certificate \
        --region $REGION_CLOUDFRONT \
        --domain-name $DOMAIN \
        --subject-alternative-names "*.${DOMAIN}" \
        --validation-method DNS \
        --query 'CertificateArn' \
        --output text)

    echo "   Certificate requested: $CERT_ARN_CLOUDFRONT"

    # Wait for validation records
    echo "   Waiting for DNS validation records..."
    sleep 10

    # Add DNS validation records to Route53
    VALIDATION_RECORDS=$(aws acm describe-certificate \
        --region $REGION_CLOUDFRONT \
        --certificate-arn $CERT_ARN_CLOUDFRONT \
        --query 'Certificate.DomainValidationOptions[*].[ResourceRecord.Name,ResourceRecord.Type,ResourceRecord.Value]' \
        --output text)

    echo "$VALIDATION_RECORDS" | while read NAME TYPE VALUE; do
        [ -z "$NAME" ] && continue

        CHANGE_BATCH=$(cat <<EOF
{
  "Changes": [{
    "Action": "UPSERT",
    "ResourceRecordSet": {
      "Name": "$NAME",
      "Type": "$TYPE",
      "TTL": 300,
      "ResourceRecords": [{"Value": "$VALUE"}]
    }
  }]
}
EOF
)
        aws route53 change-resource-record-sets \
            --hosted-zone-id $ZONE_ID \
            --change-batch "$CHANGE_BATCH" \
            --query 'ChangeInfo.Id' \
            --output text > /dev/null

        echo "   Added DNS validation record: $NAME"
    done

    echo "   DNS validation in progress (5-30 minutes)..."
else
    echo "   Found: $CERT_ARN_CLOUDFRONT"
fi
echo ""

# Step 3: Check/Create API Gateway Certificate (eu-west-3)

echo "3. Checking ACM Certificate for API Gateway ($REGION_API)..."
CERT_ARN_API=$(aws acm list-certificates \
    --region $REGION_API \
    --query "CertificateSummaryList[?DomainName=='${DOMAIN}' || DomainName=='*.${DOMAIN}'].CertificateArn" \
    --output text | head -1)

if [ -z "$CERT_ARN_API" ]; then
    echo "   No certificate found. Creating one..."

    # Request certificate
    CERT_ARN_API=$(aws acm request-certificate \
        --region $REGION_API \
        --domain-name $DOMAIN \
        --subject-alternative-names "*.${DOMAIN}" \
        --validation-method DNS \
        --query 'CertificateArn' \
        --output text)

    echo "   Certificate requested: $CERT_ARN_API"

    # Wait for validation records
    sleep 10

    # Add DNS validation records to Route53
    VALIDATION_RECORDS=$(aws acm describe-certificate \
        --region $REGION_API \
        --certificate-arn $CERT_ARN_API \
        --query 'Certificate.DomainValidationOptions[*].[ResourceRecord.Name,ResourceRecord.Type,ResourceRecord.Value]' \
        --output text)

    echo "$VALIDATION_RECORDS" | while read NAME TYPE VALUE; do
        [ -z "$NAME" ] && continue

        CHANGE_BATCH=$(cat <<EOF
{
  "Changes": [{
    "Action": "UPSERT",
    "ResourceRecordSet": {
      "Name": "$NAME",
      "Type": "$TYPE",
      "TTL": 300,
      "ResourceRecords": [{"Value": "$VALUE"}]
    }
  }]
}
EOF
)
        aws route53 change-resource-record-sets \
            --hosted-zone-id $ZONE_ID \
            --change-batch "$CHANGE_BATCH" \
            --query 'ChangeInfo.Id' \
            --output text > /dev/null 2>&1 || true

        echo "   Added DNS validation record: $NAME"
    done

    echo "   DNS validation in progress..."
else
    echo "   Found: $CERT_ARN_API"
fi
echo ""

# Output terraform.tfvars Configuration

echo "==========================================="
echo "Terraform Configuration"
echo "==========================================="
echo ""
echo "Add to terraform/terraform.tfvars:"
echo ""
cat << EOF
# Domain Configuration
domain_name        = "$DOMAIN"
frontend_subdomain = "chat"
api_subdomain      = "api"
route53_zone_id    = "$ZONE_ID"

# ACM Certificate (us-east-1 for CloudFront)
acm_certificate_arn = "$CERT_ARN_CLOUDFRONT"

# AWS Configuration
aws_region  = "$REGION_API"
environment = "prod"
EOF
echo ""

# Summary

echo "==========================================="
echo "Summary"
echo "==========================================="
echo ""

if [ -n "$CERT_ARN_CLOUDFRONT" ] && [ -n "$CERT_ARN_API" ]; then
    echo "All prerequisites ready!"
    echo ""
    echo "Next steps:"
    echo "  1. Wait for certificates to validate (check with commands below)"
    echo "  2. Update terraform/terraform.tfvars with values above"
    echo "  3. Run: cd terraform && terraform apply"
else
    echo "Certificates created but may still be validating."
fi

echo ""
echo "Check certificate status:"
echo "  aws acm describe-certificate --region us-east-1 --certificate-arn $CERT_ARN_CLOUDFRONT --query 'Certificate.Status'"
echo "  aws acm describe-certificate --region eu-west-3 --certificate-arn $CERT_ARN_API --query 'Certificate.Status'"
echo ""
