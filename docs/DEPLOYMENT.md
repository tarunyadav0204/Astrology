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
- **Logs** stored in `logs/` directory

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

# Manual restart
sudo systemctl restart astrology-app
```