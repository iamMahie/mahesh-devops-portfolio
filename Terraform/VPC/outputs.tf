output "vpc_id" {
    value = aws_vpc.main.id
}

output "public_subnet_ids" {
    value = aws_subnet.public[*].id
}

output "private_subnet_ids" {
    value = aws_subnet.private[*].id
    description = "The private subnet ids"
}

output "public_route_table_id" {
    description = "Route table id"
    value = aws_route_table.public_rt
}