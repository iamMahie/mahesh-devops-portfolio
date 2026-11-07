# Mahesh Devops Portfolio

# WED STUDIOZS
A photography website and studio workspace, served by one FastAPI application.
Jinja templates, local CSS, and plain JavaScript keep the frontend in the same
deployable artifact. There is no Node build, separate frontend service, or
Bootstrap CDN dependency.

[Read the Application Documentation](./wed-studiozs/README.md)

# DevOps Stack

***Containerization: Docker + Kubernetes***

* Multi-stage Dockerfile, non-root user, image size actually optimized
* Deployment + Service + Ingress
* ConfigMaps/Secrets for all config — nothing hardcoded
* Resource requests/limits + readiness/liveness probes tuned
* Horizontal Pod Autoscaler configured

[Docker](./Docker/README.md)

[Kubernetes](./KubernetesConfig/README.md)


***CI/CD***

* Stages: lint/test → build → push to ECR → deploy to EKS
* Different behavior for PR (test only) vs merge to main (full deploy)
* Auth to AWS via OIDC — no long-lived access keys as secrets.
* Images tagged with git SHA, never latest

[CI/CD Implementation](./github/README.md)

***IaC: Terraform***

* Modular structure, not one giant main.tf
* Remote state in S3 with DynamoDB locking

[IAC using Terraform](./Terraform/README.md)

