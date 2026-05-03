#!/bin/bash
set -euo pipefail

# Tendly Buyer - GCP Compute Engine deployment script
# Usage: ./deploy-vm.sh [--setup|--deploy|--status]

PROJECT_ID="scenic-impact-476918-n6"
ZONE="europe-north1-b"
VM_NAME="tendly-buyer-beta"
DEPLOY_DIR="/opt/tendly-buyer"

case "${1:-deploy}" in
    --setup)
        echo "=== Initial VM Setup ==="
        gcloud compute ssh $VM_NAME --zone=$ZONE --project=$PROJECT_ID --command="
            set -e
            # System packages
            sudo apt-get update && sudo apt-get upgrade -y
            sudo apt-get install -y python3.12 python3.12-venv python3-pip libpq-dev nginx certbot python3-certbot-nginx git

            # PostgreSQL
            sudo apt-get install -y postgresql postgresql-contrib
            sudo -u postgres psql -c \"CREATE USER tendly_buyer WITH PASSWORD 'CHANGE_ME';\" || true
            sudo -u postgres psql -c \"CREATE DATABASE tendly_buyer OWNER tendly_buyer;\" || true
            sudo -u postgres psql -d tendly_buyer -c \"CREATE SCHEMA IF NOT EXISTS tendly;\" || true
            sudo -u postgres psql -d tendly_buyer -c \"GRANT ALL ON SCHEMA tendly TO tendly_buyer;\" || true

            # App user
            sudo useradd -r -s /bin/false tendly || true
            sudo mkdir -p $DEPLOY_DIR /var/log/tendly-buyer
            sudo chown tendly:tendly /var/log/tendly-buyer

            echo 'Setup complete. Next: clone repo, install deps, configure .env.production'
        "
        ;;

    --deploy)
        echo "=== Deploying Tendly Buyer ==="
        gcloud compute ssh $VM_NAME --zone=$ZONE --project=$PROJECT_ID --command="
            set -e
            cd $DEPLOY_DIR

            # Pull latest code
            sudo -u tendly git pull origin main 2>/dev/null || echo 'First deploy - clone manually first'

            # Install dependencies
            sudo -u tendly bash -c 'source venv/bin/activate && pip install -r requirements.txt -q'

            # Copy systemd service and nginx config
            sudo cp systemd/tendly-buyer.service /etc/systemd/system/
            sudo cp nginx/tendly-buyer.conf /etc/nginx/sites-available/
            sudo ln -sf /etc/nginx/sites-available/tendly-buyer.conf /etc/nginx/sites-enabled/ 2>/dev/null || true

            # Restart services
            sudo systemctl daemon-reload
            sudo systemctl restart tendly-buyer
            sudo nginx -t && sudo systemctl reload nginx

            # Health check
            sleep 3
            if curl -sf http://localhost:5002/ > /dev/null 2>&1; then
                echo '✓ Deploy successful - app is running'
            else
                echo '✗ Deploy FAILED - check logs: sudo journalctl -u tendly-buyer -n 50'
                exit 1
            fi
        "
        ;;

    --status)
        echo "=== Tendly Buyer Status ==="
        gcloud compute ssh $VM_NAME --zone=$ZONE --project=$PROJECT_ID --command="
            echo '--- Service Status ---'
            sudo systemctl status tendly-buyer --no-pager -l
            echo ''
            echo '--- Recent Logs ---'
            sudo journalctl -u tendly-buyer -n 20 --no-pager
            echo ''
            echo '--- Nginx Status ---'
            sudo systemctl status nginx --no-pager
            echo ''
            echo '--- PostgreSQL Status ---'
            sudo systemctl status postgresql --no-pager
            echo ''
            echo '--- Disk Usage ---'
            df -h /
        "
        ;;

    --ssl)
        echo "=== Setting up SSL ==="
        gcloud compute ssh $VM_NAME --zone=$ZONE --project=$PROJECT_ID --command="
            sudo certbot --nginx -d buyer.tendly.eu --non-interactive --agree-tos -m kamelbelkadhi2@gmail.com
        "
        ;;

    *)
        echo "Usage: $0 [--setup|--deploy|--status|--ssl]"
        exit 1
        ;;
esac
