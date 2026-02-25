output "cur_bucket" {
  value       = aws_s3_bucket.cur_bucket.bucket
  description = "CUR destination bucket."
}

