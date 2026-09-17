# Ingestion Role for VCF ETL pipelines and batch loaders
resource "aws_iam_role" "ingestion" {
  name = "${var.project_name}-ingestion-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = [
            "lambda.amazonaws.com",
            "ecs-tasks.amazonaws.com",
            "glue.amazonaws.com"
          ]
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_policy" "ingestion_s3tables" {
  name        = "${var.project_name}-ingestion-policy-${var.environment}"
  description = "Scoped permissions for loading genomic variants into S3 Tables and Custom Iceberg"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3TablesDataIngest"
        Effect = "Allow"
        Action = [
          "s3tables:GetTableBucket",
          "s3tables:GetNamespace",
          "s3tables:GetTable",
          "s3tables:GetTableMetadataLocation",
          "s3tables:GetTableData",
          "s3tables:PutTableData",
          "s3tables:UpdateTableMetadataLocation"
        ]
        Resource = [
          aws_s3tables_table_bucket.variants.arn,
          "${aws_s3tables_table_bucket.variants.arn}/*"
        ]
      },
      {
        Sid    = "CustomIcebergAndClinicalS3Write"
        Effect = "Allow"
        Action = [
          "s3:GetBucketLocation",
          "s3:GetObject",
          "s3:ListBucket",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = [
          aws_s3_bucket.iceberg_warehouse.arn,
          "${aws_s3_bucket.iceberg_warehouse.arn}/*",
          aws_s3_bucket.clinical_data.arn,
          "${aws_s3_bucket.clinical_data.arn}/*"
        ]
      },
      {
        Sid    = "GlueCatalogMutate"
        Effect = "Allow"
        Action = [
          "glue:GetDatabase",
          "glue:GetTable",
          "glue:GetPartitions",
          "glue:CreateTable",
          "glue:UpdateTable",
          "glue:BatchCreatePartition"
        ]
        Resource = "*"
      },
      {
        Sid    = "KMSAccess"
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:Encrypt",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = aws_kms_key.genomics.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ingestion_attach" {
  role       = aws_iam_role.ingestion.name
  policy_arn = aws_iam_policy.ingestion_s3tables.policy_arn
}

# Analyst / Genomic Researcher Role for executing federated Athena / OMOP queries
resource "aws_iam_role" "analyst" {
  name = "${var.project_name}-analyst-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${local.account_id}:root"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_policy" "analyst_query" {
  name        = "${var.project_name}-analyst-policy-${var.environment}"
  description = "Read-only query permissions for Athena, S3 Tables, and Custom Iceberg"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AthenaExecution"
        Effect = "Allow"
        Action = [
          "athena:StartQueryExecution",
          "athena:GetQueryExecution",
          "athena:GetQueryResults",
          "athena:StopQueryExecution",
          "athena:GetWorkGroup"
        ]
        Resource = aws_athena_workgroup.genomics.arn
      },
      {
        Sid    = "AthenaResultsBucket"
        Effect = "Allow"
        Action = [
          "s3:GetBucketLocation",
          "s3:GetObject",
          "s3:ListBucket",
          "s3:PutObject"
        ]
        Resource = [
          aws_s3_bucket.athena_results.arn,
          "${aws_s3_bucket.athena_results.arn}/*"
        ]
      },
      {
        Sid    = "S3TablesRead"
        Effect = "Allow"
        Action = [
          "s3tables:GetTableBucket",
          "s3tables:GetNamespace",
          "s3tables:GetTable",
          "s3tables:GetTableMetadataLocation",
          "s3tables:GetTableData"
        ]
        Resource = [
          aws_s3tables_table_bucket.variants.arn,
          "${aws_s3tables_table_bucket.variants.arn}/*"
        ]
      },
      {
        Sid    = "CustomIcebergAndClinicalS3Read"
        Effect = "Allow"
        Action = [
          "s3:GetBucketLocation",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.iceberg_warehouse.arn,
          "${aws_s3_bucket.iceberg_warehouse.arn}/*",
          aws_s3_bucket.clinical_data.arn,
          "${aws_s3_bucket.clinical_data.arn}/*"
        ]
      },
      {
        Sid    = "GlueCatalogRead"
        Effect = "Allow"
        Action = [
          "glue:GetCatalog",
          "glue:GetCatalogs",
          "glue:GetDatabase",
          "glue:GetDatabases",
          "glue:GetTable",
          "glue:GetTables",
          "glue:GetPartitions"
        ]
        Resource = "*"
      },
      {
        Sid    = "KMSDecrypt"
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey",
          "kms:GenerateDataKey*"
        ]
        Resource = aws_kms_key.genomics.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "analyst_attach" {
  role       = aws_iam_role.analyst.name
  policy_arn = aws_iam_policy.analyst_query.policy_arn
}

# Clinical Geneticist / Data Steward Role (PHI Privileged)
resource "aws_iam_role" "clinical_steward" {
  name = "${var.project_name}-clinical-steward-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${local.account_id}:root"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_policy" "clinical_steward_policy" {
  name        = "${var.project_name}-clinical-steward-policy-${var.environment}"
  description = "Privileged access to full genomic variants including identifying sample calls (PHI)"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AthenaExecution"
        Effect = "Allow"
        Action = [
          "athena:StartQueryExecution",
          "athena:GetQueryExecution",
          "athena:GetQueryResults",
          "athena:StopQueryExecution",
          "athena:GetWorkGroup"
        ]
        Resource = aws_athena_workgroup.genomics.arn
      },
      {
        Sid    = "AthenaResultsBucket"
        Effect = "Allow"
        Action = [
          "s3:GetBucketLocation",
          "s3:GetObject",
          "s3:ListBucket",
          "s3:PutObject"
        ]
        Resource = [
          aws_s3_bucket.athena_results.arn,
          "${aws_s3_bucket.athena_results.arn}/*"
        ]
      },
      {
        Sid    = "FullS3WarehouseRead"
        Effect = "Allow"
        Action = [
          "s3:GetBucketLocation",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.iceberg_warehouse.arn,
          "${aws_s3_bucket.iceberg_warehouse.arn}/*",
          aws_s3_bucket.clinical_data.arn,
          "${aws_s3_bucket.clinical_data.arn}/*"
        ]
      },
      {
        Sid    = "S3TablesFullRead"
        Effect = "Allow"
        Action = [
          "s3tables:GetTableBucket",
          "s3tables:GetNamespace",
          "s3tables:GetTable",
          "s3tables:GetTableMetadataLocation",
          "s3tables:GetTableData"
        ]
        Resource = [
          aws_s3tables_table_bucket.variants.arn,
          "${aws_s3tables_table_bucket.variants.arn}/*"
        ]
      },
      {
        Sid    = "GlueCatalogRead"
        Effect = "Allow"
        Action = [
          "glue:GetCatalog",
          "glue:GetCatalogs",
          "glue:GetDatabase",
          "glue:GetDatabases",
          "glue:GetTable",
          "glue:GetTables",
          "glue:GetPartitions"
        ]
        Resource = "*"
      },
      {
        Sid    = "KMSDecrypt"
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey",
          "kms:GenerateDataKey*"
        ]
        Resource = aws_kms_key.genomics.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "clinical_steward_attach" {
  role       = aws_iam_role.clinical_steward.name
  policy_arn = aws_iam_policy.clinical_steward_policy.policy_arn
}
