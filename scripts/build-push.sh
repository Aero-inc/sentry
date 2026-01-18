#!/bin/bash
# Build and push Docker image locally (for manual testing only)
# Production deployments use GitHub Actions CI/CD

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Configuration
AWS_REGION=${AWS_REGION:-us-east-1}
ENVIRONMENT=${ENVIRONMENT:-dev}
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}
ECR_REPOSITORY="sentry-${ENVIRONMENT}-backend"
ECR_URL="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}"

echo "📦 Building for: ${ENVIRONMENT}"
echo "🔑 AWS Account: ${AWS_ACCOUNT_ID}"
echo "📍 Region: ${AWS_REGION}"
echo ""

# Login to ECR
echo "🔐 Logging in to ECR..."
aws ecr get-login-password --region ${AWS_REGION} | \
  docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# Build image
echo "🏗️  Building stream-worker..."
cd "${PROJECT_ROOT}/services/stream-worker"
docker build -t stream-worker:latest -f Dockerfile .

# Tag and push
echo "📤 Pushing to ECR..."
docker tag stream-worker:latest ${ECR_URL}:latest
docker tag stream-worker:latest ${ECR_URL}:$(git rev-parse --short HEAD 2>/dev/null || echo "manual")
docker push ${ECR_URL}:latest
docker push ${ECR_URL}:$(git rev-parse --short HEAD 2>/dev/null || echo "manual")

echo ""
echo "✅ Image pushed to ${ECR_URL}:latest"
echo ""
echo "💡 For production: Push to 'main' branch to trigger CI/CD deployment"
