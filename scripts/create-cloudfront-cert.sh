#!/bin/bash

###############################################################################
# Create ACM Certificate for CloudFront (us-east-1)
# CloudFront REQUIRES certificates to be in us-east-1 region
###############################################################################

set -e

DOMAIN="lemaire.tel"
WILDCARD_DOMAIN="*.lemaire.tel"
REGION="us-east-1"
ZONE_ID="Z042219115MNG2VU6NRK9"

echo "==========================================="
echo "Creating ACM Certificate for CloudFront"
echo "==========================================="
echo ""
echo "Domain: $DOMAIN"
echo "Wildcard: $WILDCARD_DOMAIN"
echo "Region: $REGION (required for CloudFront)"
echo ""

# Request certificate
echo "Requesting certificate..."
CERT_ARN=$(aws acm request-certificate \
    --region $REGION \
    --domain-name $DOMAIN \
    --subject-alternative-names $WILDCARD_DOMAIN \
    --validation-method DNS \
    --query 'CertificateArn' \
    --output text)

echo "✓ Certificate requested: $CERT_ARN"
echo ""

# Wait a few seconds for validation records to be ready
echo "Waiting for DNS validation records..."
sleep 10

# Get DNS validation records
echo "Getting DNS validation records..."
VALIDATION_RECORDS=$(aws acm describe-certificate \
    --region $REGION \
    --certificate-arn $CERT_ARN \
    --query 'Certificate.DomainValidationOptions[*].[ResourceRecord.Name,ResourceRecord.Type,ResourceRecord.Value]' \
    --output text)

echo "$VALIDATION_RECORDS" | while read NAME TYPE VALUE; do
    echo ""
    echo "Adding DNS validation record to Route53..."
    echo "  Name: $NAME"
    echo "  Type: $TYPE"
    echo "  Value: $VALUE"

    # Create change batch JSON
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

    # Apply the change
    aws route53 change-resource-record-sets \
        --hosted-zone-id $ZONE_ID \
        --change-batch "$CHANGE_BATCH" \
        --query 'ChangeInfo.Id' \
        --output text > /dev/null

    echo "  ✓ DNS record added"
done

echo ""
echo "==========================================="
echo "Certificate Creation Complete!"
echo "==========================================="
echo ""
echo "Certificate ARN: $CERT_ARN"
echo ""
echo "⏳ DNS validation in progress..."
echo "   This usually takes 5-30 minutes"
echo ""
echo "You can check the status with:"
echo "  aws acm describe-certificate --region us-east-1 --certificate-arn $CERT_ARN --query 'Certificate.Status'"
echo ""
echo "Or wait for validation:"
echo "  aws acm wait certificate-validated --region us-east-1 --certificate-arn $CERT_ARN"
echo ""
echo "Once validated, add this to terraform/terraform.tfvars:"
echo "  acm_certificate_arn = \"$CERT_ARN\""
echo ""
