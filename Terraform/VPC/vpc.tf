resource "aws_vpc" "main" {
    cidr_block = var.vpc_cidr
    enable_dns_support = true
    enable_dns_hostnames = true

    tags = {
        Name = "${var.project}-vpc"
    }
}

# Internet gateway 
resource "aws_internet_gateway"  "main_ig" {
    vpc_id = aws_vpc.main.id

    tags = {
        Name = "${var.project}-internet-gateway"
    }
}

# Public Subnets
resource "aws_subnet" "public_subnet" {
    vpc_id = aws_vpc.main.id
    cidr_block = var.public_cidr
}