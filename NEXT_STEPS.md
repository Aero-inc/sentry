# Next Steps Checklist

Complete these steps in order to get your infrastructure deployed.

---

## ✅ Phase 1: Initial Setup (One-time)

### 1. Configure AWS Credentials
```bash
# Install AWS CLI if needed
brew install awscli  # macOS

# Configure credentials
aws configure
# AWS Access Key ID: <your-key>
# AWS Secret Access Key: <your-secret>
# Default region: us-east-1
# Default output format: json
```

**Verify:**
```bash
aws sts get-caller-identity
```

---

### 2. Create Terraform State Bucket
```bash
# Run the setup script
./scripts/setup.sh
```

**This creates:**
- S3 bucket: `sentry-terraform-state-us-east-1`
- Versioning enabled
- Encryption enabled
- Public access blocked

**Verify:**
```bash
aws s3 ls | grep sentry-terraform-state-us-east-1
```

---

### 3. Configure GitHub Secrets

Go to: **Settings → Secrets and variables → Actions**

**Add repository secrets:**
- `AWS_ACCESS_KEY_ID` → Your AWS access key
- `AWS_SECRET_ACCESS_KEY` → Your AWS secret key
- `STAGING_API_URL` → http://staging-alb-url.us-east-1.elb.amazonaws.com
- `PRODUCTION_API_URL` → http://production-alb-url.us-east-1.elb.amazonaws.com

*(ALB URLs will be available after first infrastructure deployment)*

---

### 4. Configure GitHub Environments

**Create Staging Environment:**
1. Settings → Environments → New environment
2. Name: `staging`
3. *(No protection rules needed)*

**Create Production Environment:**
1. Settings → Environments → New environment
2. Name: `production`
3. **Enable:** Required reviewers → Add yourself
4. **Enable:** Wait timer → 5 minutes (optional)

---

## ✅ Phase 2: Initial Deployment

### 5. Deploy Staging Infrastructure
```
1. Go to: Actions → Deploy to Staging
2. Click: Run workflow
3. Branch: main
4. deploy_infrastructure: true
5. Click: Run workflow
6. Wait: ~10 minutes
```

**Verify:**
```bash
# Check cluster
aws ecs describe-clusters --clusters sentry-staging-cluster

# Check service
aws ecs describe-services \
  --cluster sentry-staging-cluster \
  --services sentry-staging-backend

# Check frontend
aws s3 ls s3://sentry-staging-frontend/
```

---

### 6. Update GitHub Secrets with ALB URLs

After infrastructure deployment:

```bash
# Get staging ALB URL
terraform output -state=terraform/terraform.tfstate staging_alb_dns

# Get production ALB URL (after production deployment)
terraform output -state=terraform/terraform.tfstate production_alb_dns
```

**Update secrets:**
- `STAGING_API_URL` → http://<staging-alb-dns>
- `PRODUCTION_API_URL` → http://<production-alb-dns>

---

### 7. Deploy Staging Application
```
1. Actions → Deploy to Staging
2. Run workflow
3. Branch: main
4. deploy_infrastructure: false
5. Run workflow
6. Wait: ~5 minutes
```

**Verify:**
```bash
# Check logs
aws logs tail /ecs/sentry-staging-backend --follow

# Test backend
curl http://<staging-alb-dns>/health

# Test frontend
curl http://sentry-staging-frontend.s3-website-us-east-1.amazonaws.com
```

---

### 8. Deploy Production Infrastructure
```
1. Actions → Deploy to Production
2. Run workflow
3. deploy_infrastructure: true
4. Run workflow
5. Approve deployment
6. Wait: ~10 minutes
```

**Verify:**
```bash
aws ecs describe-clusters --clusters sentry-production-cluster
aws ecs describe-services \
  --cluster sentry-production-cluster \
  --services sentry-production-backend
```

---

### 9. Deploy Production Application
```
1. Push to main branch (auto-triggers)
   OR
2. Actions → Deploy to Production → Run manually
3. Approve deployment
4. Wait: ~5 minutes
```

