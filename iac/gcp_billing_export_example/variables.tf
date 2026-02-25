variable "project_id" {
  type        = string
  description = "GCP project that will host the BigQuery dataset."
}

variable "region" {
  type        = string
  description = "Provider region."
  default     = "us-central1"
}

variable "location" {
  type        = string
  description = "BigQuery dataset location."
  default     = "US"
}

variable "dataset_id" {
  type        = string
  description = "BigQuery dataset id."
  default     = "billing_export"
}

variable "table_id" {
  type        = string
  description = "BigQuery table id."
  default     = "gcp_billing_export"
}

