# Staging Environment Configuration
environment         = "staging"
aws_region         = "us-east-1"
project_name       = "aero-sentry-2026"  # Make this globally unique

# ECS Configuration
ecs_task_cpu       = 256
ecs_task_memory    = 512
ecs_desired_count  = 1

# VPC Configuration
vpc_cidr           = "10.0.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b"]

# Monitoring
cloudwatch_retention_days = 7

# Tags
tags = {
  Environment = "staging"
  Project     = "sentry"
  ManagedBy   = "terraform"
}
