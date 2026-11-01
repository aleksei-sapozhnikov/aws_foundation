# AWS Foundation

OpenTofu configuration for AWS account `905418096305` in `eu-central-1`.

## Configuration

| Directory | Managed resources | State |
| --- | --- | --- |
| `foundation/` | `administrator` IAM user, AdministratorAccess attachment, and Foundation S3 state bucket with access controls | `foundation-bootstrap-state-905418096305-eu-central-1/foundation/bootstrap/tofu.tfstate` |
| `administration/aws_account/` | GitHub Actions OIDC provider, Session Manager preferences, and Administration S3 state bucket with access controls | `aws-administration-state-905418096305-eu-central-1/aws_account/tofu.tfstate` |

Each directory is an independent OpenTofu root with its own `backend.tf`
and `.terraform.lock.hcl`.

The Foundation state bucket allows access only to the AWS account root.
The Administration state bucket allows access to the account root and
`administrator`.

## Usage

Use the authorized AWS identity for the selected root, then run from its
directory:

```sh
aws sts get-caller-identity
tofu init -input=false -lockfile=readonly
tofu state list
tofu validate
tofu plan
```

For `foundation/`, also supply `bootstrap_state_bucket_name` as a variable
using a local `.tfvars` file or `-var`. Its value must match the bucket in
`foundation/backend.tf`.

Review the plan before applying. State files, credentials, plans, and local
variable values are not committed.

## Quality checks

Install Python 3.12+ and GNU Make. QA installs pinned OpenTofu 1.13.1,
TFLint 0.65.0, its AWS ruleset 0.50.0, and PyYAML 6.0.3 locally as needed.
Official OpenTofu and TFLint release archives are checked against SHA-256
manifests before extraction.

```sh
make qa-format  # Format, validate, and lint both OpenTofu roots
make qa-check   # Check formatting, validate, and lint without edits
```

Both commands check `foundation/` and `administration/aws_account/` and
validate repository files for final newlines, LF line endings, trailing
whitespace, conflict markers, JSON/YAML syntax, and the 500 KiB file limit.
Validation uses `tofu init -backend=false -lockfile=readonly` and isolated
local data directories. QA does not access remote state or require AWS credentials.
Downloaded tools and caches live in Git-ignored `.local/qa-runtime/`.

Pull requests targeting `main` run `make qa-check` automatically through
`.github/workflows/qa-check.yml`.
