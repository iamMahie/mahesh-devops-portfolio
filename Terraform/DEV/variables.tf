variable "aws_region" {
  type        = string
  description = "Aws region for resources to be deployed"
  default     = "ap-south-1"
}

variable "project" {
  type    = string
  default = "wed-studiozs"
}

variable "common_tags" {
  type = map(string)
}
