# Synthetic OMOP CDM Clinical Phenotype Architecture
# Dedicated encrypted S3 bucket for OMOP CDM clinical data
resource "aws_s3_bucket" "clinical_data" {
  bucket        = lower("${var.project_name}-clinical-data-${var.environment}-${substr(local.account_id, 0, 8)}")
  force_destroy = var.environment == "dev" ? true : false

  tags = {
    Name        = "${var.project_name}-clinical-data-${var.environment}"
    Description = "Storage for synthetic OMOP CDM person and condition_occurrence tables"
  }
}

resource "aws_s3_bucket_public_access_block" "clinical_data" {
  bucket = aws_s3_bucket.clinical_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "clinical_data" {
  bucket = aws_s3_bucket.clinical_data.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.genomics.arn
      sse_algorithm     = "aws:kms"
    }
  }
}

# AWS Glue Catalog Database for Clinical Data
resource "aws_glue_catalog_database" "clinical_omop" {
  name        = "clinical_omop"
  description = "Glue Catalog Database for synthetic OMOP CDM clinical phenotype tables"

  location_uri = "s3://${aws_s3_bucket.clinical_data.bucket}/omop/"
}

# OMOP person table
resource "aws_glue_catalog_table" "omop_person" {
  name          = "person"
  database_name = aws_glue_catalog_database.clinical_omop.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    "classification"         = "csv"
    "skip.header.line.count" = "1"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.clinical_data.bucket}/omop/person/"
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"

    ser_de_info {
      name                  = "CsvSerDe"
      serialization_library = "org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe"
      parameters = {
        "field.delim"            = ","
        "serialization.format"   = ","
        "skip.header.line.count" = "1"
      }
    }

    columns {
      name = "person_id"
      type = "bigint"
    }
    columns {
      name = "gender_concept_id"
      type = "int"
    }
    columns {
      name = "year_of_birth"
      type = "int"
    }
    columns {
      name = "month_of_birth"
      type = "int"
    }
    columns {
      name = "day_of_birth"
      type = "int"
    }
    columns {
      name = "race_concept_id"
      type = "int"
    }
    columns {
      name = "ethnicity_concept_id"
      type = "int"
    }
    columns {
      name = "sample_id"
      type = "string"
    }
  }
}

# OMOP condition_occurrence table
resource "aws_glue_catalog_table" "omop_condition_occurrence" {
  name          = "condition_occurrence"
  database_name = aws_glue_catalog_database.clinical_omop.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    "classification"         = "csv"
    "skip.header.line.count" = "1"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.clinical_data.bucket}/omop/condition_occurrence/"
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"

    ser_de_info {
      name                  = "CsvSerDe"
      serialization_library = "org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe"
      parameters = {
        "field.delim"            = ","
        "serialization.format"   = ","
        "skip.header.line.count" = "1"
      }
    }

    columns {
      name = "condition_occurrence_id"
      type = "bigint"
    }
    columns {
      name = "person_id"
      type = "bigint"
    }
    columns {
      name = "condition_concept_id"
      type = "int"
    }
    columns {
      name = "condition_start_date"
      type = "string"
    }
    columns {
      name = "condition_type_concept_id"
      type = "int"
    }
  }
}
