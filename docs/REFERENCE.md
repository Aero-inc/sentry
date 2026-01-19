# Reference Guide

Quick reference for common operations.

## 🚀 Deployments

### Staging

```
Actions → Deploy to Staging
├─ Branch: <your-branch>
├─ deploy_infrastructure: false (or true if needed)
└─ Run workflow
```

### Production

**Automatic**: Merge to main
**Manual**:

```
Actions → Deploy to Production
├─ deploy_infrastructure: false (or true if needed)
└─ Run workflow → Approve
```

---

## 📊 Monitoring

### Logs

```bash
# Real-time logs
aws logs tail /ecs/sentry-staging-backend --follow
aws logs tail /ecs/sentry-production-backend --follow

# Last hour errors
aws logs filter-log-events \
  --log-group-name /ecs/sentry-production-backend \
  --filter-pattern "ERROR" \
  --start-time $(date -u -d '1 hour ago' +%s)000
```

### Service Status

```bash
# Staging
aws ecs describe-services \
  --cluster sentry-staging-cluster \
  --services sentry-staging-backend

# Production
aws ecs describe-services \
  --cluster sentry-production-cluster \
  --services sentry-production-backend

# List running tasks
aws ecs list-tasks \
  --cluster sentry-production-cluster \
  --service-name sentry-production-backend
```

### ECR Images

```bash
# List images
aws ecr list-images \
  --repository-name sentry-staging-backend

# Latest image
aws ecr describe-images \
  --repository-name sentry-production-backend \
  --image-ids imageTag=latest
```

---

## 🛠️ Terraform Operations

### Local Testing (Optional)

```bash
cd terraform

# Initialize
terraform init -backend-config=backend-staging.hcl

# Plan
terraform plan -var-file=environments/staging.tfvars

# View state
terraform show

# List resources
terraform state list
```

---

## 🔧 Configuration

### Update Environment Settings

```bash
# Edit configuration
vim terraform/environments/staging.tfvars

# Commit
git add terraform/environments/staging.tfvars
git commit -m "Update staging config"
git push

# Deploy
Actions → Deploy to Staging → deploy_infrastructure=true
```

### Scale ECS Tasks

```hcl
# In terraform/environments/production.tfvars
ecs_desired_count = 3  # Change from 2 to 3
```

Then deploy infrastructure.

---

## 🐛 Troubleshooting

### Deployment Failed

1. Check GitHub Actions logs
2. Review CloudWatch logs
3. Check ECS service events:

```bash
aws ecs describe-services \
  --cluster sentry-staging-cluster \
  --services sentry-staging-backend
```

### ECS Task Won't Start

```bash
# Find stopped tasks
aws ecs list-tasks \
  --cluster sentry-staging-cluster \
  --desired-status STOPPED

# Get task details
aws ecs describe-tasks \
  --cluster sentry-staging-cluster \
  --tasks <task-arn>

# Check logs
aws logs tail /ecs/sentry-staging-backend --since 30m
```

### Check S3 Buckets

```bash
# List buckets
aws s3 ls | grep sentry

# Check frontend deployment
aws s3 ls s3://sentry-production-frontend/

# Test website
curl http://sentry-production-frontend.s3-website-us-east-1.amazonaws.com
```

---

## 🔄 Common Workflows

### Deploy Feature to Staging

```bash
git checkout -b feature/my-feature
# Make changes
git push origin feature/my-feature
# Deploy via Actions → Deploy to Staging
```

### Deploy to Production

```bash
git checkout main
git merge feature/my-feature
git push
# Auto-deploys (approve when prompted)
```

### Rollback

```bash
# Redeploy previous commit
git checkout main
git revert HEAD
git push
# Auto-deploys old version
```

### Update Infrastructure

```bash
# Edit terraform files
vim terraform/ecs.tf

# Deploy to staging first
Actions → Deploy to Staging → deploy_infrastructure=true

# Test, then deploy to production
git push (to main)
Actions → Deploy to Production → Approve
```

---

## 🔐 Secrets Management

### GitHub Secrets

```
Settings → Secrets and variables → Actions

Required:
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- STAGING_API_URL
- PRODUCTION_API_URL
```

### Environment Secrets

```
Settings → Environments → <environment> → Add secret
```

---

## 📝 Resource Naming

### Pattern

```
{project}-{environment}-{resource}
```

### Examples

```
sentry-staging-cluster
sentry-production-backend
sentry-staging-frontend (S3 bucket)
/ecs/sentry-production-backend (CloudWatch log group)
```

---

## 🆘 Emergency Commands

### Stop All Tasks

```bash
# Get task ARNs
aws ecs list-tasks \
  --cluster sentry-production-cluster \
  --service-name sentry-production-backend

# Stop tasks
aws ecs stop-task \
  --cluster sentry-production-cluster \
  --task <task-arn>
```

### Scale to Zero

```bash
aws ecs update-service \
  --cluster sentry-production-cluster \
  --service sentry-production-backend \
  --desired-count 0
```

### Force Deployment

```bash
aws ecs update-service \
  --cluster sentry-production-cluster \
  --service sentry-production-backend \
  --force-new-deployment
```

---

## 💡 Tips

1. Always test in staging first
2. Monitor logs during deployment
3. Keep staging and production in sync
4. Use meaningful commit messages
5. Tag production releases
6. Review costs weekly

---

## Datasets Used

- **USRT (US Real-time gun detection in CCTV)**
  - [Project Page](https://deepknowledge-us.github.io/US-Real-time-gun-detection-in-CCTV-An-open-problem-dataset/)
  - [Reference Paper](https://doi.org/10.1016/j.neunet.2020.09.013)
  - [Download Instructions](https://github.com/srikarym/CCTV-Gun/blob/master/dataset_instructions.md#usrt)
- **UCF-Crime**
  - [Dataset Link](https://www.dropbox.com/scl/fo/2aczdnx37hxvcfdo4rq4q/AOjRokSTaiKxXmgUyqdcI6k?dl=0&e=1&rlkey=5bg7mxxbq46t7aujfch46dlvz) (Use `Anomaly-Videos-Part-3.zip` only)
  - [Reference Paper](https://doi.org/10.1109/CVPR.2018.00678)
  - [Download Instructions](https://github.com/srikarym/CCTV-Gun/blob/master/dataset_instructions.md#ucf)
- **Kaggle's CCTV weapons dataset**
  - [Dataset Link](https://www.kaggle.com/datasets/simuletic/cctv-weapon-dataset)

---

## 📞 Quick Links

- **AWS Console**: https://console.aws.amazon.com
- **GitHub Actions**: Repository → Actions tab
- **CloudWatch Logs**: AWS Console → CloudWatch → Logs
- **ECS**: AWS Console → ECS → Clusters
