# storage bucket outputs
output "bucket_id" {
  description = "Name of the Terraform state bucket"
  value       = module.s3_bucket.s3_bucket_id
}

output "bucket_arn" {
  description = "ARN of the Terraform state bucket"
  value       = module.s3_bucket.s3_bucket_arn
}