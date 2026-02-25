variable "region" {
  type        = string
  description = "AWS region for the example."
  default     = "us-east-1"
}

variable "cur_bucket_name" {
  type        = string
  description = "S3 bucket to receive CUR files."
}

variable "report_name" {
  type        = string
  description = "CUR report name."
  default     = "cloud-cost-audit-demo-cur"
}

