# Sentry

Real-time video stream processing platform with ML-powered detection capabilities.

## 🏗️ Architecture

**Frontend** (S3) → **Backend** (ECS Fargate) → **ML Models** (ONNX Runtime)

- Frontend: Vite + React hosted on S3
- Backend: Python Flask API on ECS with Fargate
- Infrastructure: Terraform managed via GitHub Actions CI/CD

## 🚀 Quick Start

### Prerequisites
- AWS Account
- GitHub repository access
- AWS CLI installed and configured

### Setup (5 minutes)

1. **Create S3 bucket for Terraform state:**
   ```bash
   ./scripts/setup.sh
   ```

2. **Configure GitHub secrets** (Settings → Secrets → Actions):
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`

3. **Create GitHub environments** (Settings → Environments):
   - `staging` (no protection rules)
   - `production` (require approval)

4. **Deploy:**
   - Actions → Deploy to Staging → Run workflow (deploy_infrastructure: true)
   - Wait ~10 minutes
   - Actions → Deploy to Production → Run workflow → Approve

**Done!** 🎉

📋 **Detailed checklist:** [NEXT_STEPS.md](NEXT_STEPS.md)

## 📁 Project Structure

```
sentry/
├── .github/workflows/
│   ├── deploy-staging.yml       # Manual staging deployment
│   └── deploy-production.yml    # Auto production deployment (main branch)
│
├── terraform/
│   ├── modules/vpc/            # VPC module
│   ├── environments/           # Environment configs (staging.tfvars, production.tfvars)
│   ├── backend-*.hcl          # S3 backend configs
│   └── *.tf                   # AWS resources
│
├── services/stream-worker/     # Backend Python API
│   ├── src/                   # Application code
│   └── Dockerfile
│
├── frontend/                   # React frontend
│
├── scripts/
│   └── setup.sh               # Initial S3 bucket setup
│
└── docs/
    ├── SETUP.md               # Complete setup guide
    ├── INFRASTRUCTURE.md      # Technical infrastructure details
    └── REFERENCE.md           # Commands and troubleshooting
```
├── scripts/
│   └── build-push.sh          # Docker build helper
│
├── README.md
└── LICENSE
```

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker
- AWS CLI configured

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/Aero-inc/sentry.git
   cd sentry
   ```

2. **Set up environment variables**
   
   Create a `.env` file in the project root (see [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for all options):
   ```bash
   # .env
   AWS_REGION=us-east-1
   AWS_ACCESS_KEY_ID=your_key_here
   AWS_SECRET_ACCESS_KEY=your_secret_here
   S3_ARTIFACTS_BUCKET=sentry-dev-artifacts
   S3_CLIPS_BUCKET=sentry-dev-clips
   ```

3. **Run the backend**
   ```bash
   cd services/stream-worker
   pip install -r requirements.txt
   python app.py
   ```

4. **Run the frontend**
   ```bash
   cd frontend
   npm install
```

---

## 🛠️ Technology Stack

- **Frontend**: Vite + React → AWS S3
- **Backend**: Python Flask + ONNX Runtime → AWS ECS (Fargate)
- **Infrastructure**: Terraform → AWS (VPC, ECS, ECR, S3, IAM, CloudWatch)
- **CI/CD**: GitHub Actions
- **State**: S3 backend

---

## 🚀 Local Development (Optional)

Only needed for local testing. Production uses GitHub Actions CI/CD.

### Backend
```bash
cd services/stream-worker
pip install -r requirements.txt
python app.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Test Terraform Changes Locally (Optional)
```bash
cd terraform
terraform init -backend-config=backend-staging.hcl
terraform plan -var-file=environments/staging.tfvars
```

---

## 🔄 Development Workflow

1. Create branch: `git checkout -b feature/my-feature`
2. Make changes
3. Push: `git push origin feature/my-feature`
4. Deploy to staging: Actions → Deploy to Staging → Select branch
5. Test
6. Merge to `main`
7. Auto-deploys to production (approve when prompted)

---

## 📚 Documentation

- **[NEXT_STEPS.md](NEXT_STEPS.md)** - Complete deployment checklist
- **[docs/SETUP.md](docs/SETUP.md)** - Detailed setup guide
- **[docs/INFRASTRUCTURE.md](docs/INFRASTRUCTURE.md)** - Infrastructure overview
- **[docs/REFERENCE.md](docs/REFERENCE.md)** - Commands and troubleshooting

---

## 🔐 Security

- S3 backend with encryption and versioning
- GitHub Secrets for credentials
- Isolated VPCs per environment
- Least privilege IAM roles
- ECR vulnerability scanning

---

## 📊 Monitoring

**CloudWatch Logs:**
```bash
aws logs tail /ecs/sentry-staging-backend --follow
aws logs tail /ecs/sentry-production-backend --follow
```

**ECS Status:**
```bash
aws ecs describe-services \
  --cluster sentry-production-cluster \
  --services sentry-production-backend
```

Container Insights enabled on all clusters.

---

## 📄 License

See [LICENSE](LICENSE) file for details.