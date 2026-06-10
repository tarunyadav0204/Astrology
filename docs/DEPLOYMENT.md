# GitHub Actions Deployment

## Quick Setup

### 1. Server Setup (Only if needed)
```bash
# If server doesn't have Node.js/Python/repo:
curl -sSL https://raw.githubusercontent.com/tarunyadav0204/Astrology/main/setup-server.sh | bash

# OR manually clone if server is ready:
git clone https://github.com/tarunyadav0204/Astrology.git AstrologyApp
```

### 2. GitHub Secrets (One-time)
1. Go to GitHub repo → Settings → Secrets and variables → Actions
2. Add secrets:
   - `HOST`: Your server IP
   - `USERNAME`: Server username (ubuntu)
   - `SSH_KEY`: Private SSH key content

### 3. Manual Deployment
```bash
# On server
cd AstrologyApp
bash deploy.sh
```

## How It Works

- **Push to main** → GitHub Actions → SSH to server → Auto deployment
- **deploy.sh** pulls latest code, then **restarts the backend only if `backend/` changed** (or the API is unhealthy / first deploy / `FORCE_FULL_DEPLOY`). If the push is **frontend-only** and `/api/health` is OK, the API process is **left running** during `npm run build`. Then the **frontend** static server is restarted when there is a new build.
- **`pip install -r backend/requirements.txt`** runs only when `backend/requirements.txt` changed, on **first deploy** (no previous HEAD), or when **`FORCE_FULL_DEPLOY=true`**. Ordinary backend-only Python changes skip pip to speed deploys.
- **Force pip on a push**: put **`[pip]`**, **`[deps]`**, or **`[full-pip]`** in the commit message (any of these tags).
- **Skip pip when safe**: **`[skip-pip]`** in the commit message is ignored if `requirements.txt` changed or it is the first deploy.
- **Manual deploy**: Actions → **Deploy to GCP** → **Run workflow** → enable **Force backend pip** if you need a fresh venv install without editing `requirements.txt`.
- **systemd service** keeps backend running
- **Logs** in `logs/`: `backend.log` (append), `restart.log`, `crash-snapshots.log` (last 500 lines before watchdog restart), `monitor.log`
- Watchdog probes **`/api/keepalive`** (lightweight); deploy still verifies **`/api/health`** (includes DB)
- **GCE MIG startup** should not use `FORCE_FULL_DEPLOY=true`. For replacement VMs, prefer:
  ```bash
  export SYNC_GCP_SECRETS=true
  export DEFER_FRONTEND_BUILD=true
  bash deploy.sh
  ```
  This brings the backend up quickly for MIG health checks and avoids a full frontend build during instance bootstrap.
- **Preferred MIG startup** is to fetch a prebuilt frontend artifact from GCS and pass it to `deploy.sh` via `FRONTEND_PREBUILT_ARCHIVE`. A repo-owned template lives at [infra/gcp/astroroshni-mig-startup.sh](/Users/tarunydv/Desktop/Code/AstrologyApp/infra/gcp/astroroshni-mig-startup.sh).
- **GitHub Actions** now expects a repository variable named `GCP_FRONTEND_ARTIFACT_BUCKET` and publishes:
  - `gs://$GCP_FRONTEND_ARTIFACT_BUCKET/prod/frontend-build-$GITHUB_SHA.tgz`
  - `gs://$GCP_FRONTEND_ARTIFACT_BUCKET/prod/frontend-build-latest.tgz`
  Replacement VMs should read the `latest` object during startup.

## Services

- **Backend**: Port 8001 (systemd: astrology-app)
- **Frontend**: Port 3001 (served via deploy.sh)

## Commands

```bash
# Check service status
sudo systemctl status astrology-app

# View logs
tail -f logs/backend.log
tail -f logs/frontend.log
tail -f logs/restart.log
tail -f logs/crash-snapshots.log   # captured before each watchdog restart

# Manual restart
sudo systemctl restart astrology-app

# Sentry (optional): add to backend/.env on the server
# SENTRY_DSN=...  SENTRY_ENVIRONMENT=production
# Errors include a host snapshot (RAM/CPU/disk) at event time — not continuous infra metrics.
```
