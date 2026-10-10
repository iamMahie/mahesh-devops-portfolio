variable "aws_region" {
    type = string
    description = "Aws region for resources to be deployed"
    default = "ap-south-2"
}

variable "project" {
    type = string
    default = "wed-studiozs"
}

variable "tags" {
    type = map(string)
    default = {}
}

variable "vpc_cidr" {
    type = string
}

variable "public_subnet_cidrs" {
    type = list(string)
}

variable "private_subnet_cidrs" {
    type = list(string)
}

variable "azs" {
    type = list(string)
}

# EKS variables

variable "cluster_name" {
  type = string
}

variable "cluster_version" {
  type = string
}