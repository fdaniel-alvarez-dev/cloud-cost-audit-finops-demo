terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_bigquery_dataset" "billing" {
  dataset_id  = var.dataset_id
  description = "Dataset to store exported billing data (example)."
  location    = var.location
}

resource "google_bigquery_table" "billing_export" {
  dataset_id = google_bigquery_dataset.billing.dataset_id
  table_id   = var.table_id

  # Billing export schemas are managed by Google; this table is a placeholder for demonstration.
  deletion_protection = true
}

