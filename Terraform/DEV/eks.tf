module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 21.0"

  name               = local.cluster_name
  kubernetes_version = "1.33"

  addons = {
    coredns                = {}
    eks-pod-identity-agent = {
      before_compute = true
    }
    kube-proxy             = {}
    vpc-cni                = {
      before_compute = true
    }
    node-monitoring-agent = {
      before_compute = true
    }

  }

  # The cluster endpoint is accessible from outside of your VPC. Worker node traffic will leave your VPC to connect to the endpoint.
  endpoint_public_access = true

  # Adds the current caller identity as an administrator via cluster access entry
  enable_cluster_creator_admin_permissions = true

  vpc_id                   = module.vpc.vpc_id
  subnet_ids               = module.vpc.private_subnet_ids

  # EKS Managed Node Group(s)
  eks_managed_node_groups = {
    worker_nodes = {
      ami_type               = "AL2_x86_64"
      instance_types         = ["t3.medium"]

      min_size     = 2
      max_size     = 6
      desired_size = 2
    }
  }

  # Allow traffc from the load balancer security group on the actual backend port
  node_security_group_additional_rules = {
    from_load_balancer = {
      description              = "Allow the load balancer to reach the application"
      protocol                 = "tcp"
      from_port                = 30080 # Replace with the actual target port
      to_port                  = 30080 # Replace with the actual target port
      type                     = "ingress"
      source_security_group_id = aws_security_group.lb.id
    }
  }

  tags = {
    cluster = "wed-studiozs-application"
  }
}
