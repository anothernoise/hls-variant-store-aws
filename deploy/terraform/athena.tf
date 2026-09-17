# Dedicated encrypted S3 bucket for Athena query outputs
resource "aws_s3_bucket" "athena_results" {
  bucket        = lower("${var.project_name}-athena-results-${var.environment}-${substr(local.account_id, 0, 8)}")
  force_destroy = var.environment == "dev" ? true : false

  tags = {
    Name = "${var.project_name}-athena-results-${var.environment}"
  }
}

resource "aws_s3_bucket_public_access_block" "athena_results" {
  bucket = aws_s3_bucket.athena_results.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "athena_results" {
  bucket = aws_s3_bucket.athena_results.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.genomics.arn
      sse_algorithm     = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "athena_results" {
  bucket = aws_s3_bucket.athena_results.id

  rule {
    id     = "expire-query-results"
    status = "Enabled"

    filter {
      prefix = "results/"
    }

    expiration {
      days = 30
    }
  }
}

# Dedicated Athena WorkGroup for Genomic Analytics
resource "aws_athena_workgroup" "genomics" {
  name        = "${var.project_name}-${var.environment}"
  description = "Athena workgroup for querying S3 Tables genomic variants and OMOP phenotype data"
  state       = "ENABLED"

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true
    bytes_scanned_cutoff_per_query     = 10737418240 # 10 GB limit per query as cost safeguard

    result_configuration {
      output_location = "s3://${aws_s3_bucket.athena_results.bucket}/results/"

      encryption_configuration {
        encryption_option = "SSE_KMS"
        kms_key_arn       = aws_kms_key.genomics.arn
      }
    }
  }
}
