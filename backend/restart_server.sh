#!/bin/bash

# Auto-restart script for Astrology API
SERVER_DIR="/Users/tarunydv/Desktop/Code/AstrologyApp/backend"
HEALTH_URL="http://localhost:8001/docs"
LOG_FILE="$SERVER_DIR/restart.log"

cd $SERVER_DIR

while true; do
    # Check if server is responding
    if ! curl -s --max-time 10 $HEALTH_URL > /dev/null 2>&1; then
        echo "$(date): Server down, restarting..." >> $LOG_FILE
        
        # Kill existing process
        pkill -f "python main.py"
        sleep 2
        
        # Start server
        nohup python main.py > server.log 2>&1 &
        echo "$(date): Server restarted" >> $LOG_FILE
        
        # Wait for server to start
        sleep 10
    fi
    
    # Check every 30 seconds
    sleep 30
done