terraform {
  backend "s3" {
    bucket       = "wed-studiozs-storage"
    key          = "Terraform/DEV/terraform.tfstate"
    region       = "ap-south-1"
    encrypt      = true
    use_lockfile = true
  }
}
