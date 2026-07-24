output "alb_dns_name" {
  value       = aws_lb.app.dns_name
  description = "Public DNS name for the application load balancer."
}

output "ecs_cluster_name" {
  value       = aws_ecs_cluster.main.name
  description = "ECS cluster name."
}
