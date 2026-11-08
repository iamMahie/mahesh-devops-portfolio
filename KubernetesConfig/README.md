# Containerization with Kubernetes


**Kubernetes**
- Non-root, read-only filesystem, dropped capabilities, seccomp, Pod Security Admission labels
- Startup/readiness/liveness probes, resource limits, zero-downtime rolling updates, HPA
- ResourceQuota, LimitRange, default-deny NetworkPolicies
- Alembic migration Job before rollout
- Secrets from AWS Secrets Manager via External Secrets
- `/metrics` scraped by Prometheus via ServiceMonitor
