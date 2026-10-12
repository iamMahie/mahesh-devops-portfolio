module "s3_bucket" {
  source  = "terraform-aws-modules/s3-bucket/aws"

  bucket = "$(var.project)-storage"

  # Recover previous state versions
  versioning = {
    enabled = true
  }

  # Protect against public access
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true

  # Require encrypted connections
  attach_deny_insecure_transport_policy = true

  tags = var.common_tags
}
