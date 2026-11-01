# Account-wide GitHub Actions OIDC provider.
resource "aws_iam_openid_connect_provider" "github_actions" {
  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]

  tags = {
    Scope = "account"
  }

  lifecycle {
    prevent_destroy = true
  }
}