**Verify:**
```bash
# Check production
curl http://<production-alb-dns>/health
curl http://sentry-production-frontend.s3-website-us-east-1.amazonaws.com

# Check logs
aws logs tail /ecs/sentry-production-backend --since 10m
```

---

## ✅ Phase 3: Validation

### 10. Test Complete Flow

**Staging:**
```bash
# 1. Create test branch
git checkout -b test/deployment-validation

# 2. Make a change
echo "// Test change" >> services/stream-worker/app.py

# 3. Commit and push
git add .
git commit -m "Test: deployment validation"
git push origin test/deployment-validation

# 4. Deploy
Actions → Deploy to Staging → Branch: test/deployment-validation

# 5. Verify
curl http://<staging-alb-dns>/health
```

**Production:**
```bash
# 1. Merge to main
git checkout main
git merge test/deployment-validation
git push

# 2. Auto-deploys (approve when prompted)
# 3. Verify
curl http://<production-alb-dns>/health
```

---

### 11. Monitor Deployments

**Check CloudWatch Logs:**
```bash
# Staging
aws logs tail /ecs/sentry-staging-backend --follow

# Production
aws logs tail /ecs/sentry-production-backend --follow
```

**Check ECS Tasks:**
```bash
# Staging
aws ecs list-tasks --cluster sentry-staging-cluster

# Production
aws ecs list-tasks --cluster sentry-production-cluster
```

**Check Container Insights:**
1. AWS Console → CloudWatch
2. Container Insights
3. Select cluster: sentry-staging-cluster / sentry-production-cluster
4. View: CPU, Memory, Network metrics

---

## ✅ Phase 4: Ongoing Operations

### 12. Daily Workflow

**Feature Development:**
```bash
1. Create branch: git checkout -b feature/new-feature
2. Make changes
3. Push: git push origin feature/new-feature
4. Deploy to staging: Actions → Deploy to Staging
5. Test in staging
6. Merge to main: git checkout main && git merge feature/new-feature
7. Push: git push
8. Auto-deploys to production (approve)
```

**Infrastructure Updates:**
```bash
1. Edit: terraform/environments/staging.tfvars
2. Commit: git commit -am "Update staging config"
3. Deploy: Actions → Deploy to Staging (deploy_infrastructure=true)
4. Test
5. Update: terraform/environments/production.tfvars
6. Deploy: Actions → Deploy to Production (deploy_infrastructure=true)
```

---

### 13. Cost Monitoring

**Check AWS costs weekly:**
```bash
# Via AWS Console
AWS Console → Billing → Cost Explorer

# Estimate monthly cost:
- NAT Gateway: ~$35/month per environment
- ECS Fargate: ~$15-30/month per environment
- ALB: ~$20/month per environment
- S3: ~$1-5/month
- CloudWatch: ~$5-10/month
Total: ~$150-200/month for both environments
```

**Optimize:**
- Use single NAT Gateway per environment (already configured)
- Monitor and adjust ECS task counts
- Set up billing alerts in AWS

---

## 📋 Summary

**One-time setup:** Steps 1-4
**Initial deployment:** Steps 5-9
**Validation:** Steps 10-11
**Ongoing:** Steps 12-13

---

## 🆘 Troubleshooting

**Deployment fails:**
1. Check GitHub Actions logs
2. Review CloudWatch logs
3. Verify secrets are set correctly
4. Check AWS service quotas

**ECS tasks won't start:**
1. Check CloudWatch logs for errors
2. Verify ECR image exists
3. Check IAM permissions
4. Review ECS service events

**Infrastructure changes fail:**
1. Verify Terraform state is accessible
2. Check S3 bucket permissions
3. Review error in GitHub Actions
4. Run `terraform plan` locally to debug

---

## 📚 Documentation

- **Setup Guide:** [docs/SETUP.md](docs/SETUP.md)
- **Infrastructure Details:** [docs/INFRASTRUCTURE.md](docs/INFRASTRUCTURE.md)
- **Quick Reference:** [docs/REFERENCE.md](docs/REFERENCE.md)

---

## ✨ You're Ready!

Once all steps are complete:
- ✅ Infrastructure is deployed
- ✅ Applications are running
- ✅ CI/CD is automated
- ✅ Monitoring is active

Start building! 🚀
