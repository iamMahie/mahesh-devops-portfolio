resource "aws_vpc" "main" {
    cidr_block = var.vpc_cidr
    enable_dns_support = true
    enable_dns_hostnames = true

    tags = merge(var.tags, { Name = "${var.project}-vpc" })
}

# Internet gateway 
resource "aws_internet_gateway"  "main_ig" {
    vpc_id = aws_vpc.main.id

    tags = merge(
        var.tags, { Name = "${var.project}-internet-gateway" }
    )
}

# Public Subnets
resource "aws_subnet" "public_subnet" {
    count = length(var.public_subnet_cidrs)
    availability_zone = var.azs[count.index]
    vpc_id = aws_vpc.main.id
    cidr_block = var.public_subnet_cidrs[count.index]
    map_public_ip_on_launch = true

    tags = merge(var.tags, { Name = "${var.project}-public-subnet-${count.index + 1}" })
}

# Route Tables for public subnet
resource "aws_route_table" "public_rt" {
    vpc_id = aws_vpc.main.id
    route {
        cidr_block = "0.0.0.0/0"
        gateway_id = aws_internet_gateway.main_ig.id
    }

    tags = merge(var.tags, { Name = "${var.project}-public-rt" })
}

# Route table association for public subnet
resource "aws_route_table_association" "public_rta" {
    count = length(var.public_subnet_cidrs)
    subnet_id = aws_subnet.public_subnet[count.index].id
    route_table_id = aws_route_table.public_rt.id
}

# Private Subnets
resource "aws_subnet" "private_subnet" {
    count = length(var.private_subnet_cidrs)
    availability_zone = var.azs[count.index]
    vpc_id = aws_vpc.main.id
    cidr_block = var.private_subnet_cidrs[count.index]
    tags = merge(var.tags, { Name = "${var.project}-private-${count.index + 1}" })
}

# Elastic ip for private subnet
resource "aws_eip" "nat_eip" {
    domain = "vpc"
}


# Nat gateway
resource "aws_nat_gatewat" "nat_gateway" {
    allocation_id = aws_eip.nat_eip.id
    subnet_id = aws_subnet.private_subnet[0].id

    tags = merge(
        var.tags, { Name = "${var.project}-nat-gateway" }
    )
    depends_on = [aws_internet_gateway.main_ig]
}

# Route tables for private subnet
resource "aws_route_table" "private_rt" {
    vpc_id = aws_vpc.main.id
    route {
        cidr_block = "0.0.0.0/0"
        gateway_id = aws_nat_gatewat.nat_gateway.id
    }

    tags = merge{
        var.tags, { Name = "${var.project}-private-rt" }
    }
}

# Route table association for private subnet
resource "aws_route_table_association" "private_rta" {
    count = length(var.private_subnet_cidrs)
    subnet_id = aws_subnet.private_subnet[count.index].id
    route_table_id = aws_route_table.private_rt.id
}