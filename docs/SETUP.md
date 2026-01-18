# Sentry - Setup Guide

## 🚀 Quick Start

### Prerequisites
- AWS Account with appropriate permissions
- GitHub repository access
- AWS CLI installed (`aws --version`)

### Initial Setup (One-Time)

#### 1. Bootstrap AWS Resources
```bash
cd scripts
./setup.sh
```

This creates:
- S3 bucket: `sentry-terraform-state` (for Terraform state)
- Encryption, versioning, and proper access controls

#### 2. Configure GitHub

**Add Secrets** (Settings → Secrets and variables → Actions):
```
AWS_ACCESS_KEY_ID          # Your AWS access key
AWS_SECRET_ACCESS_KEY      # Your AWS secret key
STAGING_API_URL            # Staging API endpoint (can be placeholder)
PRODUCTION_API_URL         # Production API endpoint (can be placeholder)
```

**Create Environments** (Settings → Environments):

**Staging**:
- Name: `staging`
- Required reviewers: None (optional)
- Deployment branches: All branches

**Production**:
- Name: `production`
- Required reviewers: 1-2 team members
- Deployment branches: `main` only

#### 3. Deploy Infrastructure

**For Staging**:
1. Go to Actions → Deploy to Staging
2. Click "Run workflow"
3. Set `deploy_infrastructure` to `true`
4. Click "Run workflow"

**For Production**:
1. Go to Actions → Deploy to Production
2. Click "Run workflow"
3. Set `deploy_infrastructure` to `true`
4. Approve deployment
5. Click "Run workflow"

---

## 📦 Daily Operations

### Deploy to Staging
```
Actions → Deploy to Staging
├─ Select branch (any branch)
├─ deploy_infrastructure: false (unless infra changed)
└─ Run workflow
```

### Deploy to Production
**Automatic** on merge to `main`:
```bash
git checkout main
git pull
git merge feature-branch
git push
# Auto-deploys to production (requires approval)
```

**Manual**:
```
Actions → Deploy to Production
├─ deploy_infrastructure: false (unless infra changed)
└─ Run workflow → Approve
```

---

## 🏗️ Project Structure

```
sentry/
├── .github/workflows/
│   ├── deploy-staging.yml       # Staging deployment (manual)
│   └── deploy-production.yml    # Production deployment (auto)
│
├── terraform/                   # Infrastructure as Code
│   ├── modules/vpc/            # VPC module
│   ├── environments/           # Environment configs
│   │   ├── staging.tfvars
│   │   └── production.tfvars
│   ├── backend-*.hcl          # State backend configs
│   └── *.tf                   # Resource definitions
│
├── services/stream-worker/     # Backend service
├── frontend/                   # Frontend application
└── scripts/setup.sh           # Initial setup script
```

---

## 🔧 Environment Configuration

### Staging
- **Resources**: 1 ECS task, 256 CPU, 512 MB
- **VPC**: 10.0.0.0/16
- **Logs**: 7-day retention
- **Cost**: ~$15-30/month

### Production
- **Resources**: 2 ECS tasks, 512 CPU, 1024 MB
- **VPC**: 10.1.0.0/16
- **Logs**: 30-day retention
- **Cost**: ~$50-100/month

---

## 📊 Monitoring

### View Logs
```bash
# Staging
aws logs tail /ecs/sentry-staging-backend --follow

# Production
aws logs tail /ecs/sentry-production-backend --follow
```

### Check Service Status
```bash
# Staging
aws ecs describe-services \
  --cluster sentry-staging-cluster \
  --services sentry-staging-backend

# Production
aws ecs describe-services \
  --cluster sentry-production-cluster \
  --services sentry-production-backend
```

---

## 🐛 Troubleshooting

### Deployment Fails
1. Check GitHub Actions logs
2. Review CloudWatch logs
3. Verify AWS credentials
4. Check service events in AWS Console

### ECS Service Won't Start
```bash
# Check task failures
aws ecs list-tasks \
  --cluster sentry-staging-cluster \
  --desired-status STOPPED

# View stopped task details
aws ecs describe-tasks \
  --cluster sentry-staging-cluster \
  --tasks <task-id>
```

### State Lock Error
If Terraform state is locked (shouldn't happen with GitHub Actions):
```bash
cd terraform
terraform init -backend-config=backend-staging.hcl
# State locks auto-release, no DynamoDB table needed
```

---

## 🔄 Workflow

### Development Process
```
1. Create feature branch
   git checkout -b feature/my-feature

2. Make changes and test locally

3. Push and deploy to staging
   git push origin feature/my-feature
   → Deploy via GitHub Actions

4. Test in staging

5. Create PR and merge to main
   → Auto-deploys to production (with approval)
```

---

## 🔐 Security

- **State**: Encrypted in S3
- **Secrets**: Managed via GitHub Secrets
- **Network**: Isolated VPCs per environment
- **IAM**: Least privilege roles
- **Images**: ECR vulnerability scanning enabled

---

## 📞 Support

Common resources:
- AWS Console: Check service status
- CloudWatch Logs: View application logs
- GitHub Actions: View deployment history
- [Terraform Docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

---

## ✅ Next Steps

After initial setup:
1. ✅ Run `scripts/setup.sh`
2. ✅ Configure GitHub Secrets
3. ✅ Create GitHub Environments
4. ✅ Deploy staging infrastructure
5. ✅ Deploy staging application
6. ✅ Test in staging
7. ✅ Deploy production infrastructure
8. ✅ Deploy production application
9. ✅ Monitor and iterate

**You're ready to deploy! 🚀**
