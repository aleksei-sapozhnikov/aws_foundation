# Administration state bucket protections and access policy.
resource "aws_s3_bucket_versioning" "administration_state" {
  bucket = aws_s3_bucket.administration_state.id
  versioning_configuration {
    status = "Enabled"
  }
  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "administration_state" {
  bucket = aws_s3_bucket.administration_state.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "administration_state" {
  bucket                  = aws_s3_bucket.administration_state.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "administration_state" {
  bucket = aws_s3_bucket.administration_state.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

data "aws_iam_policy_document" "administration_state" {
  statement {
    sid       = "DenyInsecureTransport"
    effect    = "Deny"
    actions   = ["s3:*"]
    resources = [aws_s3_bucket.administration_state.arn, "${aws_s3_bucket.administration_state.arn}/*"]
    principals {
      type        = "*"
      identifiers = ["*"]
    }
    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }

  # Restrict state access to the account root and administrator.
  statement {
    sid       = "DenyNonAdministrators"
    effect    = "Deny"
    actions   = ["s3:*"]
    resources = [aws_s3_bucket.administration_state.arn, "${aws_s3_bucket.administration_state.arn}/*"]
    principals {
      type        = "*"
      identifiers = ["*"]
    }
    condition {
      test     = "ArnNotEquals"
      variable = "aws:PrincipalArn"
      values = [
        "arn:aws:iam::905418096305:root",
        "arn:aws:iam::905418096305:user/administrator",
      ]
    }
  }
}

resource "aws_s3_bucket_policy" "administration_state" {
  bucket     = aws_s3_bucket.administration_state.id
  policy     = data.aws_iam_policy_document.administration_state.json
  depends_on = [aws_s3_bucket_public_access_block.administration_state]
}
