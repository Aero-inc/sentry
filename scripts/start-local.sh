#!/bin/bash
# Start local development environment with AWS credentials
# Usage: source scripts/start-local.sh

# Get absolute path to project root (works when sourced from anywhere)
if [ -n "${BASH_SOURCE[0]}" ]; then
    SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}" 2>/dev/null || greadlink -f "${BASH_SOURCE[0]}" 2>/dev/null || python3 -c "import os,sys; print(os.path.realpath(sys.argv[1]))" "${BASH_SOURCE[0]}")"
    SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"
    PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
else
    # Fallback if BASH_SOURCE is not available
    PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
fi

cd "$PROJECT_ROOT" || (echo "Failed to cd to project root: $PROJECT_ROOT" && return 1 2>/dev/null || exit 1)

# Check if credentials are already in environment
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "📝 AWS credentials not in environment, fetching from AWS CLI config..."
    
    # Get credentials from AWS CLI configuration
    export AWS_ACCESS_KEY_ID=$(aws configure get aws_access_key_id)
    export AWS_SECRET_ACCESS_KEY=$(aws configure get aws_secret_access_key)
    
    # Check if credentials were found
    if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
        echo "❌ Failed to get AWS credentials!"
        echo ""
        echo "Please configure AWS CLI first:"
        echo "  aws configure"
        return 1 2>/dev/null || exit 1
    fi
    
    echo "✅ AWS credentials loaded from AWS CLI config"
else
    echo "✅ AWS credentials already set in environment"
fi

echo ""
echo "Starting services with docker-compose..."
echo ""

docker-compose -f docker-compose.local.yml up --build
echo ""