# Domain Setup Guide

## Overview
Your astrology application now supports multi-domain routing:

- **astrovishnu.com** - For software users (professional astrologers)
- **astroroshni.com** - For general users (astrology seekers)
- **astroclick.com** - Legacy domain (fallback)

## How It Works

### 1. Domain Detection
The app automatically detects which domain the user is accessing and shows appropriate content.

### 2. User Type Routing
- **Software Users**: Redirected to astrovishnu.com → Dashboard/Chart Selector
- **General Users**: Redirected to astroroshni.com → AstroRoshni Homepage

### 3. Shared Login
Both domains use the same login screen but route users differently after authentication.

## Setup Steps

### 1. DNS Configuration
Point both domains to your server:
```
astrovishnu.com → Your Server IP
astroroshni.com → Your Server IP
```

### 2. Web Server Configuration (Nginx/Apache)
Configure your web server to serve the same React app for both domains:

```nginx
server {
    listen 80;
    server_name astrovishnu.com astroroshni.com astroclick.com;
    
    location / {
        try_files $uri $uri/ /index.html;
        root /path/to/your/react/build;
    }
    
    location /api {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. User Type Management
To mark users as software users, update their user_type in the database:

```sql
UPDATE users SET user_type = 'software' WHERE phone = 'user_phone_number';
```

### 4. Testing
1. Access astrovishnu.com - should show software-focused landing page
2. Access astroroshni.com - should show general user landing page
3. Login as software user on astroroshni.com - should redirect to astrovishnu.com
4. Login as general user on astrovishnu.com - should redirect to astroroshni.com

## Features Implemented

### Frontend Changes
- ✅ Domain configuration system
- ✅ AstroRoshni homepage for general users
- ✅ Domain-specific landing page content
- ✅ Automatic user redirection after login
- ✅ Shared authentication system

### Backend Changes
- ✅ Added user_type field to users table
- ✅ Updated login/register endpoints to include user_type
- ✅ Database migration for existing users

## User Experience Flow

### For Software Users (astrovishnu.com)
1. Visit astrovishnu.com
2. See "Professional Vedic astrology software" messaging
3. Login → Dashboard with full chart features
4. If accessing astroroshni.com, automatically redirected to astrovishnu.com

### For General Users (astroroshni.com)
1. Visit astroroshni.com
2. See "Get personalized astrology readings" messaging
3. Login → AstroRoshni homepage with services
4. If accessing astrovishnu.com, automatically redirected to astroroshni.com

## Next Steps
1. Deploy the updated code
2. Configure DNS for both domains
3. Set up web server configuration
4. Mark existing software users in database
5. Test the complete flow

## Database Migration
Run this SQL to add user_type column to existing database:
```sql
ALTER TABLE users ADD COLUMN user_type TEXT DEFAULT 'general';
```

## Customization
- Edit `domains.config.js` to modify domain settings
- Update `AstroRoshniHomepage.js` to customize the general user experience
- Modify landing page content in `LandingPage.js` for domain-specific messaging