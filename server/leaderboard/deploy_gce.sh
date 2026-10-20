#!/bin/bash
# Deploys the vn3ds leaderboard to a free-tier e2-micro VM on Google Compute
# Engine. Safe to run again: existing pieces are kept, and a second run ships
# the current leaderboard.py and key and restarts the VM to install them.
#
#   LEADERBOARD_KEY=<key> server/leaderboard/deploy_gce.sh
#
# Settings (environment variables):
#   PROJECT  Google Cloud project   (default: gcloud's configured project)
#   ZONE     a us-central1 zone     (default: us-central1-a; free tier is
#            us-west1, us-central1 and us-east1 only)
#   VM       instance name          (default: vn3ds-leaderboard)
#   LEADERBOARD_KEY  the shared HMAC key; must match LEADERBOARD_KEY in
#            engine/source/leaderboard_config.h (read from there if unset)
#   ALLOW_DEV_KEY=1  deploy even with the public development key
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
PROJECT=${PROJECT:-$(gcloud config get-value project 2>/dev/null)}
ZONE=${ZONE:-us-central1-a}
REGION=${ZONE%-*}
VM=${VM:-vn3ds-leaderboard}
TAG=vn3ds-leaderboard
RULE=vn3ds-leaderboard-http
ADDRESS=vn3ds-leaderboard-ip

[ -n "$PROJECT" ] || { echo "Set PROJECT (or run: gcloud config set project <id>)"; exit 1; }

if [ -z "${LEADERBOARD_KEY:-}" ]; then
    LEADERBOARD_KEY=$(sed -n 's/^#define LEADERBOARD_KEY "\(.*\)"$/\1/p' \
        "$HERE/../../engine/source/leaderboard_config.h" | head -n 1)
fi
[ -n "$LEADERBOARD_KEY" ] || { echo "No LEADERBOARD_KEY"; exit 1; }
if [ "$LEADERBOARD_KEY" = "vn3ds-dev-key-change-me" ] && [ "${ALLOW_DEV_KEY:-}" != 1 ]; then
    echo "LEADERBOARD_KEY is the public development key. Make one with"
    echo "  openssl rand -hex 32"
    echo "put it in engine/source/leaderboard_config.h, rebuild the game, and run this"
    echo "again (or set ALLOW_DEV_KEY=1 for a throwaway test server)."
    exit 1
fi

G="gcloud --project=$PROJECT --quiet"
KEYFILE=$(mktemp)
trap 'rm -f "$KEYFILE"' EXIT
printf '%s' "$LEADERBOARD_KEY" > "$KEYFILE"
META_FILES="startup-script=$HERE/startup.sh,leaderboard-py=$HERE/leaderboard.py,leaderboard-key=$KEYFILE"

echo "== project $PROJECT, zone $ZONE, VM $VM"
$G services enable compute.googleapis.com

# A static address, so the IP baked into the game survives VM restarts.
if ! $G compute addresses describe "$ADDRESS" --region="$REGION" >/dev/null 2>&1; then
    echo "== reserving a static external IP"
    $G compute addresses create "$ADDRESS" --region="$REGION"
fi
IP=$($G compute addresses describe "$ADDRESS" --region="$REGION" --format='value(address)')

if ! $G compute firewall-rules describe "$RULE" >/dev/null 2>&1; then
    echo "== opening tcp:80 for instances tagged $TAG"
    $G compute firewall-rules create "$RULE" --network=default --direction=INGRESS \
        --allow=tcp:80 --target-tags="$TAG" --source-ranges=0.0.0.0/0 \
        --description="vn3ds leaderboard (plain HTTP)"
fi

if $G compute instances describe "$VM" --zone="$ZONE" >/dev/null 2>&1; then
    echo "== $VM exists: updating its code and key, then restarting it"
    $G compute instances add-metadata "$VM" --zone="$ZONE" --metadata-from-file="$META_FILES"
    $G compute instances stop "$VM" --zone="$ZONE"
    $G compute instances start "$VM" --zone="$ZONE"
else
    echo "== creating $VM (e2-micro, 10 GB standard disk: inside the free tier)"
    $G compute instances create "$VM" --zone="$ZONE" \
        --machine-type=e2-micro \
        --image-family=debian-12 --image-project=debian-cloud \
        --boot-disk-type=pd-standard --boot-disk-size=10GB \
        --address="$IP" --tags="$TAG" \
        --metadata-from-file="$META_FILES"
fi

echo "== waiting for http://$IP/v1/health"
for _ in $(seq 60); do
    if curl -sf -m 3 "http://$IP/v1/health" >/dev/null; then
        echo
        echo "Leaderboard is up: http://$IP"
        echo "Game setting:  url = http://$IP   (leaderboard.cfg, or LEADERBOARD_URL)"
        exit 0
    fi
    printf .
    sleep 5
done
echo
echo "The VM is at $IP but the server did not answer yet. Check the boot log:"
echo "  gcloud compute instances get-serial-port-output $VM --zone=$ZONE --project=$PROJECT | grep -i startup"
exit 1
