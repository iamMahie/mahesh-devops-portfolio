# Infrastructure (Terraform)
- Custom VPC module: 2 public + 2 private subnets across 2 AZs, NAT gateway
- EKS 1.33 (AL2023 managed nodes, IMDSv2) with EBS CSI and metrics-server add-ons
- GitHub OIDC provider, least-privilege CI roles, EKS access entries
- S3 remote state with versioning, TLS-only policy, native state locking
- `fmt`, `validate`, `plan` on every pull request
