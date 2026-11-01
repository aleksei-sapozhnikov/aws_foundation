# Account administration state lives in the central protected S3 bucket.
terraform {
  backend "s3" {
    bucket       = "aws-administration-state-905418096305-eu-central-1"
    key          = "aws_account/tofu.tfstate"
    region       = "eu-central-1"
    encrypt      = true
    use_lockfile = true
  }
}
