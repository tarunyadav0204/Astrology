#!/bin/bash

# Auto-restart script for Astrology API
APP_DIR="/Users/tarunydv/Desktop/Code/AstrologyApp"
HEALTH_URL="http://localhost:8001/docs"
LOG_FILE="$APP_DIR/logs/restart.log"

# Create logs directory if it doesn't exist
mkdir -p $APP_DIR/logs

cd $APP_DIR

while true; do
    # Check if server is responding
    if ! curl -s --max-time 10 $HEALTH_URL > /dev/null 2>&1; then
        echo "$(date): Server down, restarting..." >> $LOG_FILE
        
        # Kill existing processes
        fuser -k 8001/tcp 2>/dev/null || true
        sleep 3
        
        # Start backend using the same method as deploy.sh
        cd backend
        source venv/bin/activate
        nohup python main.py > ../logs/backend.log 2>&1 &
        BACKEND_PID=$!
        
        echo "$(date): Server restarted with PID: $BACKEND_PID" >> $LOG_FILE
        
        # Wait for server to start
        sleep 10
        
        # Test if it's working
        if curl -s --max-time 10 $HEALTH_URL > /dev/null 2>&1; then
            echo "$(date): Server restart successful" >> $LOG_FILE
        else
            echo "$(date): Server restart failed" >> $LOG_FILE
        fi
        
        cd $APP_DIR
    fi
    
    # Check every 30 seconds
    sleep 30
done