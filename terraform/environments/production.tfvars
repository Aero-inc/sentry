# Production Environment Configuration
environment  = "production"
aws_region   = "us-east-1"
project_name = "aero-sentry-2026"

# ECS Configuration
ecs_task_cpu      = 512
ecs_task_memory   = 1024
ecs_desired_count = 2
ecs_min_capacity  = 2
ecs_max_capacity  = 3

# VPC Configuration
vpc_cidr           = "10.1.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b"]

# Monitoring
cloudwatch_retention_days = 30

# Redis
redis_node_type = "cache.t3.small"

# Tags
tags = {
  Environment = "production"
  Project     = "aero-sentry-2026"
  ManagedBy   = "terraform"
}
