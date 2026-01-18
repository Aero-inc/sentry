# Import existing resources into Terraform state
# These import blocks will be processed once and can be removed after successful apply
# Terraform 1.5+ feature - declarative imports

# ECR Repository
import {
  to = aws_ecr_repository.backend
  id = "${var.project_name}-${var.environment}-backend"
}

# CloudWatch Log Group
import {
  to = aws_cloudwatch_log_group.backend
  id = "/ecs/${var.project_name}-${var.environment}-backend"
}

# IAM Roles
import {
  to = aws_iam_role.ecs_task_execution_role
  id = "${var.project_name}-${var.environment}-ecs-task-execution-role"
}

import {
  to = aws_iam_role.backend_task_role
  id = "${var.project_name}-${var.environment}-backend-task-role"
}

# S3 Buckets
import {
  to = aws_s3_bucket.buckets["artifacts"]
  id = "${var.project_name}-${var.environment}-artifacts"
}

import {
  to = aws_s3_bucket.buckets["clips"]
  id = "${var.project_name}-${var.environment}-clips"
}

import {
  to = aws_s3_bucket.buckets["frontend"]
  id = "${var.project_name}-${var.environment}-frontend"
}

# NOTE: After successful terraform apply, you can safely delete this file.
# Terraform will have imported these resources into state and this file is no longer needed.
