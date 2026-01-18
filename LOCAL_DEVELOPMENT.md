# Local Development Quick Start

## Prerequisites

- Docker and Docker Compose installed
- AWS credentials with access to staging environment

## Setup

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
docker rm <container-name>
```

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
