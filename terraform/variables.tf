variable "project_name" {
  type        = string
  default     = "clinical-insights-ai"
  description = "Name prefix for AWS resources."
}

variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "AWS region for the demo stack."
}

variable "container_image" {
  type        = string
  description = "Container image URI for the FastAPI application."
}

variable "container_port" {
  type        = number
  default     = 8000
  description = "FastAPI container port."
}
