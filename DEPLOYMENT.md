# Automated Git Deployment

## Quick Setup

### 1. Server Setup (One-time)
```bash
# On your GCP server
curl -sSL https://raw.githubusercontent.com/tarunyadav0204/Astrology/main/setup-server.sh | bash
```

### 2. GitHub Webhook (One-time)
1. Go to your GitHub repository settings
2. Add webhook: `http://your-server-ip:9000/webhook`
3. Set secret: `your-webhook-secret`
4. Select "Push events"

### 3. Manual Deployment
```bash
# On server
cd AstrologyApp
bash deploy.sh
```

## How It Works

- **Push to main** → GitHub webhook → Auto deployment
- **deploy.sh** pulls latest code and restarts services
- **systemd services** keep apps running
- **Logs** stored in `logs/` directory

## Services

- **Backend**: Port 8000 (systemd: astrology-app)
- **Frontend**: Port 3000 (served via deploy.sh)
- **Webhook**: Port 9000 (systemd: astrology-webhook)

## Commands

```bash
# Check service status
sudo systemctl status astrology-app
sudo systemctl status astrology-webhook

# View logs
tail -f logs/backend.log
tail -f logs/frontend.log

# Manual restart
sudo systemctl restart astrology-app
```