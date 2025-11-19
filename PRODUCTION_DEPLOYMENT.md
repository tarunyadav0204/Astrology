# Production Deployment Guide

## Pre-Deployment Security Checklist

### 1. JWT Secret Configuration ✅ CRITICAL
- [x] Remove hardcoded JWT secret from code
- [ ] Set `JWT_SECRET` environment variable on production server
- [ ] Verify secret is cryptographically secure (32+ characters)
- [ ] Test JWT functionality with new secret

### 2. Environment Variables Setup

**Required Environment Variables:**
```bash
JWT_SECRET=629b255507125eaf87d6822a6b18548d90f90a7dd92510fa260233393e6a11a6
```

**Optional Environment Variables:**
```bash
ENVIRONMENT=production
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=your_twilio_phone
GEMINI_API_KEY=your_gemini_api_key
```

### 3. Platform-Specific Setup

#### AWS EC2/ECS
```bash
# Set environment variable
export JWT_SECRET="629b255507125eaf87d6822a6b18548d90f90a7dd92510fa260233393e6a11a6"

# Or use AWS Systems Manager Parameter Store
aws ssm put-parameter \
  --name "/astrology-app/jwt-secret" \
  --value "629b255507125eaf87d6822a6b18548d90f90a7dd92510fa260233393e6a11a6" \
  --type "SecureString"
```

#### Heroku
```bash
heroku config:set JWT_SECRET=629b255507125eaf87d6822a6b18548d90f90a7dd92510fa260233393e6a11a6
```

#### DigitalOcean App Platform
1. Go to App Settings → Environment Variables
2. Add: `JWT_SECRET` = `629b255507125eaf87d6822a6b18548d90f90a7dd92510fa260233393e6a11a6`

#### Docker/Docker Compose
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    environment:
      - JWT_SECRET=629b255507125eaf87d6822a6b18548d90f90a7dd92510fa260233393e6a11a6
    ports:
      - "8001:8001"
```

#### Google Cloud Platform
```bash
# Using Secret Manager
gcloud secrets create jwt-secret \
  --data-file=- <<< "629b255507125eaf87d6822a6b18548d90f90a7dd92510fa260233393e6a11a6"
```

### 4. Verification Steps

1. **Run verification script:**
   ```bash
   cd backend
   python verify_production.py
   ```

2. **Test API endpoints:**
   ```bash
   # Test health endpoint
   curl https://your-domain.com/api/health
   
   # Test login (should work with new JWT secret)
   curl -X POST https://your-domain.com/api/login \
     -H "Content-Type: application/json" \
     -d '{"phone":"your_phone","password":"your_password"}'
   ```

3. **Check logs for JWT errors:**
   ```bash
   # Look for JWT-related errors
   tail -f /var/log/your-app.log | grep -i jwt
   ```

### 5. Security Best Practices

- ✅ JWT secret is cryptographically secure (64 hex characters)
- ✅ JWT secret is stored as environment variable, not in code
- ✅ `.env` file is in `.gitignore`
- [ ] HTTPS is enabled in production
- [ ] Database credentials are secured
- [ ] API rate limiting is configured
- [ ] CORS is properly configured for production domains

### 6. Rollback Plan

If JWT issues occur in production:

1. **Immediate fix:** Set environment variable directly
   ```bash
   export JWT_SECRET="629b255507125eaf87d6822a6b18548d90f90a7dd92510fa260233393e6a11a6"
   systemctl restart your-app-service
   ```

2. **Verify fix:**
   ```bash
   python verify_production.py
   ```

3. **If still failing:** Check application logs
   ```bash
   journalctl -u your-app-service -f
   ```

### 7. Post-Deployment Testing

- [ ] User registration works
- [ ] User login works  
- [ ] JWT tokens are properly generated
- [ ] Protected endpoints require authentication
- [ ] Admin endpoints require admin role
- [ ] Password reset functionality works

### 8. Monitoring

Set up monitoring for:
- JWT token validation errors
- Authentication failures
- Environment variable loading issues
- Application startup errors

## Emergency Contacts

- **Security Issue:** Immediately rotate JWT secret
- **Authentication Down:** Check environment variables first
- **Database Issues:** Verify connection strings and credentials

---

**⚠️ CRITICAL:** Never commit JWT secrets to version control. Always use environment variables in production.