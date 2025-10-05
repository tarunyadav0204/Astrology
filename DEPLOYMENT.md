# GitHub Actions Deployment

## Quick Setup

### 1. Server Setup (One-time)
```bash
# On your GCP server
curl -sSL https://raw.githubusercontent.com/tarunyadav0204/Astrology/main/setup-server.sh | bash
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
- **deploy.sh** pulls latest code and restarts services
- **systemd service** keeps backend running
- **Logs** stored in `logs/` directory

## Services

- **Backend**: Port 8000 (systemd: astrology-app)
- **Frontend**: Port 3000 (served via deploy.sh)

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