# Infrastructure Documentation

## 🏗️ Architecture Overview

```
GitHub Actions (CI/CD)
         │
         ▼
┌─────────────────────┐     ┌─────────────────────┐
│  Staging (10.0/16)  │     │ Production (10.1/16)│
├─────────────────────┤     ├─────────────────────┤
│ • VPC + Subnets     │     │ • VPC + Subnets     │
│ • ECS (1 task)      │     │ • ECS (2 tasks)     │
│ • ECR Repository    │     │ • ECR Repository    │
│ • S3 Buckets (3)    │     │ • S3 Buckets (3)    │
│ • CloudWatch Logs   │     │ • CloudWatch Logs   │
└─────────────────────┘     └─────────────────────┘
```

## 📦 AWS Resources

### Per Environment

**Networking**:
- VPC with public subnets across 2 AZs
- Internet Gateway
- Security Groups

**Compute**:
- ECS Fargate Cluster
- ECS Service with configurable task count
- ECR Repository for Docker images

**Storage**:
- S3 Frontend bucket (public website hosting)
- S3 Artifacts bucket (private)
- S3 Clips bucket (private)

**Monitoring**:
- CloudWatch Log Groups
- Container Insights (ECS metrics)

**State Management**:
- S3 bucket: `sentry-terraform-state`
- Separate state files per environment

---

## 🔧 Terraform Structure

### Modules

**VPC Module** (`terraform/modules/vpc/`):
- Creates isolated VPC per environment
- Configurable CIDR blocks
- Public subnets across multiple AZs
- Security groups for ECS tasks

### Resources

**Main Resources** (`terraform/*.tf`):
- `main.tf` - Provider and backend configuration
- `variables.tf` - Input variables
- `outputs.tf` - Output values
- `vpc.tf` - VPC module usage
- `ecr.tf` - Container registry
- `ecs.tf` - ECS cluster and services
- `iam.tf` - IAM roles and policies
- `s3.tf` - S3 buckets

### Environment Configurations

**Staging** (`terraform/environments/staging.tfvars`):
```hcl
environment         = "staging"
ecs_task_cpu       = 256
ecs_task_memory    = 512
ecs_desired_count  = 1
cloudwatch_retention_days = 7
```

**Production** (`terraform/environments/production.tfvars`):
```hcl
environment         = "production"
ecs_task_cpu       = 512
ecs_task_memory    = 1024
ecs_desired_count  = 2
cloudwatch_retention_days = 30
```

---

## 🚀 CI/CD Workflows

### Staging Deployment (`deploy-staging.yml`)

**Trigger**: Manual workflow dispatch

**Features**:
- Deploy any branch
- Optional infrastructure deployment
- Always deploys application (backend + frontend)

**Jobs**:
1. `deploy-infrastructure` - Terraform apply (if enabled)
2. `deploy-backend` - Build Docker, push to ECR, update ECS
3. `deploy-frontend` - Build React app, deploy to S3
4. `summary` - Generate deployment report

### Production Deployment (`deploy-production.yml`)

**Trigger**: 
- Automatic on push to `main`
- Manual workflow dispatch

**Features**:
- Auto-detects infrastructure changes
- Requires approval for production environment
- Deploys backend + frontend

**Jobs**:
1. `deploy-infrastructure` - Terraform apply (if triggered)
2. `deploy-backend` - Build Docker, push to ECR, update ECS
3. `deploy-frontend` - Build React app, deploy to S3
4. `summary` - Generate deployment report

---

## 🔐 Security

### IAM Roles

**ECS Task Execution Role**:
- Pull images from ECR
- Push logs to CloudWatch
- Read secrets (if configured)

**ECS Task Role**:
- Read/Write to S3 buckets (artifacts, clips)
- Put metrics to CloudWatch

### Network Security

**Security Groups**:
- ECS tasks: Allow port 8080, all outbound
- Isolated per environment

**S3 Buckets**:
- Frontend: Public read access
- Artifacts/Clips: Private, ECS task role only

### State Management

**S3 Backend**:
- Server-side encryption (AES256)
- Versioning enabled
- Block public access
- Separate state files per environment

---

## 📊 Scaling & Costs

### Current Setup

| Environment | Tasks | CPU | Memory | Cost/Month |
|-------------|-------|-----|--------|------------|
| Staging | 1 | 256 | 512 MB | ~$15-30 |
| Production | 2 | 512 | 1024 MB | ~$50-100 |

### Scaling Options

**Vertical Scaling**:
```hcl
# terraform/environments/production.tfvars
ecs_task_cpu    = 1024
ecs_task_memory = 2048
```

**Horizontal Scaling**:
```hcl
ecs_desired_count = 5
```

---

## 📈 Monitoring

### CloudWatch Logs

```bash
# Staging logs
aws logs tail /ecs/sentry-staging-backend --follow

# Production logs
aws logs tail /ecs/sentry-production-backend --follow
```

### Service Status

```bash
# Check ECS service
aws ecs describe-services \
  --cluster sentry-production-cluster \
  --services sentry-production-backend

# List tasks
aws ecs list-tasks \
  --cluster sentry-production-cluster \
  --service-name sentry-production-backend
```

---

## 🛠️ Making Changes

### Update Infrastructure

1. Edit Terraform files
2. Deploy to staging with `deploy_infrastructure=true`
3. Test
4. Deploy to production

### Add New Resources

Create new `.tf` file in `terraform/`:
```hcl
# terraform/alb.tf
resource "aws_lb" "main" {
  name               = "${var.project_name}-${var.environment}-alb"
  load_balancer_type = "application"
  # ...
}
```

Deploy via GitHub Actions.

---

## 📝 State Management

**No DynamoDB Locking**:
- GitHub Actions ensures serial execution
- Simpler setup, no extra costs
- State auto-locked during operations

**State Files**:
```
s3://sentry-terraform-state/
├── staging/terraform.tfstate
└── production/terraform.tfstate
```

---

## 🔗 Resources

- [AWS ECS Docs](https://docs.aws.amazon.com/ecs/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [GitHub Actions](https://docs.github.com/en/actions)
