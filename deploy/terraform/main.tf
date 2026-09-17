provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.common_tags
  }
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  account_id  = data.aws_caller_identity.current.account_id
  region      = data.aws_region.current.name
  bucket_name = var.table_bucket_name != null ? var.table_bucket_name : lower("${var.project_name}-${var.environment}-${substr(local.account_id, 0, 8)}")

  common_tags = merge(var.tags, {
    Environment = var.environment
  })
}
