# Mahesh Devops Portfolio

*** WED STUDIOZS ***
A photography website and studio workspace, served by one FastAPI application.
Jinja templates, local CSS, and plain JavaScript keep the frontend in the same
deployable artifact. There is no Node build, separate frontend service, or
Bootstrap CDN dependency.

[Read the Application Documentation](./wed-studiozs/README.md)

***DevOps Stack***

# Containerization: Docker + Kubernetes

Multi-stage Dockerfile, non-root user, image size actually optimized
Deployment + Service + Ingress
ConfigMaps/Secrets for all config — nothing hardcoded
Resource requests/limits + readiness/liveness probes tuned
Horizontal Pod Autoscaler configured

# CI/CD

Stages: lint/test → build → push to ECR → deploy to EKS
Different behavior for PR (test only) vs merge to main (full deploy)
Auth to AWS via OIDC — no long-lived access keys as secrets.
Images tagged with git SHA, never latest

# IaC: Terraform + Bicep

Modular structure, not one giant main.tf
Remote state in S3 with DynamoDB locking

# Monitoring

Scrape both cluster metrics and app-level metrics (expose a /metrics endpoint from your app)
At least 2 real dashboards — not the untouched default templates
An Alertmanager rule that fires on something real (error rate spike, restart count) and routes to Slack or email

# Bash/Python Automation

Python: a cluster health-check CLI (boto3 + kubernetes client) — node status, pod restart counts, cert expiry — outputs a report
Bash: an ECR cleanup script — deletes images older than N days, except whatever's currently deployed
