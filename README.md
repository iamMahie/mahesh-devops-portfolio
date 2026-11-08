# FastAPI on Amazon EKS — Terraform, Docker & GitHub Actions

Infrastructure, containerization, and CI/CD for a FastAPI + PostgreSQL application on Amazon EKS.
The application code (`wed-studiozs/`) was generated with GitHub Copilot; the infrastructure,
Docker, Kubernetes, and pipeline work is my own.

## Architecture
![Architecture](docs/images/architecture.png) <!-- [fill] -->

GitHub Actions ──(OIDC)──► AWS IAM
   ├─ CI: ruff → pytest (80% coverage) → build → Trivy → SBOM
   └─ CD: push to ECR → compose smoke test → approval → deploy to EKS
EKS (private subnets) ─► Traefik (Gateway API, TLS via cert-manager) ─► FastAPI pods
                                                  └─► PostgreSQL StatefulSet (encrypted gp3)

## Tech Stack
Terraform · AWS (VPC, EKS, IAM, ECR, S3) · Docker · Kubernetes (Kustomize, Gateway API) · Traefik ·
cert-manager · Prometheus · GitHub Actions · Trivy · Syft · FastAPI · PostgreSQL · Alembic

## Capabilities
**Infrastructure (Terraform)**
- Custom VPC module: 2 public + 2 private subnets across 2 AZs, NAT gateway
- EKS 1.33 (AL2023 managed nodes, IMDSv2) with EBS CSI and metrics-server add-ons
- GitHub OIDC provider, least-privilege CI roles, EKS access entries
- S3 remote state with versioning, TLS-only policy, native state locking
- `fmt`, `validate`, `plan` on every pull request

**Container**
- Multi-stage build, digest-pinned base image, non-root user, BuildKit cache, HEALTHCHECK
- Compose stack with DB healthcheck and gated migration service

**Kubernetes**
- Non-root, read-only filesystem, dropped capabilities, seccomp, Pod Security Admission labels
- Startup/readiness/liveness probes, resource limits, zero-downtime rolling updates, HPA
- ResourceQuota, LimitRange, default-deny NetworkPolicies
- Alembic migration Job before rollout
- Secrets from AWS Secrets Manager via External Secrets
- `/metrics` scraped by Prometheus via ServiceMonitor

**CI/CD**
- Images tagged with the commit SHA; actions pinned to SHAs
- Vulnerability scan gates the image push
- Deploy to staging behind GitHub Environment approval, with automatic rollback on failed rollout

## Deployment
```bash
cd Terraform/storage && terraform init && terraform apply          # state bucket
cd ../DEV && cp terraform.tfvars.example terraform.tfvars
terraform init && terraform apply                                  # VPC, EKS, IAM, add-ons
aws eks update-kubeconfig --name [fill] --region ap-south-1
# App deploys via the "Continuous Deployment" workflow
```

## Validation
- Local: `docker compose up` → `curl localhost:8000/readyz`
- Cluster: `kubectl get pods,gateway,httproute -n [fill]`; `kubectl rollout status deploy/[fill]`
- Pipeline: [fill: link to green CI run] · [fill: link to green CD run]

## Evidence
- ![CI run](docs/images/ci-green.png) <!-- [fill] -->
- ![CD run](docs/images/cd-green.png) <!-- [fill] -->
- ![kubectl get pods](docs/images/kubectl-pods.png) <!-- [fill] -->
- ![App via HTTPS](docs/images/app-browser.png) <!-- [fill] -->

## Design Trade-offs
- Single NAT gateway: lower cost, single-AZ egress dependency
- In-cluster PostgreSQL (single replica): Amazon RDS would be the production choice
- t3.small nodes: cost-optimized, limits pod density

