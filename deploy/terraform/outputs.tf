output "kms_key_arn" {
  description = "ARN of the Customer Managed KMS Key for genomic data encryption"
  value       = aws_kms_key.genomics.arn
}

output "kms_key_alias" {
  description = "Alias of the genomic KMS Key"
  value       = aws_kms_alias.genomics.name
}

# S3 Tables Strategy Outputs
output "s3tables_table_bucket_arn" {
  description = "ARN of the Amazon S3 Tables table bucket"
  value       = aws_s3tables_table_bucket.variants.arn
}

output "s3tables_table_bucket_name" {
  description = "Name of the Amazon S3 Tables table bucket"
  value       = aws_s3tables_table_bucket.variants.name
}

output "s3tables_namespace_name" {
  description = "Namespace created inside the S3 Tables bucket"
  value       = aws_s3tables_namespace.genomics.namespace
}

output "s3tables_table_arn" {
  description = "ARN of the Apache Iceberg variant table in S3 Tables"
  value       = aws_s3tables_table.variants.arn
}

output "s3tables_table_name" {
  description = "Name of the Apache Iceberg variant table in S3 Tables"
  value       = aws_s3tables_table.variants.name
}

# Custom S3 + Iceberg Strategy Outputs
output "custom_iceberg_warehouse_bucket" {
  description = "S3 bucket for custom S3 + Iceberg warehouse"
  value       = aws_s3_bucket.iceberg_warehouse.bucket
}

output "custom_iceberg_glue_database" {
  description = "Glue Catalog Database for custom S3 + Iceberg"
  value       = aws_glue_catalog_database.genomics_custom_iceberg.name
}

output "custom_iceberg_glue_table" {
  description = "Glue Catalog Table for custom S3 + Iceberg"
  value       = aws_glue_catalog_table.custom_iceberg_variants.name
}

# Clinical OMOP Outputs
output "clinical_omop_data_bucket" {
  description = "S3 bucket for synthetic OMOP CDM clinical data"
  value       = aws_s3_bucket.clinical_data.bucket
}

output "clinical_omop_glue_database" {
  description = "Glue Catalog Database for synthetic OMOP data"
  value       = aws_glue_catalog_database.clinical_omop.name
}

# Analytics & IAM Outputs
output "athena_workgroup_name" {
  description = "Name of the Athena WorkGroup"
  value       = aws_athena_workgroup.genomics.name
}

output "athena_results_bucket" {
  description = "S3 bucket for Athena query outputs"
  value       = aws_s3_bucket.athena_results.bucket
}

output "ingestion_role_arn" {
  description = "IAM Role ARN for ingestion workloads"
  value       = aws_iam_role.ingestion.arn
}

output "analyst_role_arn" {
  description = "IAM Role ARN for genomic researcher queries (Lake Formation column filtered)"
  value       = aws_iam_role.analyst.arn
}

output "clinical_steward_role_arn" {
  description = "IAM Role ARN for clinical geneticist / steward queries (unrestricted PHI access)"
  value       = aws_iam_role.clinical_steward.arn
}

# Delta Lake Outputs
output "delta_lake_warehouse_bucket" {
  description = "S3 bucket for Delta Lake warehouse"
  value       = var.enable_delta_lake ? aws_s3_bucket.delta_warehouse[0].bucket : null
}

output "delta_lake_glue_database" {
  description = "Glue Catalog Database for Delta Lake"
  value       = var.enable_delta_lake ? aws_glue_catalog_database.genomics_delta[0].name : null
}

# Hail VDS Outputs
output "hail_vds_bucket" {
  description = "S3 bucket for Hail VDS sparse matrix store"
  value       = var.enable_hail_vds ? aws_s3_bucket.hail_vds[0].bucket : null
}

output "hail_vds_glue_database" {
  description = "Glue Catalog Database for Hail VDS"
  value       = var.enable_hail_vds ? aws_glue_catalog_database.genomics_hail[0].name : null
}

# PostgreSQL / Aurora Outputs
output "postgres_endpoint" {
  description = "Connection endpoint for PostgreSQL / Amazon Aurora"
  value = var.enable_postgres ? (
    var.postgres_deployment_mode == "aurora_serverless" ? aws_rds_cluster.aurora[0].endpoint : aws_db_instance.rds[0].endpoint
  ) : null
}

output "postgres_mode" {
  description = "Configured PostgreSQL deployment mode (aurora_serverless vs rds)"
  value       = var.enable_postgres ? var.postgres_deployment_mode : "disabled"
}

# AWS HealthOmics Outputs
output "healthomics_import_role_arn" {
  description = "IAM Role ARN for AWS HealthOmics import jobs"
  value       = var.enable_healthomics ? aws_iam_role.omics_import[0].arn : null
}

output "healthomics_helper_command" {
  description = "CLI command to manage HealthOmics Variant Store lifecycle"
  value       = "python3 ingest/healthomics/manage_omics_store.py --action status"
}



