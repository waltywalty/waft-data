#!/usr/bin/env bash
# WaFT relay — one-time droplet setup. Run as root on a fresh Ubuntu 22.04/24.04 droplet:
#   bash setup.sh https://github.com/YOURUSER/waft-data.git
set -euo pipefail

REPO_URL="${1:?Usage: bash setup.sh <github-repo-url-with-token>}"

apt-get update -y && apt-get install -y python3-venv python3-pip git

BASE=/opt/waft
mkdir -p "$BASE"
cp -r "$(dirname "$0")"/* "$BASE"/ 2>/dev/null || true
cd "$BASE"

# Python env + Webull SDK (pin setuptools to dodge the paho-mqtt build bug)
python3 -m venv venv
./venv/bin/pip install --quiet "setuptools<66" wheel
./venv/bin/pip install --quiet webull-openapi-python-sdk

# Data repo checkout (the token-embedded URL authenticates pushes)
if [ ! -d "$BASE/data/.git" ]; then
  git clone "$REPO_URL" "$BASE/data"
  cd "$BASE/data"
  git config user.email "waft-relay@local" && git config user.name "WaFT Relay"
  # ensure main branch exists
  git checkout -B main
  mkdir -p latest bars meta
  echo "WaFT data relay" > README.md
  git add -A && git commit -m "init" && git push -u origin main || true
  cd "$BASE"
fi

if [ ! -f "$BASE/config.env" ]; then
  cp "$BASE/config.env.example" "$BASE/config.env"
  echo ">>> EDIT $BASE/config.env with your Webull keys, then run:"
  echo ">>>   $BASE/venv/bin/python $BASE/fetcher.py    # test once"
fi

# Cron: every minute, flock prevents overlap
cat > /etc/cron.d/waft-relay << 'CRON'
* * * * * root flock -n /tmp/waft.lock /opt/waft/venv/bin/python /opt/waft/fetcher.py >> /var/log/waft.log 2>&1
CRON
chmod 644 /etc/cron.d/waft-relay

echo "Setup complete. Edit /opt/waft/config.env, test with:"
echo "  /opt/waft/venv/bin/python /opt/waft/fetcher.py"
echo "Then the cron job streams every minute automatically. Log: /var/log/waft.log"
