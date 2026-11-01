# IAM user for account administration.
resource "aws_iam_user" "administrator" {
  name = "administrator"
  path = "/"

  tags = {
    ManagedBy = "opentofu"
  }

  lifecycle {
    prevent_destroy = true
  }
}

# AdministratorAccess granted to the administrator IAM user.
resource "aws_iam_user_policy_attachment" "administrator_access" {
  user       = aws_iam_user.administrator.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"

  lifecycle {
    prevent_destroy = true
  }
}
