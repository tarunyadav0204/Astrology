const express = require('express');
const { exec } = require('child_process');
const crypto = require('crypto');
const fs = require('fs');

const app = express();
const PORT = 9000;
const SECRET = process.env.WEBHOOK_SECRET || 'your-webhook-secret';

app.use(express.json());

// Webhook endpoint for GitHub
app.post('/webhook', (req, res) => {
  const signature = req.headers['x-hub-signature-256'];
  const payload = JSON.stringify(req.body);
  
  // Verify GitHub signature
  const hmac = crypto.createHmac('sha256', SECRET);
  const digest = 'sha256=' + hmac.update(payload).digest('hex');
  
  if (signature !== digest) {
    console.log('❌ Invalid signature');
    return res.status(401).send('Unauthorized');
  }
  
  // Only deploy on push to main branch
  if (req.body.ref === 'refs/heads/main') {
    console.log('🔄 Deploying latest changes...');
    
    exec('bash deploy.sh', (error, stdout, stderr) => {
      if (error) {
        console.error('❌ Deployment failed:', error);
        return res.status(500).send('Deployment failed');
      }
      
      console.log('✅ Deployment successful');
      console.log(stdout);
      res.status(200).send('Deployment successful');
    });
  } else {
    res.status(200).send('No deployment needed');
  }
});

app.listen(PORT, () => {
  console.log(`🎣 Webhook server running on port ${PORT}`);
});