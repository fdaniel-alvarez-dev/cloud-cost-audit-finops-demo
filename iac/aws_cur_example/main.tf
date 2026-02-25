terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0.0"
    }
  }
}

provider "aws" {
  region = var.region
}

resource "aws_s3_bucket" "cur_bucket" {
  bucket = var.cur_bucket_name
}

resource "aws_s3_bucket_versioning" "cur_bucket" {
  bucket = aws_s3_bucket.cur_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

# CUR report definition (example). This requires the CUR service permission in the payer account.
resource "aws_cur_report_definition" "cur" {
  report_name                = var.report_name
  time_unit                  = "HOURLY"
  format                     = "textORcsv"
  compression                = "GZIP"
  additional_schema_elements = ["RESOURCES"]

  s3_bucket = aws_s3_bucket.cur_bucket.bucket
  s3_prefix = "cur"
  s3_region = var.region

  refresh_closed_reports = true
  report_versioning      = "CREATE_NEW_REPORT"
}

