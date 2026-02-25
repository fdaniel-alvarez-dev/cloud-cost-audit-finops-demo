# IaC examples (safe, optional)

These Terraform snippets are included to demonstrate how the same patterns would be wired in a real client environment.

- They are **not required** to run the local demo (`make demo`).
- They are intentionally safe: no secrets, no destructive defaults, and heavy comments.

## AWS
- `iac/aws_cur_example/`: example of delivering CUR to S3 and querying with Athena.

## GCP
- `iac/gcp_billing_export_example/`: example BigQuery dataset/table scaffolding for billing exports.

