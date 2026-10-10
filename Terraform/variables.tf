variable "aws_region" {
    type = string
    description = "Aws region for region to be deployed"
    default = "ap-south-2"
}

variable "project" {
    type = string
    default = "wed-studiozs"
}

variable "common_tags" {
    type = map(string)
}