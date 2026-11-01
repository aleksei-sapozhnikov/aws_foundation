output "bootstrap_state_bucket_name" {
  description = "Name of the S3 bucket containing Foundation OpenTofu state."
  value       = aws_s3_bucket.bootstrap_state.id
}
