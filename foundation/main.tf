# Root-protected Foundation state bucket.
resource "aws_s3_bucket" "bootstrap_state" {
  bucket        = var.bootstrap_state_bucket_name
  force_destroy = false

  tags = {
    ManagedBy = "opentofu"
    Component = "foundation-bootstrap-state"
  }

  lifecycle {
    prevent_destroy = true
  }
}
