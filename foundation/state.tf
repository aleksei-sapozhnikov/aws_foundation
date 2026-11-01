# Foundation state bucket protections and access policy.
resource "aws_s3_bucket_versioning" "bootstrap_state" {
  bucket = aws_s3_bucket.bootstrap_state.id

  versioning_configuration {
    status = "Enabled"
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "bootstrap_state" {
  bucket = aws_s3_bucket.bootstrap_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "bootstrap_state" {
  bucket                  = aws_s3_bucket.bootstrap_state.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "bootstrap_state" {
  bucket = aws_s3_bucket.bootstrap_state.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

data "aws_iam_policy_document" "bootstrap_state" {
  statement {
    sid     = "DenyInsecureTransport"
    effect  = "Deny"
    actions = ["s3:*"]
    resources = [
      aws_s3_bucket.bootstrap_state.arn,
      "${aws_s3_bucket.bootstrap_state.arn}/*",
    ]

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

  # Only the account root can access Foundation state.
  statement {
    sid     = "DenyNonRootPrincipalAccess"
    effect  = "Deny"
    actions = ["s3:*"]
    resources = [
      aws_s3_bucket.bootstrap_state.arn,
      "${aws_s3_bucket.bootstrap_state.arn}/*",
    ]

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    condition {
      test     = "StringNotEquals"
      variable = "aws:PrincipalArn"
      values   = ["arn:aws:iam::905418096305:root"]
    }
  }
}

resource "aws_s3_bucket_policy" "bootstrap_state" {
  bucket = aws_s3_bucket.bootstrap_state.id
  policy = data.aws_iam_policy_document.bootstrap_state.json

  depends_on = [aws_s3_bucket_public_access_block.bootstrap_state]
}
