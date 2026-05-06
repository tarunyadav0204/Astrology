#!/bin/bash

# Auto-restart script for Astrology API
APP_DIR="$(pwd)"
HEALTH_URL="http://localhost:8001/api/health"
LOG_FILE="$APP_DIR/logs/restart.log"
FAILURE_COUNT=0
FAILURE_THRESHOLD=3
HEALTH_TIMEOUT=15
CHECK_INTERVAL=30
STARTUP_WAIT=20

# Create logs directory if it doesn't exist
mkdir -p $APP_DIR/logs

cd $APP_DIR

while true; do
    # Check if server is responding
    if curl -fsS --max-time $HEALTH_TIMEOUT $HEALTH_URL > /dev/null 2>&1; then
        if [ "$FAILURE_COUNT" -gt 0 ]; then
            echo "$(date): Health check recovered after $FAILURE_COUNT failure(s)" >> $LOG_FILE
        fi
        FAILURE_COUNT=0
        sleep $CHECK_INTERVAL
        continue
    fi

    FAILURE_COUNT=$((FAILURE_COUNT + 1))
    echo "$(date): Health check failed ($FAILURE_COUNT/$FAILURE_THRESHOLD) for $HEALTH_URL" >> $LOG_FILE

    if [ "$FAILURE_COUNT" -lt "$FAILURE_THRESHOLD" ]; then
        sleep $CHECK_INTERVAL
        continue
    fi

    echo "$(date): Server down after $FAILURE_COUNT consecutive failures, restarting..." >> $LOG_FILE
        
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
    sleep $STARTUP_WAIT

    # Test if it's working
    if curl -fsS --max-time $HEALTH_TIMEOUT $HEALTH_URL > /dev/null 2>&1; then
        echo "$(date): Server restart successful" >> $LOG_FILE
        FAILURE_COUNT=0
    else
        echo "$(date): Server restart failed" >> $LOG_FILE
    fi

    cd $APP_DIR
    sleep $CHECK_INTERVAL
done
