# Administration OpenTofu state bucket and access controls.
resource "aws_s3_bucket" "administration_state" {
  bucket        = "aws-administration-state-905418096305-eu-central-1"
  force_destroy = false

  tags = {
    ManagedBy = "opentofu"
    Component = "administration-state"
  }

  lifecycle {
    prevent_destroy = true
  }
}
