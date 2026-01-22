# Staging Environment Configuration
environment  = "staging"
aws_region   = "us-east-1"
project_name = "aero-sentry-2026" # Make this globally unique

# ECS Configuration
ecs_task_cpu      = 1024 # 1 vCPU
ecs_task_memory   = 4096 # 4GB for ML models (now using 1 worker to avoid OOM)
ecs_desired_count = 2
ecs_min_capacity  = 1
ecs_max_capacity  = 4

# VPC Configuration
vpc_cidr           = "10.0.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b"]

# Monitoring
cloudwatch_retention_days = 7

# Redis
redis_node_type = "cache.t3.micro"

# Tags
tags = {
  Environment = "staging"
  Project     = "aero-sentry-2026"
  ManagedBy   = "terraform"
}
