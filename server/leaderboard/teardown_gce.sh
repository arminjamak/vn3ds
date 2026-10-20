#!/bin/bash
# Removes everything deploy_gce.sh created: the VM (and its disk, with the
# scores on it), the firewall rule and the static IP. Same settings as
# deploy_gce.sh (PROJECT, ZONE, VM). Pass -y to skip the question.
#
# To keep a copy of the scores, export them first (see README.md, "Admin"):
#   gcloud compute ssh vn3ds-leaderboard --zone=us-central1-a --command \
#     'sudo -u vn3ds python3 /opt/vn3ds-leaderboard/leaderboard.py \
#      --db /var/lib/vn3ds-leaderboard/leaderboard.db --list' > scores.tsv
set -euo pipefail

PROJECT=${PROJECT:-$(gcloud config get-value project 2>/dev/null)}
ZONE=${ZONE:-us-central1-a}
REGION=${ZONE%-*}
VM=${VM:-vn3ds-leaderboard}
RULE=vn3ds-leaderboard-http
ADDRESS=vn3ds-leaderboard-ip

[ -n "$PROJECT" ] || { echo "Set PROJECT (or run: gcloud config set project <id>)"; exit 1; }
if [ "${1:-}" != "-y" ]; then
    printf 'Delete VM %s (and its scores), firewall rule %s and IP %s in project %s? [y/N] ' \
        "$VM" "$RULE" "$ADDRESS" "$PROJECT"
    read -r answer
    [ "$answer" = y ] || [ "$answer" = Y ] || exit 1
fi

G="gcloud --project=$PROJECT --quiet"
if $G compute instances describe "$VM" --zone="$ZONE" >/dev/null 2>&1; then
    $G compute instances delete "$VM" --zone="$ZONE" --delete-disks=all
fi
if $G compute firewall-rules describe "$RULE" >/dev/null 2>&1; then
    $G compute firewall-rules delete "$RULE"
fi
if $G compute addresses describe "$ADDRESS" --region="$REGION" >/dev/null 2>&1; then
    $G compute addresses delete "$ADDRESS" --region="$REGION"
fi
echo "Leaderboard removed."
