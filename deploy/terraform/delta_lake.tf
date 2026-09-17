# Delta Lake on S3 Strategy
# Leverages Parquet data files + ACID transaction log (_delta_log)
# Natively integrated with AWS Glue Data Catalog and queryable via Amazon Athena / EMR / Databricks

resource "aws_s3_bucket" "delta_warehouse" {
  count         = var.enable_delta_lake ? 1 : 0
  bucket        = "${local.bucket_name}-delta-warehouse"
  force_destroy = true

  tags = merge(local.common_tags, {
    Tier = "Delta-Lake-Warehouse"
  })
}

resource "aws_s3_bucket_server_side_encryption_configuration" "delta_warehouse" {
  count  = var.enable_delta_lake ? 1 : 0
  bucket = aws_s3_bucket.delta_warehouse[0].id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.genomics.arn
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "delta_warehouse" {
  count                   = var.enable_delta_lake ? 1 : 0
  bucket                  = aws_s3_bucket.delta_warehouse[0].id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# AWS Glue Catalog Database for Delta Lake
resource "aws_glue_catalog_database" "genomics_delta" {
  count       = var.enable_delta_lake ? 1 : 0
  name        = "genomics_delta"
  description = "Glue Catalog database for genomic variants stored in Delta Lake format"
}

# AWS Glue Catalog Table for Delta Lake
# Using Delta Lake storage handler for Amazon Athena Presto/Trino engine
resource "aws_glue_catalog_table" "delta_variants" {
  count         = var.enable_delta_lake ? 1 : 0
  name          = "variants"
  database_name = aws_glue_catalog_database.genomics_delta[0].name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    "classification" = "delta"
    "table_type"     = "DELTA"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.delta_warehouse[0].bucket}/warehouse/variants/"
    input_format  = "org.apache.hadoop.mapred.SequenceFileInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveSequenceFileOutputFormat"

    ser_de_info {
      name                  = "DeltaSerDe"
      serialization_library = "org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe"
    }

    columns {
      name = "start"
      type = "bigint"
    }
    columns {
      name = "end_pos"
      type = "bigint"
    }
    columns {
      name = "reference_bases"
      type = "string"
    }
    columns {
      name = "alternate_bases"
      type = "string"
    }
    columns {
      name = "sample_id"
      type = "string"
    }
    columns {
      name = "genotype"
      type = "string"
    }
    columns {
      name = "qual"
      type = "double"
    }
    columns {
      name = "filter"
      type = "string"
    }
    columns {
      name = "dp"
      type = "int"
    }
    columns {
      name = "gq"
      type = "int"
    }
    columns {
      name = "allele_depth"
      type = "string"
    }
    columns {
      name = "attributes"
      type = "string"
    }
    columns {
      name = "cohort_id"
      type = "string"
    }
    columns {
      name = "reference_name"
      type = "string"
    }
  }
}
