# Custom S3 + Iceberg Architecture (DIY Strategy)
# Storage bucket for self-managed Apache Iceberg warehouse
resource "aws_s3_bucket" "iceberg_warehouse" {
  bucket        = lower("${var.project_name}-iceberg-warehouse-${var.environment}-${substr(local.account_id, 0, 8)}")
  force_destroy = var.environment == "dev" ? true : false

  tags = {
    Name        = "${var.project_name}-iceberg-warehouse-${var.environment}"
    Description = "Data warehouse bucket for custom S3 + Apache Iceberg variant tables"
  }
}

resource "aws_s3_bucket_public_access_block" "iceberg_warehouse" {
  bucket = aws_s3_bucket.iceberg_warehouse.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "iceberg_warehouse" {
  bucket = aws_s3_bucket.iceberg_warehouse.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.genomics.arn
      sse_algorithm     = "aws:kms"
    }
  }
}

# AWS Glue Catalog Database for Custom Iceberg
resource "aws_glue_catalog_database" "genomics_custom_iceberg" {
  name        = "genomics_custom_iceberg"
  description = "Glue Catalog Database for custom S3 + Iceberg genomic variant store"

  location_uri = "s3://${aws_s3_bucket.iceberg_warehouse.bucket}/warehouse/"
}

# AWS Glue Catalog Table registered as Apache Iceberg
resource "aws_glue_catalog_table" "custom_iceberg_variants" {
  name          = "variants"
  database_name = aws_glue_catalog_database.genomics_custom_iceberg.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    "table_type" = "ICEBERG"
    "format"     = "PARQUET"
    "EXTERNAL"   = "TRUE"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.iceberg_warehouse.bucket}/warehouse/variants/"
    input_format  = "org.apache.iceberg.mr.hive.HiveIcebergInputFormat"
    output_format = "org.apache.iceberg.mr.hive.HiveIcebergOutputFormat"

    ser_de_info {
      name                  = "IcebergSerDe"
      serialization_library = "org.apache.iceberg.mr.hive.HiveIcebergSerDe"
    }

    columns {
      name = "reference_name"
      type = "string"
    }
    columns {
      name = "start"
      type = "bigint"
    }
    columns {
      name = "end"
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
  }

  partition_keys {
    name = "reference_name"
    type = "string"
  }
}
