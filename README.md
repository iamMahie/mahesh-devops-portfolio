# Mahesh Devops Portfolio

*** WED STUDIOZS ***
A photography website and studio workspace, served by one FastAPI application.
Jinja templates, local CSS, and plain JavaScript keep the frontend in the same
deployable artifact. There is no Node build, separate frontend service, or
Bootstrap CDN dependency.

[Read the Application Documentation](./wed-studiozs/README.md)

*** Hands-On DevOps Stack ***
Format: One project, built end-to-end, not tutorial-followed.

# Containerization: Docker + Kubernetes

Build: Take any app with a database dependency (a simple API + Postgres/Redis works fine) and deploy it to EKS, production-style — not "it runs."

Requirements that separate this from a tutorial:

Multi-stage Dockerfile, non-root user, image size actually optimized
Deployment + Service + Ingress (not just a bare LoadBalancer)
ConfigMaps/Secrets for all config — nothing hardcoded
Resource requests/limits + readiness/liveness probes tuned, not copy-pasted defaults
Horizontal Pod Autoscaler configured and tested — generate load, watch it actually scale

# CI/CD Deep Dive

Build: Automate Day 1's deploy with GitHub Actions.

Requirements:

Stages: lint/test → build → push to ECR → deploy to EKS
Different behavior for PR (test only) vs merge to main (full deploy)
Auth to AWS via OIDC — no long-lived access keys as secrets. This one detail is a real interview differentiator.
Images tagged with git SHA, never latest

# IaC: Terraform + Bicep

Honest scoping note: deep Terraform and deep Bicep in one day isn't realistic. Split the effort instead of splitting it evenly.

Main build (Terraform, AWS): Rewrite Day 1's EKS + VPC as Terraform modules.

Modular structure, not one giant main.tf
Remote state in S3 with DynamoDB locking
Destroy and rebuild the cluster from code only — no manual console steps left

Lighter build (Bicep, Azure): One resource group with a storage account + minimal AKS cluster (control plane is free — keep node size/count small). The goal isn't depth, it's being able to explain Bicep vs. Terraform trade-offs in an interview.

# Monitoring Deep Dive

Build: Instrument Day 1's cluster with Prometheus + Grafana via Helm.

Requirements:

Scrape both cluster metrics and app-level metrics (expose a /metrics endpoint from your app)
At least 2 real dashboards — not the untouched default templates
An Alertmanager rule that fires on something real (error rate spike, restart count) and routes to Slack or email

# Bash/Python Automation

Build: Two tools you'd actually use on the job, not toy scripts.

Python: a cluster health-check CLI (boto3 + kubernetes client) — node status, pod restart counts, cert expiry — outputs a report, optionally posts to Slack
Bash: an ECR cleanup script — deletes images older than N days, except whatever's currently deployed