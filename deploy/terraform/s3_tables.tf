# Amazon S3 Tables: Dedicated Table Bucket for Apache Iceberg tabular storage
resource "aws_s3tables_table_bucket" "variants" {
  name = local.bucket_name

  maintenance_configuration = {
    iceberg_unreferenced_file_removal = {
      status = "enabled"
      settings = {
        unreferenced_days = 3
        non_current_days  = 7
      }
    }
  }

  lifecycle {
    ignore_changes = [encryption_configuration]
  }
}

# Namespace within the S3 Tables Bucket (equivalent to database in Glue/Athena)
resource "aws_s3tables_namespace" "genomics" {
  namespace        = var.namespace_name
  table_bucket_arn = aws_s3tables_table_bucket.variants.arn
}

# Variant Table in Apache Iceberg format
resource "aws_s3tables_table" "variants" {
  name             = var.table_name
  namespace        = aws_s3tables_namespace.genomics.namespace
  table_bucket_arn = aws_s3tables_table_bucket.variants.arn
  format           = "ICEBERG"
}
