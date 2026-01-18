# Local Development Quick Start

## Prerequisites

- Docker and Docker Compose installed
- AWS CLI configured with credentials (or manual credentials)

## Quick Start with Script

The fastest way to start local development:

```bash
# Make sure you have AWS CLI configured first
aws configure

# Start everything with one command
source scripts/start-local.sh
```

This script will:
- ✅ Automatically load AWS credentials from your AWS CLI config
- ✅ Build and start all services with docker-compose
- ✅ Handle paths correctly even if run from any directory

## Manual Setup (Alternative)

If you prefer to run commands manually:

1. **Export AWS credentials:**
   ```bash
   export AWS_ACCESS_KEY_ID=your-access-key
   export AWS_SECRET_ACCESS_KEY=your-secret-key
   ```

2. **Start services:**
   ```bash
   docker-compose -f docker-compose.local.yml up
   ```

3. **Access:**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8080
   - Health check: http://localhost:8080/health

## What's Running

- **Backend**: Connects to staging AWS (S3, CloudWatch)
- **Frontend**: Hot-reload enabled for development

## Common Commands

```bash
# Start with convenience script (recommended)
source scripts/start-local.sh

# Or use docker-compose directly:

# Start in background
docker-compose -f docker-compose.local.yml up -d

# View logs
docker-compose -f docker-compose.local.yml logs -f

# Rebuild after code changes
docker-compose -f docker-compose.local.yml up --build

# Stop services
docker-compose -f docker-compose.local.yml down

# Stop and remove containers
docker stop sentry-stream-worker sentry-frontend
docker rm sentry-stream-worker sentry-frontend
```

## Troubleshooting

**Port already in use?**
```bash
docker ps -a | grep sentry
docker stop <container-name>
doIf using the start script, make sure AWS CLI is configured
aws configure list

# If setting manually, verify credentials are exported
echo $AWS_ACCESS_KEY_ID
```

**"Failed to download model" errors?**
This is normal for local development - ML models aren't uploaded to S3 yet. The service will start and function without them (useful for testing the API).
**AWS credentials not working?**
```bash
# Verify credentials are exported
echo $AWS_ACCESS_KEY_ID
```

**Need to change environment variables?**
Edit `docker-compose.local.yml` and rebuild:
```bash
docker-compose -f docker-compose.local.yml up --build
```

## Testing the API

```bash
# Health check
curl http://localhost:8080/health

# Create a stream
curl -X POST http://localhost:8080/streams \
  -H "Content-Type: application/json" \
  -d '{
    "stream_id": "test-stream",
    "enable_clip_recording": true
  }'

# Get stats
curl http://localhost:8080/stats
```

## Notes

- Uses staging AWS resources (safe for testing)
- Frontend auto-reloads on code changes
- Backend requires container rebuild for code changes
- All data goes to staging S3 buckets

## More Info

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed architecture and deployment info.
