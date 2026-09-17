# Hail VDS (Variant Dataset) on S3 Strategy
# Stores split sparse matrix tables (reference data chunks + variant sparse matrix)
# Optimized for large-scale population genetics, GWAS, and LD pruning via Apache Spark / Hail

resource "aws_s3_bucket" "hail_vds" {
  count         = var.enable_hail_vds ? 1 : 0
  bucket        = "${local.bucket_name}-hail-vds"
  force_destroy = true

  tags = merge(local.common_tags, {
    Tier = "Hail-VDS-Warehouse"
  })
}

resource "aws_s3_bucket_server_side_encryption_configuration" "hail_vds" {
  count  = var.enable_hail_vds ? 1 : 0
  bucket = aws_s3_bucket.hail_vds[0].id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.genomics.arn
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "hail_vds" {
  count                   = var.enable_hail_vds ? 1 : 0
  bucket                  = aws_s3_bucket.hail_vds[0].id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# AWS Glue Catalog Database for Hail VDS metadata
resource "aws_glue_catalog_database" "genomics_hail" {
  count       = var.enable_hail_vds ? 1 : 0
  name        = "genomics_hail_vds"
  description = "Glue Catalog database cataloging Hail Variant Dataset (VDS) sparse matrices"
}

# Glue Table for the Variant Matrix component of Hail VDS
resource "aws_glue_catalog_table" "hail_variant_data" {
  count         = var.enable_hail_vds ? 1 : 0
  name          = "variant_data"
  database_name = aws_glue_catalog_database.genomics_hail[0].name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    "classification" = "parquet"
    "typeOfData"     = "file"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.hail_vds[0].bucket}/vds/variant_data/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      name                  = "ParquetHiveSerDe"
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }

    columns {
      name = "locus_contig"
      type = "string"
    }
    columns {
      name = "locus_position"
      type = "int"
    }
    columns {
      name = "alleles"
      type = "array<string>"
    }
    columns {
      name = "sample_id"
      type = "string"
    }
    columns {
      name = "call"
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
      name = "ad"
      type = "array<int>"
    }
    columns {
      name = "info"
      type = "string"
    }
  }
}
