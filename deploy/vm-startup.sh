#!/bin/bash
# Tendly Buyer VM startup script.
# Runs once on first boot. Installs Docker + Compose v2 and configures
# the Artifact Registry credential helper for root (so `sudo docker pull` works).
set -euo pipefail

BOOTSTRAP_FLAG=/var/lib/tendly-buyer-bootstrapped
if [ -f "$BOOTSTRAP_FLAG" ]; then
    exit 0
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y curl ca-certificates

# Install Docker (with Compose v2 plugin) via the official script.
curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
sh /tmp/get-docker.sh
systemctl enable --now docker

# Configure Artifact Registry credential helper for root (VM SA powers it).
gcloud auth configure-docker europe-north1-docker.pkg.dev --quiet

mkdir -p /opt/tendly-buyer
touch "$BOOTSTRAP_FLAG"
