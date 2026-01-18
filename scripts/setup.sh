#!/bin/bash

# Sentry Initial Setup Script
# This script sets up the required AWS infrastructure for Sentry

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🚀 Sentry Initial Setup${NC}"
echo "=========================="
echo ""

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
BUCKET_NAME="sentry-terraform-state-us-east-1"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found. Please install it first.${NC}"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS credentials not configured. Run 'aws configure' first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} AWS CLI configured"
echo ""

# Create S3 bucket for Terraform state
echo "📦 Creating S3 bucket for Terraform state..."
if aws s3 ls "s3://${BUCKET_NAME}" 2>&1 | grep -q 'NoSuchBucket'; then
    aws s3api create-bucket \
        --bucket "${BUCKET_NAME}" \
        --region "${AWS_REGION}" \
        2>/dev/null || true
    
    # Enable versioning
    aws s3api put-bucket-versioning \
        --bucket "${BUCKET_NAME}" \
        --versioning-configuration Status=Enabled
    
    # Enable encryption
    aws s3api put-bucket-encryption \
        --bucket "${BUCKET_NAME}" \
        --server-side-encryption-configuration '{
            "Rules": [{
                "ApplyServerSideEncryptionByDefault": {
                    "SSEAlgorithm": "AES256"
                }
            }]
        }'
    
    # Block public access
    aws s3api put-public-access-block \
        --bucket "${BUCKET_NAME}" \
        --public-access-block-configuration \
            "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
    
    echo -e "${GREEN}✓${NC} S3 bucket created: ${BUCKET_NAME}"
else
    echo -e "${YELLOW}⚠${NC}  S3 bucket already exists: ${BUCKET_NAME}"
fi

echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Configure GitHub Secrets:"
echo "   - AWS_ACCESS_KEY_ID"
echo "   - AWS_SECRET_ACCESS_KEY"
echo "   - STAGING_API_URL"
echo "   - PRODUCTION_API_URL"
echo ""
echo "2. Create GitHub Environments:"
echo "   - staging (optional approval)"
echo "   - production (required approval)"
echo ""
echo "3. Deploy infrastructure:"
echo "   Actions → Deploy to Staging → Set deploy_infrastructure=true"
echo ""
echo "4. Deploy application:"
echo "   Actions → Deploy to Staging → Select your branch"
echo ""
echo "📚 See README.md for detailed instructions"
