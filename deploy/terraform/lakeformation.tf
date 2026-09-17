# AWS Lake Formation Governance & Column-Level Access Controls
# Separates non-identifying genomic locus data from re-identifying PHI (genotypes & sample IDs)

variable "enable_lakeformation" {
  type        = bool
  description = "Set to true to provision Lake Formation permissions (requires Lake Formation Admin privileges in target account)"
  default     = false
}

# Register the Iceberg Warehouse S3 Location in Lake Formation
resource "aws_lakeformation_resource" "iceberg_warehouse" {
  count = var.enable_lakeformation ? 1 : 0
  arn   = aws_s3_bucket.iceberg_warehouse.arn
}

# 1. Genomic Researcher Role Permissions:
# Graded Column-Level Security (Excludes re-identifying columns: sample_id, genotype, allele_depth)
resource "aws_lakeformation_permissions" "researcher_column_filter" {
  count       = var.enable_lakeformation ? 1 : 0
  principal   = aws_iam_role.analyst.arn
  permissions = ["SELECT"]

  table_with_columns {
    database_name = aws_glue_catalog_database.genomics_custom_iceberg.name
    name          = aws_glue_catalog_table.custom_iceberg_variants.name
    column_names = [
      "reference_name",
      "start",
      "end",
      "reference_bases",
      "alternate_bases",
      "qual",
      "filter",
      "dp",
      "gq",
      "attributes",
      "cohort_id"
    ]
  }
}

# 2. Clinical Geneticist / Data Steward Permissions:
# Full access to all columns including sensitive PHI (individual genotype calls and sample linkage)
resource "aws_lakeformation_permissions" "clinical_steward_full_access" {
  count       = var.enable_lakeformation ? 1 : 0
  principal   = aws_iam_role.clinical_steward.arn
  permissions = ["SELECT", "DESCRIBE"]

  table_with_columns {
    database_name = aws_glue_catalog_database.genomics_custom_iceberg.name
    name          = aws_glue_catalog_table.custom_iceberg_variants.name
    wildcard      = true
  }
}
