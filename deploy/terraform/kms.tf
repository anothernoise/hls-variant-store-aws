# Dedicated Customer Managed Key (CMK) for Genomic Data Protection at Rest
resource "aws_kms_key" "genomics" {
  description             = "CMK for HLS genomic variant store and S3 Tables encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "EnableRootIAMAccess"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${local.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "AllowS3TablesMaintenanceService"
        Effect = "Allow"
        Principal = {
          Service = "maintenance.s3tables.amazonaws.com"
        }
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = local.account_id
          }
        }
      },
      {
        Sid    = "AllowS3ServiceAccess"
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = local.account_id
          }
        }
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-kms-${var.environment}"
  }
}

resource "aws_kms_alias" "genomics" {
  name          = "alias/${var.project_name}-${var.environment}"
  target_key_id = aws_kms_key.genomics.key_id
}
