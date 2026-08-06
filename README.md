# WaFT Data Relay — DigitalOcean Setup

Streams Webull market data (quotes + 1-minute bars) to a private GitHub repo every
minute, 24/7. Claude pulls the repo to analyze with near-real-time data.
Your Webull keys live ONLY on the droplet. Claude receives only a read-only GitHub token.

## Step 1 — GitHub (5 minutes, phone or laptop)

1. Create a **private** repo named `waft-data` (github.com → New repository → Private).
2. Create the droplet's write token: Settings → Developer settings → **Fine-grained tokens**
   → Generate new token. Name: `waft-droplet`. Repository access: *Only select repositories*
   → `waft-data`. Permissions: **Contents: Read and write**. Copy the token (`github_pat_...`).
3. Create Claude's read token the same way: name `waft-claude-read`, same single repo,
   Permissions: **Contents: Read-only**. Copy it — this is the ONLY secret you paste to Claude.

## Step 2 — Droplet (15 minutes)

1. DigitalOcean → Create → Droplet: Ubuntu 24.04, **Basic / cheapest ($4-6/mo)**, any region
   (Singapore = lowest latency to both HK and you).
2. Open the droplet console (or ssh in as root).
3. Upload/copy this folder to the droplet (e.g. `scp -r waft-relay root@DROPLET_IP:/root/`
   or just create the files via nano — they're small).
4. Run setup, embedding the write token in the repo URL:
   ```
   bash /root/waft-relay/setup.sh https://github_pat_XXXX@github.com/YOURUSER/waft-data.git
   ```
5. Edit the config and paste your Webull keys (directly from the Webull dashboard):
   ```
   nano /opt/waft/config.env
   ```
6. Test one cycle manually:
   ```
   /opt/waft/venv/bin/python /opt/waft/fetcher.py
   ```
   Success looks like: `2026-...Z ok=8 err=0`. Errors are listed in the output —
   `403` on data calls means the Webull market-data subscription isn't active yet
   (subscribe in the Webull OpenAPI dashboard). Auth failures usually mean a
   mistyped key — re-copy from the dashboard.
7. Done. Cron now pushes every minute. Watch it: `tail -f /var/log/waft.log`

## Step 3 — Tell Claude

Paste to Claude: the repo URL (github.com/YOURUSER/waft-data) and the **read-only**
token from Step 1.3. Claude clones the repo and starts using live data in analyses
and briefs.

## Maintenance

- Stop streaming: `rm /etc/cron.d/waft-relay` · Resume: re-run setup.sh
- Rotate Webull keys: regenerate in Webull dashboard → edit /opt/waft/config.env
- The repo accumulates 1-minute bar history daily — free backtest archive.
- Repo getting large after months: delete old files in `bars/` or squash history.
