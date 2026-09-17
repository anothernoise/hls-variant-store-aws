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

variable "enable_s3_tables" {
  type        = bool
  description = "Enable Amazon S3 Tables table bucket and Apache Iceberg table resources"
  default     = true
}

variable "enable_custom_iceberg" {
  type        = bool
  description = "Enable Custom S3 + Iceberg warehouse and Glue Catalog resources"
  default     = true
}

variable "enable_clinical_omop" {
  type        = bool
  description = "Enable OMOP CDM clinical data warehouse bucket and Glue Catalog resources"
  default     = true
}

variable "enable_delta_lake" {
  type        = bool
  description = "Enable Delta Lake on S3 warehouse and Glue Catalog resources"
  default     = true
}

variable "enable_hail_vds" {
  type        = bool
  description = "Enable Hail VDS on S3 bucket and Glue Catalog resources"
  default     = true
}

variable "enable_postgres" {
  type        = bool
  description = "Enable PostgreSQL relational variant store (RDS instance or Aurora Serverless v2)"
  default     = false
}

variable "postgres_deployment_mode" {
  type        = string
  description = "Deployment topology for PostgreSQL: 'aurora_serverless' (Aurora Serverless v2) or 'rds' (RDS Single/Multi-AZ instance)"
  default     = "aurora_serverless"

  validation {
    condition     = contains(["aurora_serverless", "rds"], var.postgres_deployment_mode)
    error_message = "postgres_deployment_mode must be either 'aurora_serverless' or 'rds'."
  }
}

variable "postgres_db_name" {
  type        = string
  description = "Database name for PostgreSQL"
  default     = "genomics_relational"
}

variable "postgres_admin_username" {
  type        = string
  description = "Master administrator username for PostgreSQL / Aurora"
  default     = "genomics_admin"
}

variable "enable_healthomics" {
  type        = bool
  description = "Enable AWS HealthOmics reference store and variant store resources"
  default     = false
}

variable "healthomics_reference_arn" {
  type        = string
  description = "Optional ARN of an existing AWS HealthOmics Reference (e.g. GRCh38/hg38). If null, reference store is created."
  default     = null
}


