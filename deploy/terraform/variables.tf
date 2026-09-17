variable "aws_region" {
  type        = string
  description = "AWS region for deployment"
  default     = "us-east-1"
}

variable "environment" {
  type        = string
  description = "Deployment environment (e.g. dev, staging, prod)"
  default     = "dev"
}

variable "project_name" {
  type        = string
  description = "Project identifier for resource naming and tagging"
  default     = "hls-variant-store"
}

variable "table_bucket_name" {
  type        = string
  description = "Name of the S3 Tables table bucket (must be 3-63 chars, lowercase, numbers, hyphens). If null, a deterministic name is derived."
  default     = null
}

variable "namespace_name" {
  type        = string
  description = "Namespace (database equivalent) inside the S3 Tables bucket. Must be lowercase."
  default     = "genomics"
}

variable "table_name" {
  type        = string
  description = "Name of the Apache Iceberg variant table. Must be lowercase."
  default     = "variants"
}

variable "tags" {
  type        = map(string)
  description = "Common tags to apply to all taggable resources"
  default = {
    Project   = "HLS-Variant-Store"
    ManagedBy = "Terraform"
    DataClass = "Genomic-Synthetic"
  }
}
