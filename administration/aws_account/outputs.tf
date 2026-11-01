output "administration_state_bucket_name" {
  description = "Name of the S3 bucket containing Administration OpenTofu state."
  value       = aws_s3_bucket.administration_state.id
}
