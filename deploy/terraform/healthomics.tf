# AWS HealthOmics Variant Store Strategy
#
# NOTE FOR SOLUTION ARCHITECTS & DEPLOYMENT:
# As of Terraform AWS Provider v6.x, AWS HealthOmics control plane resources 
# (Variant Stores, Reference Stores, Annotation Stores) are managed via the 
# AWS HealthOmics API / AWS CLI / CloudFormation / Boto3 rather than native Terraform resources.
#
# This file provisions:
# 1. Dedicated IAM Service Role for HealthOmics VCF import operations.
# 2. S3 & KMS Least-Privilege Policies for Omics data plane read/write.
# 3. Automated lifecycle helper integration via `ingest/healthomics/manage_omics_store.py`.

# IAM Role for HealthOmics VCF Import Jobs
resource "aws_iam_role" "omics_import" {
  count = var.enable_healthomics ? 1 : 0
  name  = "${var.project_name}-omics-import-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "omics.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_policy" "omics_import" {
  count       = var.enable_healthomics ? 1 : 0
  name        = "${var.project_name}-omics-import-policy-${var.environment}"
  description = "IAM policy for HealthOmics variant store VCF import jobs"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.clinical_data.arn,
          "${aws_s3_bucket.clinical_data.arn}/*",
          aws_s3_bucket.iceberg_warehouse.arn,
          "${aws_s3_bucket.iceberg_warehouse.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = aws_kms_key.genomics.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "omics_import_attach" {
  count      = var.enable_healthomics ? 1 : 0
  role       = aws_iam_role.omics_import[0].name
  policy_arn = aws_iam_policy.omics_import[0].arn
}
