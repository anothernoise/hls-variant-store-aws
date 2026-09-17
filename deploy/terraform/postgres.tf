# Relational Variant Store: PostgreSQL on Amazon RDS vs. Amazon Aurora Serverless v2
# Demonstrates architectural trade-offs for metadata, clinical cohorts, and targeted variant queries

# Random password generation for master user (stored in Secrets Manager)
resource "random_password" "postgres_master" {
  count   = var.enable_postgres ? 1 : 0
  length  = 20
  special = false
}

resource "aws_secretsmanager_secret" "postgres_credentials" {
  count                   = var.enable_postgres ? 1 : 0
  name_prefix             = "genomics-postgres-admin-"
  description             = "PostgreSQL master admin credentials for HLS variant store"
  kms_key_id              = aws_kms_key.genomics.arn
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "postgres_credentials" {
  count     = var.enable_postgres ? 1 : 0
  secret_id = aws_secretsmanager_secret.postgres_credentials[0].id
  secret_string = jsonencode({
    engine   = "postgres"
    username = var.postgres_admin_username
    password = random_password.postgres_master[0].result
    database = var.postgres_db_name
  })
}

# Network: Private DB Subnet Group (Default VPC fallback for lab demo)
data "aws_vpc" "default" {
  count   = var.enable_postgres ? 1 : 0
  default = true
}

data "aws_subnets" "default" {
  count = var.enable_postgres ? 1 : 0
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default[0].id]
  }
}

resource "aws_db_subnet_group" "postgres" {
  count       = var.enable_postgres ? 1 : 0
  name_prefix = "genomics-postgres-"
  subnet_ids  = data.aws_subnets.default[0].ids

  tags = merge(local.common_tags, {
    Tier = "Relational-Variant-Store"
  })
}

resource "aws_security_group" "postgres" {
  count       = var.enable_postgres ? 1 : 0
  name_prefix = "genomics-postgres-sg-"
  vpc_id      = data.aws_vpc.default[0].id
  description = "Security group for genomics PostgreSQL/Aurora instance"

  ingress {
    description = "PostgreSQL access from VPC"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [data.aws_vpc.default[0].cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# OPTION A: Amazon Aurora PostgreSQL (Serverless v2)
# Best for: Auto-scaling variable bioinformatic workloads, instant storage scaling
# -----------------------------------------------------------------------------
resource "aws_rds_cluster" "aurora" {
  count                  = var.enable_postgres && var.postgres_deployment_mode == "aurora_serverless" ? 1 : 0
  cluster_identifier     = "${var.project_name}-aurora-${var.environment}"
  engine                 = "aurora-postgresql"
  engine_version         = "16.8"
  database_name          = var.postgres_db_name
  master_username        = var.postgres_admin_username
  master_password        = random_password.postgres_master[0].result
  db_subnet_group_name   = aws_db_subnet_group.postgres[0].name
  vpc_security_group_ids = [aws_security_group.postgres[0].id]
  kms_key_id             = aws_kms_key.genomics.arn
  storage_encrypted      = true
  skip_final_snapshot    = true
  deletion_protection    = false

  serverlessv2_scaling_configuration {
    min_capacity = 0.5
    max_capacity = 2.0
  }

  tags = merge(local.common_tags, {
    Architecture = "Aurora-Serverless-v2"
  })
}

resource "aws_rds_cluster_instance" "aurora_instance" {
  count              = var.enable_postgres && var.postgres_deployment_mode == "aurora_serverless" ? 1 : 0
  cluster_identifier = aws_rds_cluster.aurora[0].id
  instance_class     = "db.serverless"
  engine             = aws_rds_cluster.aurora[0].engine
  engine_version     = aws_rds_cluster.aurora[0].engine_version
  identifier         = "${var.project_name}-aurora-instance-1"

  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# OPTION B: Amazon RDS PostgreSQL (Single-AZ / Multi-AZ Instance)
# Best for: Predictable provisioned compute, low-cost steady baseline
# -----------------------------------------------------------------------------
resource "aws_db_instance" "rds" {
  count                  = var.enable_postgres && var.postgres_deployment_mode == "rds" ? 1 : 0
  identifier             = "${var.project_name}-rds-${var.environment}"
  engine                 = "postgres"
  engine_version         = "16.1"
  instance_class         = "db.t4g.micro"
  allocated_storage      = 20
  max_allocated_storage  = 50
  db_name                = var.postgres_db_name
  username               = var.postgres_admin_username
  password               = random_password.postgres_master[0].result
  db_subnet_group_name   = aws_db_subnet_group.postgres[0].name
  vpc_security_group_ids = [aws_security_group.postgres[0].id]
  kms_key_id             = aws_kms_key.genomics.arn
  storage_encrypted      = true
  skip_final_snapshot    = true
  deletion_protection    = false

  tags = merge(local.common_tags, {
    Architecture = "RDS-PostgreSQL-Instance"
  })
}
