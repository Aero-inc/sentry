# Deployment Architecture

This document explains the deployment differences between local development and production environments.

## Overview

| Component | Local Development | Staging/Production |
|-----------|------------------|-------------------|
| **Backend** | Docker (via docker-compose.local.yml) | Docker (ECR → ECS) |
| **Frontend** | Docker (via docker-compose.local.yml) | Static files (S3 → CloudFront) |

## Local Development

### Running Locally
```bash
docker-compose -f docker-compose.local.yml up
```

**Backend:**
- Uses: `services/stream-worker/Dockerfile`
- Runs on: `http://localhost:8080`
- Container orchestration: docker-compose.local.yml

**Frontend:**
- Uses: `frontend/Dockerfile`
- Runs on: `http://localhost:5173`
- Container orchestration: docker-compose.local.yml
- Hot reload enabled via Vite dev server

### Why Docker for Frontend Locally?
- Consistent development environment across team
- No need to install Node.js on host machine
- Matches backend containerized approach
- Easy setup with single command

## Staging/Production Deployment

### Backend Deployment (Containerized)
```
Dockerfile → Docker Build → ECR → ECS Fargate
```

**Flow:**
1. GitHub Actions builds Docker image from `services/stream-worker/Dockerfile`
2. Image pushed to AWS ECR (Elastic Container Registry)
3. ECS Fargate pulls and runs the container
4. Exposed via Application Load Balancer + CloudFront

**Files involved:**
- `services/stream-worker/Dockerfile` - Container definition
- `.github/workflows/deploy-staging.yml` - CI/CD pipeline
- `terraform/ecs.tf` - ECS infrastructure

**Why Docker for Backend in Production?**
- ✅ Consistent environment (dev/staging/prod)
- ✅ Easy scaling via ECS
- ✅ Health checks and auto-recovery
- ✅ Isolated dependencies

### Frontend Deployment (Static Files)
```
npm install → npm run build → S3 → CloudFront CDN
```

**Flow:**
1. GitHub Actions runs `npm install` and `npm run build`
2. Static files (HTML, CSS, JS) uploaded to S3 bucket
3. CloudFront CDN serves files globally
4. Cache invalidation on each deployment

**Files involved:**
- `frontend/package.json` - Build configuration
- `.github/workflows/deploy-staging.yml` - CI/CD pipeline
- `terraform/s3.tf` - S3 bucket infrastructure
- `terraform/cloudfront.tf` - CDN configuration

**Why S3 + CloudFront for Frontend in Production?**
- ✅ **Performance**: Global CDN edge locations (faster for users worldwide)
- ✅ **Cost**: $0.023/GB vs ~$50/month for containers
- ✅ **Scalability**: Handles millions of requests automatically
- ✅ **Simplicity**: No servers to manage
- ✅ **Best Practice**: Industry standard for static React/Vite apps

## Deployment Commands

### Local Development
```bash
# Start all services
docker-compose -f docker-compose.local.yml up

# Start in background
docker-compose -f docker-compose.local.yml up -d

# Rebuild containers
docker-compose -f docker-compose.local.yml up --build

# Stop all services
docker-compose -f docker-compose.local.yml down
```

### Production Deployment

**Staging:**
```bash
# Trigger via GitHub Actions UI
# Repository → Actions → "Deploy to Staging" → Run workflow
```

**Production:**
```bash
# Trigger via GitHub Actions UI (manual approval required)
# Repository → Actions → "Deploy to Production" → Run workflow
```

Alternatively, push to respective branches (if auto-deploy is enabled).

## Architecture Diagrams

### Local Development
```
┌─────────────────────────────────────┐
│  docker-compose.local.yml           │
├─────────────────┬───────────────────┤
│   Backend       │    Frontend       │
│   Container     │    Container      │
│   :8080         │    :5173          │
│   (Dockerfile)  │    (Dockerfile)   │
└─────────────────┴───────────────────┘
```

### Production (Staging/Prod)
```
┌──────────────────────────────────────────────┐
│             GitHub Actions                    │
├────────────────────┬─────────────────────────┤
│     Backend        │       Frontend          │
│                    │                         │
│  Dockerfile        │  npm build              │
│      ↓             │      ↓                  │
│    ECR             │     S3                  │
│      ↓             │      ↓                  │
│  ECS Fargate       │  CloudFront CDN         │
│      ↓             │      ↓                  │
│     ALB            │   (Global Edge)         │
│      ↓             │                         │
│  CloudFront        │                         │
└────────────────────┴─────────────────────────┘
```

## Common Questions

### Q: Why not use Docker for frontend in production?
**A:** Static file hosting (S3 + CloudFront) is faster (global CDN), cheaper (~$1/month vs ~$50/month), more scalable (automatic), and simpler (no container management).

### Q: Why use the same Dockerfile for backend in both environments?
**A:** Ensures consistency - if it works locally, it works in production.

### Q: Can I test production frontend build locally?
**A:** Yes:
```bash
cd frontend
npm install
npm run build
npm run preview
```

### Q: How do I add environment variables?

**Local Development:**
- Add to `docker-compose.local.yml` environment section

**Production:**
- **Backend** → `terraform/ecs.tf` (runtime variables)
- **Frontend** → `.github/workflows/deploy-*.yml` (build-time variables)

**Why different locations?**
- Backend reads env vars when running → defined in ECS task
- Frontend compiles env vars during build → defined in GitHub Actions

**For secrets (API keys, passwords):**
- **Backend** → AWS Secrets Manager/Parameter Store + reference in `terraform/ecs.tf`
- **Frontend** → GitHub Secrets + reference in workflows
- ⚠️ Frontend secrets are visible in browser - use backend for truly sensitive operations

**Decision tree:**
```
Backend variable → terraform/ecs.tf (or AWS Secrets Manager if secret)
Frontend variable → .github/workflows/*.yml (or GitHub Secrets if secret)
```

## Related Documentation

- [INFRASTRUCTURE.md](./INFRASTRUCTURE.md) - Full infrastructure overview
- [SETUP.md](./SETUP.md) - Initial setup guide
- [REFERENCE.md](./REFERENCE.md) - API and command reference
