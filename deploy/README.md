# Deploying tendly-buyer to GCP (small VM + small Cloud SQL)

A single GitHub Actions workflow (`.github/workflows/deploy-vm.yml`) provisions and
deploys everything. Re-running is safe — every step is idempotent.

## Architecture

```
                     GitHub Actions (deploy-vm.yml)
                              │
                              │ build & push image
                              ▼
                    Artifact Registry (tendly-buyer)
                              │
                              │ pulled from VM
                              ▼
   GCE VM (e2-small, Debian 12)              Cloud SQL (db-f1-micro, Postgres 15)
   ┌────────────────────────────┐            ┌────────────────────────────────┐
   │  docker compose            │            │  tendly-buyer-db                │
   │   ├─ buyer-db-proxy ───────┼───────────▶│   └─ tendly_buyer (DB)         │
   │   │   (cloud-sql-proxy v2) │            │       └─ tendly_buyer (user)    │
   │   └─ app  ──── port 80     │            └────────────────────────────────┘
   │       └─ uses VM SA for                  ▲
   │          read-only access ──────────────┐│
   └────────────────────────────┘            ││
                                             ││ via cloud-sql-python-connector
                                             │▼
                                  Cloud SQL: tendly-prod (READ ONLY)
```

## Resources created

| Resource | Name | Spec |
|---|---|---|
| GCE VM | `tendly-buyer-vm` (zone `europe-north1-b`) | `e2-small`, 20 GB pd-balanced, Debian 12 |
| Cloud SQL | `tendly-buyer-db` (`europe-north1`) | `db-f1-micro`, Postgres 15, 10 GB HDD, ZONAL |
| Service account | `tendly-buyer-vm-sa@…` | runtime SA attached to the VM |
| Artifact Registry | `tendly-buyer` (`europe-north1`) | Docker repo |
| Firewall | `tendly-buyer-allow-http`, `tendly-buyer-allow-iap-ssh` | tcp:80,443 + IAP SSH |
| Secrets | `tendly-buyer-prod-buyer-db-password`, `tendly-buyer-prod-session-secret` | auto-generated on first run |

## Approximate monthly cost

| Item | Est. cost |
|---|---|
| `e2-small` VM (730h, sustained-use discount) | ~$13 |
| `db-f1-micro` + 10 GB HDD + backups | ~$8–10 |
| Egress / Artifact Registry | <$1 |
| **Total** | **~$22/mo** |

## Required GitHub secret

| Secret | Purpose |
|---|---|
| `GCP_SA_KEY` | JSON key for the **deployer** service account (used by `google-github-actions/auth@v2`). |

## Deployer service account roles

The SA whose JSON key you paste into `GCP_SA_KEY` needs broad rights because the
workflow provisions infra on first run. Recommended bundle (project-level):

- `roles/serviceusage.serviceUsageAdmin` (enable APIs)
- `roles/compute.admin` (create VM + firewall)
- `roles/cloudsql.admin` (create instance, DB, user)
- `roles/artifactregistry.admin` (create repo, push images)
- `roles/secretmanager.admin` (create secrets, grant access)
- `roles/iam.serviceAccountAdmin` (create the runtime SA)
- `roles/iam.serviceAccountUser` (attach SA to the VM)
- `roles/resourcemanager.projectIamAdmin` (grant roles to runtime SA)
- `roles/iap.tunnelResourceAccessor` (SSH into VM via IAP)
- `roles/compute.osAdminLogin` (SSH login on the VM)

Once the infra is stable you can shrink this set; the deploy-only path needs
just compute + artifact-registry + secret-accessor + IAP.

## Pre-existing secrets the workflow expects

These already live in the project's Secret Manager (used by the rest of the
Tendly platform) and are simply read by the workflow:

- `tendly-prod-db-password` — read-only access to `tendly-prod`
- `tendly-prod-gemini-api-key` — Gemini API key
- `tendly-prod-together-api-key` — optional, treated as empty if missing

## Running the workflow

GitHub → Actions → **Deploy Tendly Buyer to GCE** → Run workflow → environment `prod`.

First run creates everything (Cloud SQL takes ~10 min). Subsequent runs only
build the image, copy the new compose/env, run migrations, and `docker compose up -d`.

## Operating the VM

```bash
# SSH (uses IAP — works from anywhere with gcloud auth)
gcloud compute ssh tendly-buyer-vm --zone=europe-north1-b --tunnel-through-iap

# Logs
sudo docker compose -f /opt/tendly-buyer/docker-compose.yml logs -f app

# Restart
sudo docker compose -f /opt/tendly-buyer/docker-compose.yml restart app
```

## Adding HTTPS (later)

Two options:

1. Put a GCP HTTPS Load Balancer in front (managed cert, cleanest, ~$18/mo extra).
2. Add Caddy or nginx + certbot on the VM and point a DNS A record at the VM
   external IP — uses the existing `nginx/tendly-buyer.conf` as a starting point.
