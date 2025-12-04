# S3 Bucket Security Plan: CloudFront-Only Access

## Current State (Insecure)

**S3 Bucket:** `virtual-me-chatbot-frontend-prod-298290307734`
- ❌ **Publicly accessible** at: http://virtual-me-chatbot-frontend-prod-298290307734.s3-website.eu-west-3.amazonaws.com
- ❌ Public access blocks disabled
- ❌ Public read bucket policy
- ❌ CloudFront uses website endpoint (not secure origin)

**Security Issues:**
1. Anyone can access S3 bucket directly, bypassing CloudFront
2. No access logging for direct S3 access
3. Cannot leverage CloudFront security features (WAF, rate limiting)
4. Potential for unauthorized content scraping

## Desired State (Secure)

**S3 Bucket:**
- ✅ **Private** - not accessible via public URL
- ✅ CloudFront-only access via Origin Access Identity (OAI)
- ✅ Public access blocks enabled
- ✅ Restrictive bucket policy

**CloudFront:**
- ✅ Uses S3 origin (not website endpoint)
- ✅ Authenticates with OAI
- ✅ Only way to access content

## Changes Required

### 1. CloudFront Distribution (`cloudfront.tf`)

**Change origin configuration:**

```hcl
# BEFORE (lines 59-69):
origin {
  domain_name = aws_s3_bucket_website_configuration.frontend.website_endpoint
  origin_id   = "S3-${local.s3_bucket}"

  custom_origin_config {
    http_port              = 80
    https_port             = 443
    origin_protocol_policy = "http-only"
    origin_ssl_protocols   = ["TLSv1.2"]
  }
}

# AFTER:
origin {
  domain_name = aws_s3_bucket.frontend.bucket_regional_domain_name
  origin_id   = "S3-${local.s3_bucket}"

  s3_origin_config {
    origin_access_identity = aws_cloudfront_origin_access_identity.frontend.cloudfront_access_identity_path
  }
}
```

**Why:**
- Use S3 origin instead of website endpoint
- Enable OAI authentication
- CloudFront will sign requests to S3

### 2. S3 Public Access Block (`main.tf` lines 332-339)

```hcl
# BEFORE:
resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# AFTER:
resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
```

**Why:** Block all public access to prevent accidental exposure

### 3. S3 Bucket Policy (`main.tf` lines 341-359)

```hcl
# BEFORE:
resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.frontend.arn}/*"
      }
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.frontend]
}

# AFTER:
resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "CloudFrontReadGetObject"
        Effect    = "Allow"
        Principal = {
          AWS = aws_cloudfront_origin_access_identity.frontend.iam_arn
        }
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.frontend.arn}/*"
      }
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.frontend]
}
```

**Why:**
- Only allow CloudFront OAI to read objects
- Remove wildcard (*) principal

### 4. Remove S3 Website Configuration (`main.tf` lines 361-372)

```hcl
# REMOVE THIS ENTIRELY:
resource "aws_s3_bucket_website_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "index.html"
  }
}
```

**Why:**
- Website configuration requires public access
- Not needed when using CloudFront with OAI
- CloudFront handles index.html and error pages

## Implementation Impact

### What Will Stop Working
- ❌ Direct S3 website URL: `http://virtual-me-chatbot-frontend-prod-298290307734.s3-website.eu-west-3.amazonaws.com`

### What Will Continue Working
- ✅ CloudFront URL: `https://d6hzeab4v9p8a.cloudfront.net`
- ✅ Custom domain: `https://chat.lemaire.tel`

### Deployment Steps

1. Run `terraform plan` to review changes
2. Run `terraform apply` to implement changes
3. CloudFront will update (takes 5-10 minutes)
4. Test https://chat.lemaire.tel still works
5. Verify S3 URL returns 403 Forbidden

## Security Benefits

1. **Access Control:** Only CloudFront can access S3 content
2. **Audit Trail:** All access logged through CloudFront
3. **DDoS Protection:** CloudFront provides AWS Shield Standard
4. **WAF Ready:** Can add AWS WAF rules to CloudFront
5. **Rate Limiting:** Can configure CloudFront rate limits
6. **Cost Optimization:** Reduces S3 data transfer costs

## Rollback Plan

If issues occur, rollback by reverting these changes:
1. Re-enable public access blocks
2. Restore public bucket policy
3. Add back website configuration
4. Change CloudFront to use website endpoint

## Recommendation

✅ **Proceed with implementation** - This is a security best practice and should be done immediately.
