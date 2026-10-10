# locals

locals {
    cluster_name = "wed-studiozs-cluster-${randon_string.suffix.result}"
}

resource "randon_string" "suffix" {
    length = 9
    special = false
}

# VPC 
module "vpc" {
    source = "./modules/vpc"
    
    project = var.project
    vpc_cidr = "10.0.0.0/16"
    public_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24"]
    private_subnet_cidrs = ["10.0.11.0/24", "10.0.12.0/24"]
    azs = ["${var.aws_region}a", "${var.aws_region}b"]
    tags = var.common_tags

}