#!/bin/bash
# GCE startup script (runs as root on every boot of the leaderboard VM).
# Installs leaderboard.py and the shared key from the instance metadata that
# deploy_gce.sh set, and runs the server as a systemd service on port 80.
set -euo pipefail

MD=http://metadata.google.internal/computeMetadata/v1/instance/attributes
get() { curl -sf -H 'Metadata-Flavor: Google' "$MD/$1"; }

command -v python3 >/dev/null || { apt-get update && apt-get install -y python3; }

id vn3ds >/dev/null 2>&1 || useradd --system --home-dir /var/lib/vn3ds-leaderboard \
    --no-create-home --shell /usr/sbin/nologin vn3ds
install -d -m 755 /opt/vn3ds-leaderboard
get leaderboard-py > /opt/vn3ds-leaderboard/leaderboard.py.new
mv /opt/vn3ds-leaderboard/leaderboard.py.new /opt/vn3ds-leaderboard/leaderboard.py

install -d -m 700 /etc/vn3ds-leaderboard
(umask 077 && get leaderboard-key > /etc/vn3ds-leaderboard/key)

cat > /etc/systemd/system/vn3ds-leaderboard.service <<'EOF'
[Unit]
Description=vn3ds minigame leaderboard
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=/usr/bin/python3 /opt/vn3ds-leaderboard/leaderboard.py --host 0.0.0.0 --port 80 --db /var/lib/vn3ds-leaderboard/leaderboard.db
# the key is handed over as a credential: $CREDENTIALS_DIRECTORY/key
LoadCredential=key:/etc/vn3ds-leaderboard/key
User=vn3ds
Group=vn3ds
StateDirectory=vn3ds-leaderboard
StateDirectoryMode=0700
AmbientCapabilities=CAP_NET_BIND_SERVICE
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
MemoryMax=256M
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable vn3ds-leaderboard
systemctl restart vn3ds-leaderboard
