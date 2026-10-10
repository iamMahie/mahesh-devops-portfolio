variable "aws_region" {
    type = string
    description = "Aws region for region to be deployed"
    default = "ap-south-2"
}

variable "project" {
    type = string
    default = "wed-studiozs"
}

variable "vpc_cidr {
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

variable "tags" {
    type = map(string)
    default = {}
}