terraform {
  backend "s3" {
    bucket       = "foundation-bootstrap-state-905418096305-eu-central-1"
    key          = "foundation/bootstrap/tofu.tfstate"
    region       = "eu-central-1"
    encrypt      = true
    use_lockfile = true
  }
}
