output "environment" {
  description = "Environment name"
  value       = var.environment
}

output "ecr_repository_url" {
  description = "ECR repository URL for backend"
  value       = aws_ecr_repository.backend.repository_url
}

output "s3_buckets" {
  description = "S3 bucket names"
  value = {
    for key, bucket in aws_s3_bucket.buckets : key => bucket.id
  }
}

output "s3_frontend_url" {
  description = "S3 frontend website URL"
  value       = "http://${aws_s3_bucket.buckets["frontend"].bucket}.s3-website-${var.aws_region}.amazonaws.com"
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  description = "ECS service name"
  value       = aws_ecs_service.backend.name
}

output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "public_subnets" {
  description = "Public subnet IDs"
  value       = module.vpc.public_subnet_ids
}

output "ecs_security_group_id" {
  description = "ECS security group ID"
  value       = module.vpc.ecs_security_group_id
}

output "backend_api_url" {
  description = "Backend API URL (Load Balancer DNS)"
  value       = "http://${aws_lb.backend.dns_name}"
}

output "backend_alb_dns" {
  description = "Backend ALB DNS name"
  value       = aws_lb.backend.dns_name
}

output "cloudfront_frontend_url" {
  description = "CloudFront distribution URL for frontend (HTTPS)"
  value       = "https://${aws_cloudfront_distribution.frontend.domain_name}"
}

output "cloudfront_backend_url" {
  description = "CloudFront distribution URL for backend API (HTTPS)"
  value       = "https://${aws_cloudfront_distribution.backend.domain_name}"
}

output "cloudfront_frontend_domain" {
  description = "CloudFront distribution domain name for frontend"
  value       = aws_cloudfront_distribution.frontend.domain_name
}

output "cloudfront_backend_domain" {
  description = "CloudFront distribution domain name for backend"
  value       = aws_cloudfront_distribution.backend.domain_name
}

