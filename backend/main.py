from fastapi import FastAPI, Depends, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import swisseph as swe
import sqlite3
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import bcrypt
import jwt
from horoscope.api import HoroscopeAPI
from rule_engine.api import router as rule_engine_router
from user_settings import router as settings_router
from daily_predictions import DailyPredictionEngine
from house_combinations import router as house_combinations_router
try:
    from house_combinations import init_house_combinations_db
except ImportError:
    def init_house_combinations_db():
        print("House combinations database initialization skipped")
        pass
from marriage_analysis.marriage_analyzer import MarriageAnalyzer
from nadi.services.nadi_service import router as nadi_router
from vedic_transit_aspects import router as vedic_transit_router
from vedic_predictions.api.prediction_endpoint import router as vedic_predictions_router
from vedic_predictions.api.badhaka_maraka_endpoint import router as badhaka_maraka_router
from planetary_dignities import router as planetary_dignities_router
from chara_karakas import router as chara_karakas_router
from shadbala import router as shadbala_router
from classical_shadbala import router as classical_shadbala_router
from auth import get_current_user as auth_get_current_user
from app.kp.routes.kp_routes import router as kp_router
from career_analysis.career_router import router as career_router
from panchang.panchang_routes import router as panchang_router
from panchang.muhurat_routes import router as muhurat_router
from health.health_routes import router as health_router
import math
from datetime import timedelta


# Load environment variables explicitly
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Loaded environment variables from .env file")
except ImportError:
    print("python-dotenv not installed, using system environment variables")
except Exception as e:
    print(f"Warning loading environment variables: {e}")
    pass

app = FastAPI()
horoscope_api = HoroscopeAPI()

# Configure timeout for long-running requests (Gemini AI takes 30-60 seconds)
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class TimeoutMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Set longer timeout for AI endpoints
        if "/ai-insights" in str(request.url):
            # No timeout for AI endpoints - let them complete
            response = await call_next(request)
        else:
            # Normal timeout for other endpoints
            response = await call_next(request)
        return response

app.add_middleware(TimeoutMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include rule engine router with /api prefix
app.include_router(rule_engine_router, prefix="/api")
app.include_router(settings_router, prefix="/api")
app.include_router(house_combinations_router, prefix="/api")
app.include_router(nadi_router, prefix="/api")
app.include_router(vedic_transit_router, prefix="/api")
app.include_router(vedic_predictions_router)
app.include_router(badhaka_maraka_router, prefix="/api")
app.include_router(planetary_dignities_router, prefix="/api")
app.include_router(chara_karakas_router, prefix="/api")
app.include_router(shadbala_router, prefix="/api")
app.include_router(classical_shadbala_router, prefix="/api")
app.include_router(kp_router, prefix="/api")
app.include_router(career_router, prefix="/api")
app.include_router(panchang_router, prefix="/api")
app.include_router(muhurat_router, prefix="/api")
app.include_router(health_router, prefix="/api")


# Root endpoint for health check
@app.get("/")
async def root():
    return {"message": "Astrology API", "docs": "/api/docs", "version": "1.0.0"}

@app.get("/api/test")
async def test_endpoint():
    return {"status": "ok", "message": "API is working", "timestamp": datetime.now().isoformat()}

# Health check endpoint for load balancer
@app.get("/docs")
async def health_docs():
    return {"status": "healthy", "message": "Astrology API is running"}

@app.get("/api/status")
async def api_status():
    return {
        "api_status": "running",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "endpoints": ["/api/login", "/api/register", "/api/health"]
    }

class BirthData(BaseModel):
    name: str
    date: str
    time: str
    latitude: float
    longitude: float
    timezone: str
    place: str = ""
    gender: str = ""

class TransitRequest(BaseModel):
    birth_data: BirthData
    transit_date: str

class UserCreate(BaseModel):
    name: str
    phone: str
    password: str
    role: str = "user"

class UserLogin(BaseModel):
    phone: str
    password: str

class ForgotPassword(BaseModel):
    phone: str

class ResetPassword(BaseModel):
    phone: str
    new_password: str

class SendResetCode(BaseModel):
    phone: str

class VerifyResetCode(BaseModel):
    phone: str
    code: str

class ResetPasswordWithToken(BaseModel):
    token: str
    new_password: str

class MarriageAnalysisRequest(BaseModel):
    chart_data: dict
    birth_details: dict
    analysis_type: str = "single"

class CompatibilityRequest(BaseModel):
    boy_birth_data: BirthData
    girl_birth_data: BirthData

class DailyPredictionRequest(BaseModel):
    birth_data: BirthData
    target_date: Optional[str] = None

class ClassicalPredictionRequest(BaseModel):
    birth_data: BirthData
    prediction_date: Optional[str] = None

class User(BaseModel):
    userid: int
    name: str
    phone: str
    role: str

# Lahiri Ayanamsa
swe.set_sid_mode(swe.SIDM_LAHIRI)

# JWT Configuration
SECRET_KEY = "astrology-app-secret-key-2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours
security = HTTPBearer()

# Initialize SQLite database
def init_db():
    try:
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        
        # Create users table (simplified)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                userid INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create subscription plans table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscription_plans (
                plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                plan_name TEXT NOT NULL,
                price DECIMAL(10,2) DEFAULT 0.00,
                duration_months INTEGER DEFAULT 1,
                features TEXT NOT NULL,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create user subscriptions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                userid INTEGER NOT NULL,
                plan_id INTEGER NOT NULL,
                status TEXT DEFAULT 'active',
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (userid) REFERENCES users (userid),
                FOREIGN KEY (plan_id) REFERENCES subscription_plans (plan_id)
            )
        ''')
        
        # Insert default subscription plans
        cursor.execute("SELECT COUNT(*) FROM subscription_plans")
        if cursor.fetchone()[0] == 0:
            default_plans = [
                ('astrovishnu', 'Free', 0.00, 12, '{"charts": true, "basic_features": true}'),
                ('astrovishnu', 'Premium', 99.99, 12, '{"charts": true, "predictions": true, "api_access": true, "advanced_features": true}'),
                ('astroroshni', 'Free', 0.00, 12, '{"consultations": 1, "basic_reports": true}'),
                ('astroroshni', 'Basic', 29.99, 1, '{"consultations": 3, "reports": true, "priority_support": false}'),
                ('astroroshni', 'Premium', 99.99, 12, '{"consultations": 10, "reports": true, "priority_support": true, "custom_remedies": true}')
            ]
            
            for platform, plan_name, price, duration, features in default_plans:
                cursor.execute('''
                    INSERT INTO subscription_plans (platform, plan_name, price, duration_months, features)
                    VALUES (?, ?, ?, ?, ?)
                ''', (platform, plan_name, price, duration, features))
        
        # Check if birth_charts table exists and has userid column
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='birth_charts'")
        result = cursor.fetchone()
        
        if result and 'userid' not in result[0]:
            # Drop existing table and recreate with userid column
            cursor.execute('DROP TABLE birth_charts')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS birth_charts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                userid INTEGER NOT NULL,
                name TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                timezone TEXT NOT NULL,
                place TEXT DEFAULT '',
                gender TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (userid) REFERENCES users (userid),
                UNIQUE(userid, date, time, latitude, longitude)
            )
        ''')
        
        # Add place column if it doesn't exist
        try:
            cursor.execute('ALTER TABLE birth_charts ADD COLUMN place TEXT DEFAULT ""')
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Add gender column if it doesn't exist
        try:
            cursor.execute('ALTER TABLE birth_charts ADD COLUMN gender TEXT DEFAULT ""')
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Create planet nakshatra interpretations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS planet_nakshatra_interpretations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                planet TEXT NOT NULL,
                nakshatra TEXT NOT NULL,
                house INTEGER NOT NULL,
                interpretation TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(planet, nakshatra, house)
            )
        ''')
        
        # Create nakshatras table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS nakshatras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                lord TEXT NOT NULL,
                deity TEXT NOT NULL,
                nature TEXT NOT NULL,
                guna TEXT NOT NULL,
                description TEXT NOT NULL,
                characteristics TEXT NOT NULL,
                positive_traits TEXT NOT NULL,
                negative_traits TEXT NOT NULL,
                careers TEXT NOT NULL,
                compatibility TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create password reset codes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS password_reset_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT NOT NULL,
                code TEXT NOT NULL,
                token TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                used BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database initialization error: {str(e)}")
        # Create a minimal database if initialization fails
        try:
            conn = sqlite3.connect('astrology.db')
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    userid INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            conn.close()
            print("Minimal database created")
        except Exception as e2:
            print(f"Failed to create minimal database: {str(e2)}")

try:
    init_db()
    print("Database initialized successfully")
except Exception as e:
    print(f"Database initialization failed: {str(e)}")

# Authentication functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Use the auth module function
get_current_user = auth_get_current_user

# Helper function to check user access
def has_platform_access(userid: int, platform: str, feature: str = None) -> bool:
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT sp.features
        FROM user_subscriptions us
        JOIN subscription_plans sp ON us.plan_id = sp.plan_id
        WHERE us.userid = ? AND sp.platform = ? AND us.status = 'active' 
              AND us.end_date >= date('now')
    ''', (userid, platform))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return False
    
    if feature:
        features = json.loads(result[0])
        return features.get(feature, False)
    
    return True

@app.post("/api/register")
async def register(user_data: UserCreate):
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT phone FROM users WHERE phone = ?", (user_data.phone,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Phone number already registered")
    
    hashed_password = hash_password(user_data.password)
    cursor.execute(
        "INSERT INTO users (name, phone, password, role) VALUES (?, ?, ?, ?)",
        (user_data.name, user_data.phone, hashed_password, user_data.role)
    )
    conn.commit()
    
    cursor.execute("SELECT userid, name, phone, role FROM users WHERE phone = ?", (user_data.phone,))
    user = cursor.fetchone()
    
    # Get free plans for both platforms
    cursor.execute("SELECT plan_id FROM subscription_plans WHERE plan_name = 'Free' AND platform = 'astrovishnu'")
    astrovishnu_free = cursor.fetchone()
    cursor.execute("SELECT plan_id FROM subscription_plans WHERE plan_name = 'Free' AND platform = 'astroroshni'")
    astroroshni_free = cursor.fetchone()
    
    # Give user free access to both platforms
    from datetime import date, timedelta
    start_date = date.today()
    end_date = start_date + timedelta(days=365)  # 1 year free
    
    if astrovishnu_free:
        cursor.execute(
            "INSERT INTO user_subscriptions (userid, plan_id, start_date, end_date) VALUES (?, ?, ?, ?)",
            (user[0], astrovishnu_free[0], start_date, end_date)
        )
    
    if astroroshni_free:
        cursor.execute(
            "INSERT INTO user_subscriptions (userid, plan_id, start_date, end_date) VALUES (?, ?, ?, ?)",
            (user[0], astroroshni_free[0], start_date, end_date)
        )
    
    conn.commit()
    conn.close()
    
    access_token = create_access_token(data={"sub": user_data.phone})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "userid": user[0], 
            "name": user[1], 
            "phone": user[2], 
            "role": user[3]
        }
    }

@app.post("/api/login")
async def login(user_data: UserLogin):
    try:
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        cursor.execute("SELECT userid, name, phone, password, role FROM users WHERE phone = ?", (user_data.phone,))
        user = cursor.fetchone()
        
        if not user or not verify_password(user_data.password, user[3]):
            conn.close()
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Get user's active subscriptions
        cursor.execute('''
            SELECT sp.platform, sp.plan_name, sp.features, us.status, us.end_date
            FROM user_subscriptions us
            JOIN subscription_plans sp ON us.plan_id = sp.plan_id
            WHERE us.userid = ? AND us.status = 'active' AND us.end_date >= date('now')
        ''', (user[0],))
        
        subscriptions = cursor.fetchall()
        conn.close()
        
        # Format subscriptions
        user_subscriptions = {}
        for sub in subscriptions:
            platform, plan_name, features, status, end_date = sub
            try:
                user_subscriptions[platform] = {
                    'plan_name': plan_name,
                    'features': json.loads(features) if features else {},
                    'status': status,
                    'end_date': end_date
                }
            except json.JSONDecodeError:
                user_subscriptions[platform] = {
                    'plan_name': plan_name,
                    'features': {},
                    'status': status,
                    'end_date': end_date
                }
        
        access_token = create_access_token(data={"sub": user_data.phone})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "userid": user[0], 
                "name": user[1], 
                "phone": user[2], 
                "role": user[4],
                "subscriptions": user_subscriptions
            }
        }
    except Exception as e:
        print(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.get("/api/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# Subscription Management APIs
@app.get("/api/subscription-plans")
async def get_subscription_plans(platform: str = None):
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    if platform:
        cursor.execute("SELECT * FROM subscription_plans WHERE platform = ? AND is_active = 1", (platform,))
    else:
        cursor.execute("SELECT * FROM subscription_plans WHERE is_active = 1")
    
    plans = cursor.fetchall()
    conn.close()
    
    result = []
    for plan in plans:
        result.append({
            'plan_id': plan[0],
            'platform': plan[1],
            'plan_name': plan[2],
            'price': plan[3],
            'duration_months': plan[4],
            'features': json.loads(plan[5]),
            'is_active': plan[6]
        })
    
    return {'plans': result}

@app.get("/api/user-subscriptions")
async def get_user_subscriptions(current_user: User = Depends(get_current_user)):
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT us.subscription_id, sp.platform, sp.plan_name, sp.features, us.status, 
               us.start_date, us.end_date, sp.price
        FROM user_subscriptions us
        JOIN subscription_plans sp ON us.plan_id = sp.plan_id
        WHERE us.userid = ?
        ORDER BY us.created_at DESC
    ''', (current_user.userid,))
    
    subscriptions = cursor.fetchall()
    conn.close()
    
    result = []
    for sub in subscriptions:
        result.append({
            'id': sub[0],
            'platform': sub[1],
            'plan_name': sub[2],
            'features': json.loads(sub[3]),
            'status': sub[4],
            'start_date': sub[5],
            'end_date': sub[6],
            'price': sub[7]
        })
    
    return {'subscriptions': result}

@app.post("/api/check-access")
async def check_access(request: dict, current_user: User = Depends(get_current_user)):
    platform = request.get('platform')
    feature = request.get('feature')
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT sp.features
        FROM user_subscriptions us
        JOIN subscription_plans sp ON us.plan_id = sp.plan_id
        WHERE us.userid = ? AND sp.platform = ? AND us.status = 'active' 
              AND us.end_date >= date('now')
    ''', (current_user.userid, platform))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return {'has_access': False, 'reason': 'No active subscription'}
    
    features = json.loads(result[0])
    has_access = features.get(feature, False)
    
    return {
        'has_access': has_access,
        'features': features,
        'reason': 'Feature not included in plan' if not has_access else None
    }

@app.post("/api/forgot-password")
async def forgot_password(request: ForgotPassword):
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    cursor.execute("SELECT userid, name FROM users WHERE phone = ?", (request.phone,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=404, detail="Phone number not found")
    
    return {"message": "Password reset available", "user_name": user[1]}

@app.post("/api/send-reset-code")
async def send_reset_code(request: SendResetCode):
    import random
    import secrets
    from datetime import datetime, timedelta
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    cursor.execute("SELECT userid, name FROM users WHERE phone = ?", (request.phone,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="Phone number not found")
    
    # Generate 6-digit code and secure token
    code = str(random.randint(100000, 999999))
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(minutes=10)  # 10 minute expiry
    
    # Store reset code
    cursor.execute(
        "INSERT INTO password_reset_codes (phone, code, token, expires_at) VALUES (?, ?, ?, ?)",
        (request.phone, code, token, expires_at)
    )
    conn.commit()
    conn.close()
    
    # Debug: Print environment variables
    print(f"Twilio SID: {os.getenv('TWILIO_ACCOUNT_SID')[:10] if os.getenv('TWILIO_ACCOUNT_SID') else 'None'}...")
    print(f"Twilio Token: {os.getenv('TWILIO_AUTH_TOKEN')[:10] if os.getenv('TWILIO_AUTH_TOKEN') else 'None'}...")
    print(f"Twilio Phone: {os.getenv('TWILIO_PHONE_NUMBER')}")
    
    # Send SMS with code
    from sms_service import sms_service
    sms_sent = sms_service.send_reset_code(request.phone, code)
    
    response_data = {
        "message": f"Reset code sent to {request.phone}",
        "user_name": user[1]
    }
    
    # Include code in response only if SMS failed (for testing)
    if not sms_sent:
        response_data["code"] = code
        response_data["message"] += " (SMS service unavailable - code shown for testing)"
    
    return response_data

@app.post("/api/verify-reset-code")
async def verify_reset_code(request: VerifyResetCode):
    from datetime import datetime
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT token FROM password_reset_codes WHERE phone = ? AND code = ? AND expires_at > ? AND used = FALSE",
        (request.phone, request.code, datetime.utcnow())
    )
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    
    token = result[0]
    conn.close()
    
    return {"message": "Code verified", "reset_token": token}

@app.post("/api/reset-password-with-token")
async def reset_password_with_token(request: ResetPasswordWithToken):
    from datetime import datetime
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    # Verify token is valid and not used
    cursor.execute(
        "SELECT phone FROM password_reset_codes WHERE token = ? AND expires_at > ? AND used = FALSE",
        (request.token, datetime.utcnow())
    )
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    phone = result[0]
    
    # Update password
    hashed_password = hash_password(request.new_password)
    cursor.execute("UPDATE users SET password = ? WHERE phone = ?", (hashed_password, phone))
    
    # Mark token as used
    cursor.execute("UPDATE password_reset_codes SET used = TRUE WHERE token = ?", (request.token,))
    
    conn.commit()
    conn.close()
    
    return {"message": "Password reset successfully"}

@app.post("/api/reset-password")
async def reset_password(request: ResetPassword):
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT userid FROM users WHERE phone = ?", (request.phone,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="Phone number not found")
    
    hashed_password = hash_password(request.new_password)
    cursor.execute("UPDATE users SET password = ? WHERE phone = ?", (hashed_password, request.phone))
    conn.commit()
    conn.close()
    
    return {"message": "Password reset successfully"}

@app.get("/api/health")
async def api_health():
    try:
        # Test database connection
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        conn.close()
        return {"status": "healthy", "message": "Astrology API is running", "users": user_count}
    except Exception as e:
        return {"status": "unhealthy", "message": f"Database error: {str(e)}"}

@app.post("/api/calculate-chart")
async def calculate_chart(birth_data: BirthData, node_type: str = 'mean', current_user: User = Depends(get_current_user)):
    # Store birth data in database (update if exists)
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO birth_charts (userid, name, date, time, latitude, longitude, timezone, place, gender)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (current_user.userid, birth_data.name, birth_data.date, birth_data.time, 
          birth_data.latitude, birth_data.longitude, birth_data.timezone, birth_data.place, birth_data.gender))
    conn.commit()
    conn.close()
    
    # Calculate Julian Day with proper timezone handling
    time_parts = birth_data.time.split(':')
    hour = float(time_parts[0]) + float(time_parts[1])/60
    
    # Auto-detect IST for Indian coordinates, otherwise parse timezone
    if 6.0 <= birth_data.latitude <= 37.0 and 68.0 <= birth_data.longitude <= 97.0:
        # Indian coordinates - use IST (UTC+5:30)
        tz_offset = 5.5
    else:
        # Parse timezone offset (e.g., "UTC+5:30" -> 5.5)
        tz_offset = 0
        if birth_data.timezone.startswith('UTC'):
            tz_str = birth_data.timezone[3:]  # Remove 'UTC'
            if tz_str:
                if ':' in tz_str:
                    # Handle UTC+5:30 format
                    sign = 1 if tz_str[0] == '+' else -1
                    parts = tz_str[1:].split(':')
                    tz_offset = sign * (float(parts[0]) + float(parts[1])/60)
                else:
                    tz_offset = float(tz_str)
    
    # Convert local time to UTC
    utc_hour = hour - tz_offset
    
    jd = swe.julday(
        int(birth_data.date.split('-')[0]),
        int(birth_data.date.split('-')[1]),
        int(birth_data.date.split('-')[2]),
        utc_hour
    )
    
    # Calculate planetary positions
    planets = {}
    planet_names = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
    
    for i, planet in enumerate([0, 1, 4, 2, 5, 3, 6, 11, 12]):  # Swiss Ephemeris planet numbers
        if planet <= 6:  # Regular planets
            # Try with speed flag to get accurate velocity data
            pos = swe.calc_ut(jd, planet, swe.FLG_SIDEREAL | swe.FLG_SPEED)
        else:  # Lunar nodes
            node_flag = swe.TRUE_NODE if node_type == 'true' else swe.MEAN_NODE
            pos = swe.calc_ut(jd, node_flag, swe.FLG_SIDEREAL | swe.FLG_SPEED)
        
        # pos is a tuple: (position_array, return_flag)
        pos_array = pos[0]
        longitude = pos_array[0]
        
        # Speed is at index 3 (daily motion in longitude)
        speed = pos_array[3] if len(pos_array) > 3 else 0.0
        
        if planet == 12:  # Ketu - add 180 degrees to Rahu
            longitude = (longitude + 180) % 360
        
        is_retrograde = speed < 0 if planet <= 6 else False
        
        planets[planet_names[i]] = {
            'longitude': longitude,
            'sign': int(longitude / 30),
            'degree': longitude % 30,
            'retrograde': is_retrograde
        }

    # Calculate ascendant and houses
    houses_data = swe.houses(jd, birth_data.latitude, birth_data.longitude, b'P')
    ayanamsa = swe.get_ayanamsa_ut(jd)
    
    # Get sidereal ascendant (houses_data[1][0] is the ascendant)
    ascendant_tropical = houses_data[1][0]  # Tropical ascendant
    ascendant_sidereal = (ascendant_tropical - ayanamsa) % 360
    
    # For Vedic astrology, use Whole Sign houses based on sidereal ascendant
    ascendant_sign = int(ascendant_sidereal / 30)
    houses = []
    for i in range(12):
        house_sign = (ascendant_sign + i) % 12
        house_longitude = (house_sign * 30) + (ascendant_sidereal % 30)
        houses.append({
            'longitude': house_longitude % 360,
            'sign': house_sign
        })
    
    # Calculate Gulika and Mandi using proper Vedic method
    # Get day of week (0=Sunday, 1=Monday, etc.)
    weekday = int((jd + 1.5) % 7)
    
    # Gulika calculation - Saturn's portion during day
    # Saturn's portion for each weekday (in hours from sunrise)
    gulika_portions = [10.5, 1.5, 3.0, 4.5, 6.0, 7.5, 9.0]  # Sun-Sat
    gulika_time = gulika_portions[weekday]
    
    # Calculate Gulika longitude based on time from sunrise
    # Each hour = 15 degrees (360/24)
    gulika_longitude = (gulika_time * 15) % 360
    
    # Mandi calculation - Mars' portion during day (different from Gulika)
    # Mars portions for each weekday (in hours from sunrise)
    mandi_portions = [7.5, 15.0, 22.5, 6.0, 13.5, 21.0, 4.5]  # Sun-Sat
    mandi_time = mandi_portions[weekday]
    
    # Calculate Mandi longitude
    mandi_longitude = (mandi_time * 15) % 360
    
    # Apply ayanamsa correction
    gulika_longitude = (gulika_longitude - ayanamsa) % 360
    mandi_longitude = (mandi_longitude - ayanamsa) % 360
    
    # Ensure positive longitudes
    if gulika_longitude < 0:
        gulika_longitude += 360
    if mandi_longitude < 0:
        mandi_longitude += 360
    
    # Add Gulika and Mandi to planets with house positions
    gulika_house = 1
    for house_num in range(12):
        house_start = houses[house_num]['longitude']
        house_end = (house_start + 30) % 360
        if house_start <= house_end:
            if house_start <= gulika_longitude < house_end:
                gulika_house = house_num + 1
                break
        else:
            if gulika_longitude >= house_start or gulika_longitude < house_end:
                gulika_house = house_num + 1
                break
    
    mandi_house = 1
    for house_num in range(12):
        house_start = houses[house_num]['longitude']
        house_end = (house_start + 30) % 360
        if house_start <= house_end:
            if house_start <= mandi_longitude < house_end:
                mandi_house = house_num + 1
                break
        else:
            if mandi_longitude >= house_start or mandi_longitude < house_end:
                mandi_house = house_num + 1
                break
    
    planets['Gulika'] = {
        'longitude': gulika_longitude,
        'sign': int(gulika_longitude / 30),
        'degree': gulika_longitude % 30,
        'house': gulika_house
    }
    
    planets['Mandi'] = {
        'longitude': mandi_longitude,
        'sign': int(mandi_longitude / 30),
        'degree': mandi_longitude % 30,
        'house': mandi_house
    }
    
    # Calculate house positions for all planets using Whole Sign system
    # In Whole Sign houses, each house is exactly 30 degrees starting from ascendant sign
    for planet_name in planets:
        planet_longitude = planets[planet_name]['longitude']
        planet_sign = int(planet_longitude / 30)
        
        # Calculate house number using Whole Sign system
        # House 1 starts from ascendant sign
        house_number = ((planet_sign - ascendant_sign) % 12) + 1
        planets[planet_name]['house'] = house_number
    
    return {
        "planets": planets,
        "houses": houses,
        "ayanamsa": ayanamsa,
        "ascendant": ascendant_sidereal
    }

@app.post("/api/calculate-transits")
async def calculate_transits(request: TransitRequest, current_user: User = Depends(get_current_user)):
    jd = swe.julday(
        int(request.transit_date.split('-')[0]),
        int(request.transit_date.split('-')[1]),
        int(request.transit_date.split('-')[2]),
        12.0
    )
    
    # Calculate transit planetary positions
    planets = {}
    planet_names = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
    
    for i, planet in enumerate([0, 1, 4, 2, 5, 3, 6, 11, 12]):  # Swiss Ephemeris planet numbers
        if planet <= 6:  # Regular planets
            pos = swe.calc_ut(jd, planet, swe.FLG_SIDEREAL | swe.FLG_SPEED)
        else:  # Lunar nodes - always use mean for transits
            pos = swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SIDEREAL | swe.FLG_SPEED)
        
        pos_array = pos[0]
        longitude = pos_array[0]
        
        # Use index 3 for speed (standard Swiss Ephemeris)
        speed = pos_array[3] if len(pos_array) > 3 else 0.0
        
        if planet == 12:  # Ketu - add 180 degrees to Rahu
            longitude = (longitude + 180) % 360
        
        is_retrograde = speed < 0 if planet <= 6 else False
        
        planets[planet_names[i]] = {
            'longitude': longitude,
            'sign': int(longitude / 30),
            'degree': longitude % 30,
            'retrograde': is_retrograde
        }
    
    # Calculate birth chart houses for transit display
    birth_data = request.birth_data
    time_parts = birth_data.time.split(':')
    hour = float(time_parts[0]) + float(time_parts[1])/60
    
    if 6.0 <= birth_data.latitude <= 37.0 and 68.0 <= birth_data.longitude <= 97.0:
        tz_offset = 5.5
    else:
        tz_offset = 0
        if birth_data.timezone.startswith('UTC'):
            tz_str = birth_data.timezone[3:]
            if tz_str and ':' in tz_str:
                sign = 1 if tz_str[0] == '+' else -1
                parts = tz_str[1:].split(':')
                tz_offset = sign * (float(parts[0]) + float(parts[1])/60)
    
    utc_hour = hour - tz_offset
    birth_jd = swe.julday(
        int(birth_data.date.split('-')[0]),
        int(birth_data.date.split('-')[1]),
        int(birth_data.date.split('-')[2]),
        utc_hour
    )
    
    birth_houses_data = swe.houses(birth_jd, birth_data.latitude, birth_data.longitude, b'P')
    birth_ayanamsa = swe.get_ayanamsa_ut(birth_jd)
    birth_ascendant_tropical = birth_houses_data[1][0]
    birth_ascendant_sidereal = (birth_ascendant_tropical - birth_ayanamsa) % 360
    
    ascendant_sign = int(birth_ascendant_sidereal / 30)
    houses = []
    for i in range(12):
        house_sign = (ascendant_sign + i) % 12
        house_longitude = (house_sign * 30) + (birth_ascendant_sidereal % 30)
        houses.append({
            'longitude': house_longitude % 360,
            'sign': house_sign
        })
    
    return {
        "planets": planets,
        "houses": houses,
        "ayanamsa": birth_ayanamsa,
        "ascendant": birth_ascendant_sidereal
    }

@app.get("/api/birth-charts")
async def get_birth_charts(search: str = "", limit: int = 50, current_user: User = Depends(get_current_user)):
    print(f"Search query: '{search}', Limit: {limit}")
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    if search.strip():
        search_pattern = f'%{search.strip()}%'
        print(f"Using search pattern: {search_pattern}")
        cursor.execute('''
            SELECT id, userid, name, date, time, latitude, longitude, timezone, created_at, place, gender FROM birth_charts 
            WHERE userid = ? AND name LIKE ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (current_user.userid, search_pattern, limit))
    else:
        print("No search query, returning all charts")
        cursor.execute('SELECT id, userid, name, date, time, latitude, longitude, timezone, created_at, place, gender FROM birth_charts WHERE userid = ? ORDER BY created_at DESC LIMIT ?', (current_user.userid, limit,))
    
    rows = cursor.fetchall()
    print(f"Found {len(rows)} charts")
    conn.close()
    
    charts = []
    for row in rows:
        charts.append({
            'id': row[0],
            'userid': row[1],
            'name': row[2],
            'date': row[3],
            'time': row[4],
            'latitude': row[5],
            'longitude': row[6],
            'timezone': row[7],
            'created_at': row[8],
            'place': row[9] if row[9] else '',
            'gender': row[10] if row[10] else ''
        })
    
    return {"charts": charts}

@app.put("/api/birth-charts/{chart_id}")
async def update_birth_chart(chart_id: int, birth_data: BirthData):
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE birth_charts 
        SET name=?, date=?, time=?, latitude=?, longitude=?, timezone=?, place=?, gender=?
        WHERE id=?
    ''', (birth_data.name, birth_data.date, birth_data.time, 
          birth_data.latitude, birth_data.longitude, birth_data.timezone, birth_data.place, birth_data.gender, chart_id))
    conn.commit()
    conn.close()
    return {"message": "Chart updated successfully"}

@app.delete("/api/birth-charts/{chart_id}")
async def delete_birth_chart(chart_id: int):
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM birth_charts WHERE id=?', (chart_id,))
    conn.commit()
    conn.close()
    return {"message": "Chart deleted successfully"}

@app.post("/api/calculate-yogi")
async def calculate_yogi(birth_data: BirthData):
    time_parts = birth_data.time.split(':')
    hour = float(time_parts[0]) + float(time_parts[1])/60
    
    if 6.0 <= birth_data.latitude <= 37.0 and 68.0 <= birth_data.longitude <= 97.0:
        tz_offset = 5.5
    else:
        tz_offset = 0
        if birth_data.timezone.startswith('UTC'):
            tz_str = birth_data.timezone[3:]
            if tz_str and ':' in tz_str:
                sign = 1 if tz_str[0] == '+' else -1
                parts = tz_str[1:].split(':')
                tz_offset = sign * (float(parts[0]) + float(parts[1])/60)
    
    utc_hour = hour - tz_offset
    jd = swe.julday(
        int(birth_data.date.split('-')[0]),
        int(birth_data.date.split('-')[1]),
        int(birth_data.date.split('-')[2]),
        utc_hour
    )
    
    sun_pos = swe.calc_ut(jd, 0, swe.FLG_SIDEREAL)[0][0]
    moon_pos = swe.calc_ut(jd, 1, swe.FLG_SIDEREAL)[0][0]
    
    yogi_point = (sun_pos + moon_pos) % 360
    yogi_sign = int(yogi_point / 30)
    yogi_degree = yogi_point % 30
    
    avayogi_point = (yogi_point + 186.666667) % 360
    avayogi_sign = int(avayogi_point / 30)
    avayogi_degree = avayogi_point % 30
    
    dagdha_point = (avayogi_point + 12) % 360
    dagdha_sign = int(dagdha_point / 30)
    dagdha_degree = dagdha_point % 30
    
    # Calculate Tithi Shunya Rashi
    tithi_deg = (moon_pos - sun_pos) % 360
    tithi_num = int(tithi_deg / 12) + 1
    
    # Tithi Shunya Rashi calculation based on Tithi
    tithi_shunya_signs = {
        1: 11, 2: 5, 3: 6, 4: 7, 5: 8, 6: 9, 7: 10, 8: 11,
        9: 0, 10: 1, 11: 2, 12: 3, 13: 4, 14: 5, 15: 6
    }
    
    tithi_shunya_sign = tithi_shunya_signs.get(tithi_num, 0)
    tithi_shunya_point = tithi_shunya_sign * 30 + 15  # Middle of the sign
    tithi_shunya_degree = 15.0
    
    from event_prediction.config import SIGN_NAMES
    
    return {
        "yogi": {
            "longitude": yogi_point,
            "sign": yogi_sign,
            "sign_name": SIGN_NAMES[yogi_sign],
            "degree": round(yogi_degree, 2)
        },
        "avayogi": {
            "longitude": avayogi_point,
            "sign": avayogi_sign,
            "sign_name": SIGN_NAMES[avayogi_sign],
            "degree": round(avayogi_degree, 2)
        },
        "dagdha_rashi": {
            "longitude": dagdha_point,
            "sign": dagdha_sign,
            "sign_name": SIGN_NAMES[dagdha_sign],
            "degree": round(dagdha_degree, 2)
        },
        "tithi_shunya_rashi": {
            "longitude": tithi_shunya_point,
            "sign": tithi_shunya_sign,
            "sign_name": SIGN_NAMES[tithi_shunya_sign],
            "degree": round(tithi_shunya_degree, 2)
        }
    }



@app.post("/api/calculate-dasha")
async def calculate_dasha(birth_data: BirthData):
    return await calculate_accurate_dasha(birth_data)

@app.post("/api/dasha")
async def get_dasha(birth_data: BirthData):
    """Get current dasha data for classical engine"""
    return await calculate_accurate_dasha(birth_data)

@app.post("/api/calculate-panchang")
async def calculate_panchang(request: TransitRequest):
    jd = swe.julday(
        int(request.transit_date.split('-')[0]),
        int(request.transit_date.split('-')[1]),
        int(request.transit_date.split('-')[2]),
        12.0
    )
    
    sun_pos = swe.calc_ut(jd, 0, swe.FLG_SIDEREAL)[0][0]
    moon_pos = swe.calc_ut(jd, 1, swe.FLG_SIDEREAL)[0][0]
    
    # Tithi (Lunar day) - difference between Moon and Sun
    tithi_deg = (moon_pos - sun_pos) % 360
    tithi_num = int(tithi_deg / 12) + 1
    
    from event_prediction.config import TITHI_NAMES, VARA_NAMES, NAKSHATRA_NAMES, YOGA_NAMES, KARANA_NAMES
    
    # Vara (Weekday)
    vara_index = int((jd + 1.5) % 7)
    
    # Nakshatra
    nakshatra_index = int(moon_pos / 13.333333)
    
    # Yoga - sum of Sun and Moon longitudes
    yoga_deg = (sun_pos + moon_pos) % 360
    yoga_index = int(yoga_deg / 13.333333)
    
    # Karana - half of Tithi
    karana_index = int(tithi_deg / 6) % 11
    
    return {
        "tithi": {
            "number": tithi_num,
            "name": TITHI_NAMES[min(tithi_num - 1, 14)],
            "degrees": round(tithi_deg, 2)
        },
        "vara": {
            "number": vara_index + 1,
            "name": VARA_NAMES[vara_index]
        },
        "nakshatra": {
            "number": nakshatra_index + 1,
            "name": NAKSHATRA_NAMES[nakshatra_index],
            "degrees": round(moon_pos % 13.333333, 2)
        },
        "yoga": {
            "number": yoga_index + 1,
            "name": YOGA_NAMES[min(yoga_index, 26)],
            "degrees": round(yoga_deg, 2)
        },
        "karana": {
            "number": karana_index + 1,
            "name": KARANA_NAMES[karana_index]
        }
    }

@app.post("/api/calculate-birth-panchang")
async def calculate_birth_panchang(birth_data: BirthData):
    # Use existing calculate_panchang with birth date as transit date
    request = TransitRequest(
        birth_data=birth_data,
        transit_date=birth_data.date
    )
    return await calculate_panchang(request)

@app.post("/api/calculate-divisional-chart")
async def calculate_divisional_chart(request: dict, current_user: User = Depends(get_current_user)):
    """Calculate accurate divisional charts using proper Vedic formulas"""
    birth_data = BirthData(**request['birth_data'])
    division_number = request.get('division', 9)
    

    
    # First get the basic chart
    chart_data = await calculate_chart(birth_data, 'mean', current_user)
    
    def get_divisional_sign(sign, degree_in_sign, division):
        """Calculate divisional sign using proper Vedic formulas"""
        part = int(degree_in_sign / (30/division))
        
        if division == 9:  # Navamsa (D9)
            # Movable signs (0,3,6,9): Start from same sign
            # Fixed signs (1,4,7,10): Start from 9th sign
            # Dual signs (2,5,8,11): Start from 5th sign
            if sign in [0, 3, 6, 9]:  # Movable signs
                navamsa_start = sign
            elif sign in [1, 4, 7, 10]:  # Fixed signs
                navamsa_start = (sign + 8) % 12  # 9th from sign
            else:  # Dual signs [2, 5, 8, 11]
                navamsa_start = (sign + 4) % 12  # 5th from sign
            return (navamsa_start + part) % 12
        
        elif division == 10:  # Dasamsa (D10)
            return (sign + part) % 12 if sign % 2 == 0 else ((sign + 8) + part) % 12
        
        elif division == 12:  # Dwadasamsa (D12)
            return (sign + part) % 12
        
        elif division == 16:  # Shodasamsa (D16)
            # For movable signs: start from Aries
            # For fixed signs: start from Leo  
            # For dual signs: start from Sagittarius
            if sign in [0, 3, 6, 9]:  # Movable signs (Aries, Cancer, Libra, Capricorn)
                d16_start = 0  # Aries
            elif sign in [1, 4, 7, 10]:  # Fixed signs (Taurus, Leo, Scorpio, Aquarius)
                d16_start = 4  # Leo
            else:  # Dual signs (Gemini, Virgo, Sagittarius, Pisces)
                d16_start = 8  # Sagittarius
            return (d16_start + part) % 12
        
        elif division == 20:  # Vimsamsa (D20)
            # For movable signs: start from Aries
            # For fixed signs: start from Sagittarius
            # For dual signs: start from Leo
            if sign in [0, 3, 6, 9]:  # Movable signs
                d20_start = 0  # Aries
            elif sign in [1, 4, 7, 10]:  # Fixed signs
                d20_start = 8  # Sagittarius
            else:  # Dual signs
                d20_start = 4  # Leo
            return (d20_start + part) % 12
        
        elif division == 24:  # Chaturvimsamsa (D24)
            # All signs start from Cancer
            return (3 + part) % 12  # Cancer
        
        elif division == 27:  # Saptavimsamsa (D27)
            # Fire signs (Aries, Leo, Sagittarius): start from Aries
            # Earth signs (Taurus, Virgo, Capricorn): start from Cancer  
            # Air signs (Gemini, Libra, Aquarius): start from Libra
            # Water signs (Cancer, Scorpio, Pisces): start from Capricorn
            if sign in [0, 4, 8]:  # Fire signs
                d27_start = 0  # Aries
            elif sign in [1, 5, 9]:  # Earth signs
                d27_start = 3  # Cancer
            elif sign in [2, 6, 10]:  # Air signs
                d27_start = 6  # Libra
            else:  # Water signs [3, 7, 11]
                d27_start = 9  # Capricorn
            return (d27_start + part) % 12
        
        elif division == 30:  # Trimsamsa (D30)
            # Special calculation for D30 based on planetary rulership within each sign
            if sign % 2 == 1:  # Odd signs
                if part < 5: return 3  # Mars (0-5 degrees)
                elif part < 10: return 6  # Saturn (5-10 degrees)
                elif part < 18: return 4  # Jupiter (10-18 degrees)
                elif part < 25: return 1  # Mercury (18-25 degrees)
                else: return 2  # Venus (25-30 degrees)
            else:  # Even signs
                if part < 5: return 2  # Venus (0-5 degrees)
                elif part < 12: return 1  # Mercury (5-12 degrees)
                elif part < 20: return 4  # Jupiter (12-20 degrees)
                elif part < 25: return 6  # Saturn (20-25 degrees)
                else: return 3  # Mars (25-30 degrees)
        
        elif division == 40:  # Khavedamsa (D40)
            # For movable signs: start from Aries
            # For fixed signs: start from Leo
            # For dual signs: start from Sagittarius
            if sign in [0, 3, 6, 9]:  # Movable signs
                d40_start = 0  # Aries
            elif sign in [1, 4, 7, 10]:  # Fixed signs
                d40_start = 4  # Leo
            else:  # Dual signs
                d40_start = 8  # Sagittarius
            return (d40_start + part) % 12
        
        elif division == 45:  # Akshavedamsa (D45)
            # For movable signs: start from Aries
            # For fixed signs: start from Leo
            # For dual signs: start from Sagittarius
            if sign in [0, 3, 6, 9]:  # Movable signs
                d45_start = 0  # Aries
            elif sign in [1, 4, 7, 10]:  # Fixed signs
                d45_start = 4  # Leo
            else:  # Dual signs
                d45_start = 8  # Sagittarius
            return (d45_start + part) % 12
        
        elif division == 60:  # Shashtyamsa (D60)
            # For movable signs: start from Aries
            # For fixed signs: start from Leo
            # For dual signs: start from Sagittarius
            if sign in [0, 3, 6, 9]:  # Movable signs
                d60_start = 0  # Aries
            elif sign in [1, 4, 7, 10]:  # Fixed signs
                d60_start = 4  # Leo
            else:  # Dual signs
                d60_start = 8  # Sagittarius
            return (d60_start + part) % 12
        
        else:
            # Default calculation for other divisions
            return (sign + part) % 12
    
    # Calculate divisional chart
    divisional_data = {
        'planets': {},
        'houses': [],
        'ayanamsa': chart_data['ayanamsa']
    }
    
    # Calculate divisional ascendant
    asc_sign = int(chart_data['ascendant'] / 30)
    asc_degree = chart_data['ascendant'] % 30
    divisional_asc_sign = get_divisional_sign(asc_sign, asc_degree, division_number)
    divisional_data['ascendant'] = divisional_asc_sign * 30 + 15  # Middle of sign
    
    # Calculate divisional houses
    for i in range(12):
        house_sign = (divisional_asc_sign + i) % 12
        divisional_data['houses'].append({
            'longitude': house_sign * 30,
            'sign': house_sign
        })
    
    # Calculate divisional positions for planets
    # Include Gulika/Mandi in all charts
    planets_to_process = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu', 'Gulika', 'Mandi']
    
    for planet in planets_to_process:
        if planet in chart_data['planets']:
            planet_data = chart_data['planets'][planet]
            
            # For Gulika and Mandi, keep original positions (don't apply divisional transformation)
            if planet in ['Gulika', 'Mandi']:
                divisional_data['planets'][planet] = {
                    'longitude': planet_data['longitude'],
                    'sign': planet_data['sign'],
                    'degree': planet_data['degree']
                }
            else:
                # Regular planetary divisional calculation
                planet_sign = int(planet_data['longitude'] / 30)
                planet_degree = planet_data['longitude'] % 30
                
                divisional_sign = get_divisional_sign(planet_sign, planet_degree, division_number)
                
                # Calculate the actual degree within the divisional sign
                # Each division part represents 30/division_number degrees
                part_size = 30.0 / division_number
                part_index = int(planet_degree / part_size)
                degree_within_part = planet_degree % part_size
                # Scale the degree within part to full sign (0-30 degrees)
                actual_degree = (degree_within_part / part_size) * 30.0
                
                divisional_longitude = divisional_sign * 30 + actual_degree
                
                divisional_data['planets'][planet] = {
                    'longitude': divisional_longitude,
                    'sign': divisional_sign,
                    'degree': actual_degree,
                    'retrograde': planet_data.get('retrograde', False)
                }
    

    
    return {
        'divisional_chart': divisional_data,
        'division_number': division_number,
        'chart_name': f'D{division_number}'
    }

@app.post("/api/calculate-friendship")
async def calculate_friendship(birth_data: BirthData):
    from event_prediction.config import NATURAL_FRIENDS, NATURAL_ENEMIES
    
    # Calculate temporal friendship based on house positions
    time_parts = birth_data.time.split(':')
    hour = float(time_parts[0]) + float(time_parts[1])/60
    
    if 6.0 <= birth_data.latitude <= 37.0 and 68.0 <= birth_data.longitude <= 97.0:
        tz_offset = 5.5
    else:
        tz_offset = 0
        if birth_data.timezone.startswith('UTC'):
            tz_str = birth_data.timezone[3:]
            if tz_str and ':' in tz_str:
                sign = 1 if tz_str[0] == '+' else -1
                parts = tz_str[1:].split(':')
                tz_offset = sign * (float(parts[0]) + float(parts[1])/60)
    
    utc_hour = hour - tz_offset
    jd = swe.julday(
        int(birth_data.date.split('-')[0]),
        int(birth_data.date.split('-')[1]),
        int(birth_data.date.split('-')[2]),
        utc_hour
    )
    
    # Get planetary positions
    planets = {}
    planet_names = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
    
    for i, planet in enumerate([0, 1, 4, 2, 5, 3, 6, 11, 12]):
        if planet <= 6:
            pos = swe.calc_ut(jd, planet, swe.FLG_SIDEREAL)[0]
        else:
            pos = swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SIDEREAL)[0]
            if planet == 12:
                pos = list(pos)
                pos[0] = (pos[0] + 180) % 360
        
        planets[planet_names[i]] = {
            'sign': int(pos[0] / 30),
            'longitude': pos[0]
        }
    
    # Calculate compound friendship
    friendship_matrix = {}
    
    for planet1 in planet_names:
        friendship_matrix[planet1] = {}
        
        for planet2 in planet_names:
            if planet1 == planet2:
                friendship_matrix[planet1][planet2] = 'self'
                continue
            
            # Natural friendship
            if planet2 in NATURAL_FRIENDS.get(planet1, []):
                natural = 'friend'
            elif planet2 in NATURAL_ENEMIES.get(planet1, []):
                natural = 'enemy'
            else:
                natural = 'neutral'
            
            # Temporal friendship (based on house distance)
            house_diff = abs(planets[planet1]['sign'] - planets[planet2]['sign'])
            if house_diff > 6:
                house_diff = 12 - house_diff
            
            if house_diff in [1, 3, 5, 9, 11]:
                temporal = 'friend'
            elif house_diff in [2, 4, 6, 8, 10, 12]:
                temporal = 'enemy'
            else:
                temporal = 'neutral'
            
            # Compound relationship
            if natural == 'friend' and temporal == 'friend':
                compound = 'great_friend'
            elif natural == 'friend' and temporal == 'neutral':
                compound = 'friend'
            elif natural == 'friend' and temporal == 'enemy':
                compound = 'neutral'
            elif natural == 'neutral' and temporal == 'friend':
                compound = 'friend'
            elif natural == 'neutral' and temporal == 'neutral':
                compound = 'neutral'
            elif natural == 'neutral' and temporal == 'enemy':
                compound = 'enemy'
            elif natural == 'enemy' and temporal == 'friend':
                compound = 'neutral'
            elif natural == 'enemy' and temporal == 'neutral':
                compound = 'enemy'
            else:
                compound = 'great_enemy'
            
            friendship_matrix[planet1][planet2] = compound
    
    # Calculate aspects
    aspects_matrix = {}
    
    for planet1 in planet_names:
        aspects_matrix[planet1] = {}
        
        for planet2 in planet_names:
            if planet1 == planet2:
                aspects_matrix[planet1][planet2] = 'self'
                continue
            
            # Calculate angular difference
            angle_diff = abs(planets[planet1]['longitude'] - planets[planet2]['longitude'])
            if angle_diff > 180:
                angle_diff = 360 - angle_diff
            
            # Vedic aspects with orbs
            aspect_type = 'none'
            if 0 <= angle_diff <= 10:  # Conjunction
                aspect_type = 'conjunction'
            elif 50 <= angle_diff <= 70:  # Sextile (60°)
                aspect_type = 'sextile'
            elif 80 <= angle_diff <= 100:  # Square (90°)
                aspect_type = 'square'
            elif 110 <= angle_diff <= 130:  # Trine (120°)
                aspect_type = 'trine'
            elif 170 <= angle_diff <= 180:  # Opposition (180°)
                aspect_type = 'opposition'
            
            aspects_matrix[planet1][planet2] = {
                'type': aspect_type,
                'angle': round(angle_diff, 1)
            }
    
    return {
        "friendship_matrix": friendship_matrix, 
        "aspects_matrix": aspects_matrix,
        "planet_positions": planets
    }

@app.post("/api/predict-house7-events")
async def predict_house7_events(birth_data: BirthData):
    from event_prediction.house7_analyzer import House7Analyzer
    
    # First calculate chart data
    chart_data = await calculate_chart(birth_data, 'mean')
    
    # Initialize House 7 analyzer
    analyzer = House7Analyzer(birth_data, chart_data)
    
    # Analyze house strength
    strength_analysis = analyzer.analyze_house_strength()
    
    # Predict marriage timing
    marriage_predictions = analyzer.predict_marriage_timing()
    
    return {
        "house_analysis": {
            "house_number": 7,
            "house_name": "Marriage/Partnerships",
            "house_lord": analyzer.house_7_lord,
            "house_sign": analyzer.house_7_sign,
            "strength_analysis": strength_analysis
        },
        "event_predictions": marriage_predictions,
        "recommendations": {
            "favorable_periods": [p for p in marriage_predictions if p['probability'] == 'High'],
            "remedies": analyzer._get_remedies() if hasattr(analyzer, '_get_remedies') else []
        }
    }

@app.post("/api/analyze-transits")
async def analyze_transits(request: TransitRequest):
    from event_prediction.transit_analyzer import TransitAnalyzer
    
    # Calculate chart
    chart_data = await calculate_chart(request.birth_data, 'mean')
    
    # Initialize transit analyzer
    transit_analyzer = TransitAnalyzer(request.birth_data, chart_data)
    
    # Parse transit date
    transit_year = int(request.transit_date.split('-')[0])
    
    # Get all transit activations for the year
    activations = transit_analyzer.find_transit_activations(
        ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'],
        transit_year, transit_year
    )
    
    return {
        "transit_date": request.transit_date,
        "activations": activations
    }

@app.post("/api/calculate-yogi-impact")
async def calculate_yogi_impact(birth_data: BirthData):
    from event_prediction.yogi_analyzer import YogiAnalyzer
    
    # Calculate chart
    chart_data = await calculate_chart(birth_data, 'mean')
    
    # Initialize Yogi analyzer
    yogi_analyzer = YogiAnalyzer(birth_data, chart_data)
    
    # Get Yogi data
    yogi_data = yogi_analyzer.yogi_data
    
    # Analyze impact on all houses
    house_impacts = {}
    for house_num in range(1, 13):
        house_impacts[f"house_{house_num}"] = yogi_analyzer.analyze_yogi_impact_on_house(house_num)
    
    return {
        "yogi_points": yogi_data,
        "house_impacts": house_impacts
    }

@app.post("/api/predict-year-events")
async def predict_year_events(request: dict):
    from event_prediction.universal_predictor import UniversalPredictor
    
    birth_data = BirthData(**request['birth_data'])
    year = request['year']
    
    # Calculate chart
    chart_data = await calculate_chart(birth_data, 'mean')
    
    # Initialize universal predictor
    predictor = UniversalPredictor(birth_data, chart_data)
    
    # Get predictions for all houses
    predictions = predictor.predict_year_events(year)
    
    return {
        "year": year,
        "predictions": predictions,
        "birth_info": {
            "name": birth_data.name,
            "date": birth_data.date
        }
    }

@app.post("/api/predict-marriage-complete")
async def predict_marriage_complete(birth_data: BirthData):
    from event_prediction.house7_analyzer import House7Analyzer
    from event_prediction.transit_analyzer import TransitAnalyzer
    from event_prediction.yogi_analyzer import YogiAnalyzer
    
    # Calculate chart first
    chart_data = await calculate_chart(birth_data, 'mean')
    
    # Initialize all analyzers
    house7_analyzer = House7Analyzer(birth_data, chart_data)
    transit_analyzer = TransitAnalyzer(birth_data, chart_data)
    yogi_analyzer = YogiAnalyzer(birth_data, chart_data)
    
    # Get house strength
    house_strength = house7_analyzer.analyze_house_strength()
    
    # Get marriage timing predictions
    marriage_predictions = house7_analyzer.predict_marriage_timing()
    
    # Get Yogi impact on 7th house
    yogi_impact = yogi_analyzer.analyze_yogi_impact_on_house(7)
    
    # Get relevant planets for transit analysis
    relevant_planets = [house7_analyzer.house_7_lord, 'Venus']
    relevant_planets.extend(house7_analyzer._get_planets_in_house(7))
    
    # Get transit activations for next 5 years
    current_year = datetime.now().year
    transit_activations = transit_analyzer.find_transit_activations(
        relevant_planets, current_year, current_year + 5
    )
    
    # Combine all predictions with transit confirmations
    enhanced_predictions = []
    for prediction in marriage_predictions:
        year = prediction['year']
        
        # Find transit confirmations for this year
        year_transits = [t for t in transit_activations if t['date'].year == year]
        
        # Boost strength if strong transits confirm
        transit_boost = 0
        for transit in year_transits:
            if transit['strength'] >= 75:
                transit_boost += 5
        
        enhanced_prediction = prediction.copy()
        enhanced_prediction['strength'] += transit_boost
        enhanced_prediction['transit_confirmations'] = len(year_transits)
        
        # Update probability based on enhanced strength
        if enhanced_prediction['strength'] >= 85:
            enhanced_prediction['probability'] = 'Very High'
        elif enhanced_prediction['strength'] >= 70:
            enhanced_prediction['probability'] = 'High'
        elif enhanced_prediction['strength'] >= 55:
            enhanced_prediction['probability'] = 'Medium'
        
        enhanced_predictions.append(enhanced_prediction)
    
    return {
        "house_strength": house_strength,
        "marriage_predictions": enhanced_predictions,
        "yogi_impact": yogi_impact,
        "transit_activations": transit_activations[:10],
        "house_7_lord": house7_analyzer.house_7_lord,
        "relevant_planets": relevant_planets,
        "algorithm_completeness": "85%",
        "features_active": [
            "Real Vimshottari Dasha calculations",
            "7th house strength analysis", 
            "Jupiter/Saturn transit activations",
            "Solar activation cycles",
            "Yogi/Avayogi impact analysis",
            "Multi-layer confirmation system"
        ]
    }

@app.post("/api/calculate-accurate-dasha")
async def calculate_accurate_dasha(birth_data: BirthData):
    """Calculate accurate Vimshottari Dasha using shared calculator"""
    from shared.dasha_calculator import DashaCalculator
    
    # Convert BirthData to dict
    birth_dict = {
        'name': birth_data.name,
        'date': birth_data.date,
        'time': birth_data.time,
        'latitude': birth_data.latitude,
        'longitude': birth_data.longitude,
        'timezone': birth_data.timezone
    }
    
    calculator = DashaCalculator()
    dasha_data = calculator.calculate_current_dashas(birth_dict)
    
    # Format maha_dashas for API response
    maha_dashas = []
    for maha in dasha_data.get('maha_dashas', []):
        maha_dashas.append({
            'planet': maha['planet'],
            'start': maha['start'].strftime('%Y-%m-%d'),
            'end': maha['end'].strftime('%Y-%m-%d'),
            'years': maha['years']
        })
    
    return {
        "maha_dashas": maha_dashas,
        "current_dashas": {
            "mahadasha": dasha_data.get('mahadasha', {}),
            "antardasha": dasha_data.get('antardasha', {}),
            "pratyantardasha": dasha_data.get('pratyantardasha', {}),
            "sookshma": dasha_data.get('sookshma', {}),
            "prana": dasha_data.get('prana', {})
        },
        "moon_nakshatra": dasha_data.get('moon_nakshatra', 1),
        "moon_lord": dasha_data.get('moon_lord', 'Sun')
    }

@app.post("/api/calculate-cascading-dashas")
async def calculate_cascading_dashas(request: dict):
    """Calculate complete cascading dasha hierarchy for a given date"""
    from shared.dasha_calculator import DashaCalculator
    
    birth_data = BirthData(**request['birth_data'])
    target_date = datetime.strptime(request.get('target_date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d')
    
    # Convert to dict for calculator
    birth_dict = {
        'name': birth_data.name,
        'date': birth_data.date,
        'time': birth_data.time,
        'latitude': birth_data.latitude,
        'longitude': birth_data.longitude,
        'timezone': birth_data.timezone
    }
    
    calculator = DashaCalculator()
    
    # Get current dashas for target date
    current_dashas = calculator.calculate_current_dashas(birth_dict, target_date)
    
    # Get all maha dashas
    maha_dashas = []
    for maha in current_dashas.get('maha_dashas', []):
        maha_dashas.append({
            'planet': maha['planet'],
            'start': maha['start'].strftime('%Y-%m-%d'),
            'end': maha['end'].strftime('%Y-%m-%d'),
            'current': maha['start'] <= target_date <= maha['end'],
            'years': maha['years']
        })
    
    # Find current maha dasha
    current_maha = None
    for maha in current_dashas.get('maha_dashas', []):
        if maha['start'] <= target_date <= maha['end']:
            current_maha = maha
            break
    
    result = {
        'maha_dashas': maha_dashas,
        'antar_dashas': [],
        'pratyantar_dashas': [],
        'sookshma_dashas': [],
        'prana_dashas': [],
        'current_dashas': current_dashas.get('current_dashas', {})
    }
    
    if current_maha:
        # Calculate all antar dashas for current maha
        antar_request = {
            'birth_data': birth_dict,
            'parent_dasha': {
                'planet': current_maha['planet'],
                'start': current_maha['start'].strftime('%Y-%m-%d'),
                'end': current_maha['end'].strftime('%Y-%m-%d')
            },
            'dasha_type': 'antar',
            'target_date': target_date.strftime('%Y-%m-%d')
        }
        antar_result = await calculate_sub_dashas(antar_request)
        result['antar_dashas'] = antar_result['sub_dashas']
        
        # Find current antar
        current_antar = None
        for antar in result['antar_dashas']:
            if antar['current']:
                current_antar = antar
                break
        
        if current_antar:
            # Calculate pratyantar dashas
            pratyantar_request = {
                'birth_data': birth_dict,
                'parent_dasha': current_antar,
                'dasha_type': 'pratyantar',
                'target_date': target_date.strftime('%Y-%m-%d'),
                'maha_lord': current_maha['planet']
            }
            pratyantar_result = await calculate_sub_dashas(pratyantar_request)
            result['pratyantar_dashas'] = pratyantar_result['sub_dashas']
            
            # Find current pratyantar
            current_pratyantar = None
            for pratyantar in result['pratyantar_dashas']:
                if pratyantar['current']:
                    current_pratyantar = pratyantar
                    break
            
            if current_pratyantar:
                # Calculate sookshma dashas
                sookshma_request = {
                    'birth_data': birth_dict,
                    'parent_dasha': current_pratyantar,
                    'dasha_type': 'sookshma',
                    'target_date': target_date.strftime('%Y-%m-%d'),
                    'maha_lord': current_maha['planet'],
                    'antar_lord': current_antar['planet']
                }
                sookshma_result = await calculate_sub_dashas(sookshma_request)
                result['sookshma_dashas'] = sookshma_result['sub_dashas']
                
                # Find current sookshma
                current_sookshma = None
                for sookshma in result['sookshma_dashas']:
                    if sookshma['current']:
                        current_sookshma = sookshma
                        break
                
                if current_sookshma:
                    # Calculate prana dashas
                    prana_request = {
                        'birth_data': birth_dict,
                        'parent_dasha': current_sookshma,
                        'dasha_type': 'prana',
                        'target_date': target_date.strftime('%Y-%m-%d'),
                        'maha_lord': current_maha['planet'],
                        'antar_lord': current_antar['planet'],
                        'pratyantar_lord': current_pratyantar['planet']
                    }
                    prana_result = await calculate_sub_dashas(prana_request)
                    result['prana_dashas'] = prana_result['sub_dashas']
    
    return result

@app.post("/api/calculate-sub-dashas")
async def calculate_sub_dashas(request: dict):
    """Calculate sub-dashas (Antar, Pratyantar, Sookshma, Prana) for given parent dasha"""
    from event_prediction.config import DASHA_PERIODS, PLANET_ORDER
    
    birth_data = BirthData(**request['birth_data'])
    parent_dasha = request['parent_dasha']
    dasha_type = request['dasha_type']
    target_date = datetime.strptime(request.get('target_date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d')
    
    # Calculate sub-dashas using proper Vimshottari method
    parent_start = datetime.strptime(parent_dasha['start'], '%Y-%m-%d')
    parent_end = datetime.strptime(parent_dasha['end'], '%Y-%m-%d')
    parent_planet = parent_dasha['planet']
    
    # Calculate parent period in days
    parent_total_days = (parent_end - parent_start).days + 1  # Include end date
    
    # Get planet order starting from parent planet
    start_index = PLANET_ORDER.index(parent_planet)
    sub_dashas = []
    current_date = parent_start
    
    # Calculate total period for proportional division
    total_period = 0
    for i in range(9):
        planet = PLANET_ORDER[(start_index + i) % 9]
        if dasha_type == 'antar':
            period = (DASHA_PERIODS[parent_planet] * DASHA_PERIODS[planet]) / 120
        elif dasha_type == 'pratyantar':
            antar_period = (DASHA_PERIODS[request.get('maha_lord', parent_planet)] * DASHA_PERIODS[parent_planet]) / 120
            period = (antar_period * DASHA_PERIODS[planet]) / 120
        elif dasha_type == 'sookshma':
            maha_lord = request.get('maha_lord', parent_planet)
            antar_lord = request.get('antar_lord', parent_planet)
            antar_period = (DASHA_PERIODS[maha_lord] * DASHA_PERIODS[antar_lord]) / 120
            pratyantar_period = (antar_period * DASHA_PERIODS[parent_planet]) / 120
            period = (pratyantar_period * DASHA_PERIODS[planet]) / 120
        elif dasha_type == 'prana':
            maha_lord = request.get('maha_lord', parent_planet)
            antar_lord = request.get('antar_lord', parent_planet)
            pratyantar_lord = request.get('pratyantar_lord', parent_planet)
            antar_period = (DASHA_PERIODS[maha_lord] * DASHA_PERIODS[antar_lord]) / 120
            pratyantar_period = (antar_period * DASHA_PERIODS[pratyantar_lord]) / 120
            sookshma_period = (pratyantar_period * DASHA_PERIODS[parent_planet]) / 120
            period = (sookshma_period * DASHA_PERIODS[planet]) / 120
        else:
            period = DASHA_PERIODS[planet]
        
        total_period += period
    
    # Calculate actual sub-dasha periods
    for i in range(9):
        planet = PLANET_ORDER[(start_index + i) % 9]
        
        if dasha_type == 'antar':
            period = (DASHA_PERIODS[parent_planet] * DASHA_PERIODS[planet]) / 120
        elif dasha_type == 'pratyantar':
            antar_period = (DASHA_PERIODS[request.get('maha_lord', parent_planet)] * DASHA_PERIODS[parent_planet]) / 120
            period = (antar_period * DASHA_PERIODS[planet]) / 120
        elif dasha_type == 'sookshma':
            maha_lord = request.get('maha_lord', parent_planet)
            antar_lord = request.get('antar_lord', parent_planet)
            antar_period = (DASHA_PERIODS[maha_lord] * DASHA_PERIODS[antar_lord]) / 120
            pratyantar_period = (antar_period * DASHA_PERIODS[parent_planet]) / 120
            period = (pratyantar_period * DASHA_PERIODS[planet]) / 120
        elif dasha_type == 'prana':
            maha_lord = request.get('maha_lord', parent_planet)
            antar_lord = request.get('antar_lord', parent_planet)
            pratyantar_lord = request.get('pratyantar_lord', parent_planet)
            antar_period = (DASHA_PERIODS[maha_lord] * DASHA_PERIODS[antar_lord]) / 120
            pratyantar_period = (antar_period * DASHA_PERIODS[pratyantar_lord]) / 120
            sookshma_period = (pratyantar_period * DASHA_PERIODS[parent_planet]) / 120
            period = (sookshma_period * DASHA_PERIODS[planet]) / 120
        
        # Calculate days for this sub-dasha
        ratio = period / total_period
        sub_days = parent_total_days * ratio
        end_date = current_date + timedelta(days=sub_days)
        
        # Ensure we don't exceed parent end date
        if end_date > parent_end:
            end_date = parent_end
        
        # For display, make end date inclusive but not beyond parent end
        display_end = min(end_date.date(), parent_end.date())
        
        is_current = current_date.date() <= target_date.date() <= display_end
        
        sub_dashas.append({
            'planet': planet,
            'start': current_date.strftime('%Y-%m-%d'),
            'end': display_end.strftime('%Y-%m-%d'),
            'current': is_current,
            'years': round(period, 4)
        })
        
        current_date = end_date
        if current_date >= parent_end:
            break
    
    return {'sub_dashas': sub_dashas}

@app.post("/api/calculate-ashtakavarga")
async def calculate_ashtakavarga(request: dict, current_user: User = Depends(get_current_user)):
    from ashtakavarga import AshtakavargaCalculator
    
    birth_data = BirthData(**request['birth_data'])
    chart_type = request.get('chart_type', 'lagna')
    
    if chart_type == 'transit':
        # For transit charts, use current transit positions
        transit_date = request.get('transit_date', datetime.now().strftime('%Y-%m-%d'))
        # Parse ISO datetime string to date if needed
        if 'T' in transit_date:
            transit_date = transit_date.split('T')[0]
        transit_request = TransitRequest(
            birth_data=birth_data,
            transit_date=transit_date
        )
        chart_data = await calculate_transits(transit_request, current_user)
    else:
        # For birth charts (lagna, navamsa), use birth positions
        chart_data = await calculate_chart(birth_data, 'mean', current_user)
    
    calculator = AshtakavargaCalculator(birth_data, chart_data)
    
    sarva = calculator.calculate_sarvashtakavarga()
    analysis = calculator.get_ashtakavarga_analysis(chart_type)
    
    return {
        "ashtakavarga": sarva,
        "analysis": analysis,
        "chart_type": chart_type
    }

@app.get("/api/interpretations/planet-nakshatra")
async def get_planet_nakshatra_interpretation(
    planet: str, 
    nakshatra: str, 
    house: int,
    current_user: User = Depends(get_current_user)
):
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT interpretation FROM planet_nakshatra_interpretations WHERE planet = ? AND nakshatra = ? AND house = ?",
        (planet, nakshatra, house)
    )
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {"interpretation": result[0]}
    else:
        raise HTTPException(status_code=404, detail="Interpretation not found")

@app.post("/api/analyze-houses")
async def analyze_houses(birth_data: BirthData, current_user: User = Depends(get_current_user)):
    """Comprehensive analysis of all 12 houses"""
    from event_prediction.universal_house_analyzer import UniversalHouseAnalyzer
    
    # Calculate chart data
    chart_data = await calculate_chart(birth_data, 'mean', current_user)
    
    # Initialize house analyzer
    house_analyzer = UniversalHouseAnalyzer(birth_data, chart_data)
    
    # Analyze all houses
    house_analyses = house_analyzer.analyze_all_houses()
    
    return {
        "birth_info": {
            "name": birth_data.name,
            "date": birth_data.date,
            "time": birth_data.time
        },
        "house_analyses": house_analyses
    }

@app.post("/api/analyze-single-house")
async def analyze_single_house(request: dict, current_user: User = Depends(get_current_user)):
    """Detailed analysis of a single house"""
    from event_prediction.universal_house_analyzer import UniversalHouseAnalyzer
    
    birth_data = BirthData(**request['birth_data'])
    house_number = request['house_number']
    
    # Calculate chart data
    chart_data = await calculate_chart(birth_data, 'mean', current_user)
    
    # Initialize house analyzer
    house_analyzer = UniversalHouseAnalyzer(birth_data, chart_data)
    
    # Analyze specific house
    house_analysis = house_analyzer.analyze_house(house_number)
    
    return {
        "birth_info": {
            "name": birth_data.name,
            "date": birth_data.date,
            "time": birth_data.time
        },
        "house_analysis": house_analysis
    }

@app.post("/api/daily-predictions")
async def get_daily_predictions(request: DailyPredictionRequest, current_user: User = Depends(get_current_user)):
    """Get daily predictions using rule engine"""
    from datetime import datetime, date
    
    # Parse target date
    target_date = date.today()
    if request.target_date:
        target_date = datetime.strptime(request.target_date, '%Y-%m-%d').date()
    
    # Get required data using existing functions
    chart_data = await calculate_chart(request.birth_data, 'mean', current_user)
    dasha_data = await calculate_accurate_dasha(request.birth_data)
    
    # Calculate transit data for target date
    transit_request = TransitRequest(
        birth_data=request.birth_data,
        transit_date=target_date.isoformat()
    )
    transit_data = await calculate_transits(transit_request, current_user)
    
    # Initialize prediction engine
    prediction_engine = DailyPredictionEngine()
    
    # Generate predictions
    predictions = prediction_engine.get_daily_predictions(
        birth_data=request.birth_data.model_dump(),
        chart_data=chart_data,
        dasha_data=dasha_data,
        transit_data=transit_data,
        target_date=target_date
    )
    
    return predictions

@app.post("/api/daily-prediction-rules")
async def add_daily_prediction_rule(rule_data: dict, current_user: User = Depends(get_current_user)):
    """Add new daily prediction rule (admin only)"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    prediction_engine = DailyPredictionEngine()
    success = prediction_engine.add_prediction_rule(rule_data)
    
    if success:
        return {"message": "Prediction rule added successfully"}
    else:
        raise HTTPException(status_code=400, detail="Failed to add prediction rule")

@app.post("/api/reset-prediction-rules")
async def reset_prediction_rules(current_user: User = Depends(get_current_user)):
    """Reset daily prediction rules to defaults (admin only)"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    prediction_engine = DailyPredictionEngine()
    success = prediction_engine.reset_prediction_rules()
    
    if success:
        return {"message": "Prediction rules reset successfully"}
    else:
        raise HTTPException(status_code=400, detail="Failed to reset prediction rules")

@app.post("/api/classical-prediction")
async def get_classical_prediction(request: ClassicalPredictionRequest, current_user: User = Depends(get_current_user)):
    """Generate comprehensive classical Vedic prediction"""
    from classical_engine.prediction_engine import ClassicalPredictionEngine
    
    # Convert birth_data to dict
    birth_dict = {
        'name': request.birth_data.name,
        'date': request.birth_data.date,
        'time': request.birth_data.time,
        'latitude': request.birth_data.latitude,
        'longitude': request.birth_data.longitude,
        'timezone': request.birth_data.timezone
    }
    
    # Parse prediction date
    prediction_date = datetime.now()
    if request.prediction_date:
        try:
            prediction_date = datetime.strptime(request.prediction_date, '%Y-%m-%d')
        except ValueError:
            prediction_date = datetime.now()
    
    # Initialize classical prediction engine with specific date
    engine = ClassicalPredictionEngine(birth_dict, prediction_date)
    
    # Generate comprehensive prediction
    result = engine.generate_comprehensive_prediction()
    
    return result

@app.get("/api/daily-prediction-rules")
async def get_daily_prediction_rules(current_user: User = Depends(get_current_user)):
    """Get all daily prediction rules (admin only)"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    import sqlite3
    import json
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM daily_prediction_rules ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    
    rules = []
    for row in rows:
        rules.append({
            "id": row[0],
            "rule_type": row[1],
            "conditions": json.loads(row[2]),
            "prediction_template": row[3],
            "confidence_base": row[4],
            "life_areas": json.loads(row[5]) if row[5] else [],
            "timing_advice": row[6],
            "colors": json.loads(row[7]) if row[7] else [],
            "is_active": bool(row[8]),
            "created_at": row[9]
        })
    
    return {"rules": rules}

@app.delete("/api/daily-prediction-rules/{rule_id}")
async def delete_daily_prediction_rule(rule_id: str, current_user: User = Depends(get_current_user)):
    """Delete a daily prediction rule (admin only)"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    import sqlite3
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM daily_prediction_rules WHERE id = ?", (rule_id,))
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Rule not found")
    
    conn.commit()
    conn.close()
    
    return {"message": "Rule deleted successfully"}

@app.put("/api/daily-prediction-rules/{rule_id}")
async def update_daily_prediction_rule(rule_id: str, rule_data: dict, current_user: User = Depends(get_current_user)):
    """Update a daily prediction rule (admin only)"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    import sqlite3
    import json
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE daily_prediction_rules 
        SET rule_type=?, conditions=?, prediction_template=?, confidence_base=?, 
            life_areas=?, timing_advice=?, colors=?, is_active=?
        WHERE id=?
    ''', (
        rule_data.get("rule_type", ""),
        json.dumps(rule_data.get("conditions", {})),
        rule_data.get("prediction_template", ""),
        rule_data.get("confidence_base", 50),
        json.dumps(rule_data.get("life_areas", [])),
        rule_data.get("timing_advice", ""),
        json.dumps(rule_data.get("colors", [])),
        rule_data.get("is_active", True),
        rule_id
    ))
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Rule not found")
    
    conn.commit()
    conn.close()
    
    return {"message": "Rule updated successfully"}

# Nakshatra Management APIs
class NakshatraData(BaseModel):
    name: str
    lord: str
    deity: str
    nature: str
    guna: str
    description: str
    characteristics: str
    positive_traits: str
    negative_traits: str
    careers: str
    compatibility: str

@app.get("/api/nakshatras")
async def get_nakshatras(current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM nakshatras ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    
    nakshatras = []
    for row in rows:
        nakshatras.append({
            "id": row[0],
            "name": row[1],
            "lord": row[2],
            "deity": row[3],
            "nature": row[4],
            "guna": row[5],
            "description": row[6],
            "characteristics": row[7],
            "positive_traits": row[8],
            "negative_traits": row[9],
            "careers": row[10],
            "compatibility": row[11],
            "created_at": row[12]
        })
    
    return {"nakshatras": nakshatras}

@app.get("/api/nakshatras-public")
async def get_nakshatras_public(current_user: User = Depends(get_current_user)):
    """Public endpoint to get detailed nakshatra data for UI"""
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM nakshatras ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    
    nakshatras = []
    for row in rows:
        nakshatras.append({
            "name": row[1],
            "lord": row[2],
            "deity": row[3],
            "nature": row[4],
            "guna": row[5],
            "description": row[6],
            "characteristics": row[7],
            "positive_traits": row[8],
            "negative_traits": row[9],
            "careers": row[10],
            "compatibility": row[11]
        })
    
    return {"nakshatras": nakshatras}

@app.post("/api/nakshatras")
async def create_nakshatra(nakshatra_data: NakshatraData, current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO nakshatras (name, lord, deity, nature, guna, description, 
                                  characteristics, positive_traits, negative_traits, 
                                  careers, compatibility)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            nakshatra_data.name, nakshatra_data.lord, nakshatra_data.deity,
            nakshatra_data.nature, nakshatra_data.guna, nakshatra_data.description,
            nakshatra_data.characteristics, nakshatra_data.positive_traits,
            nakshatra_data.negative_traits, nakshatra_data.careers,
            nakshatra_data.compatibility
        ))
        conn.commit()
        nakshatra_id = cursor.lastrowid
        conn.close()
        
        return {"message": "Nakshatra created successfully", "id": nakshatra_id}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Nakshatra name already exists")

@app.put("/api/nakshatras/{nakshatra_id}")
async def update_nakshatra(nakshatra_id: int, nakshatra_data: NakshatraData, current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE nakshatras 
        SET name=?, lord=?, deity=?, nature=?, guna=?, description=?, 
            characteristics=?, positive_traits=?, negative_traits=?, 
            careers=?, compatibility=?
        WHERE id=?
    ''', (
        nakshatra_data.name, nakshatra_data.lord, nakshatra_data.deity,
        nakshatra_data.nature, nakshatra_data.guna, nakshatra_data.description,
        nakshatra_data.characteristics, nakshatra_data.positive_traits,
        nakshatra_data.negative_traits, nakshatra_data.careers,
        nakshatra_data.compatibility, nakshatra_id
    ))
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Nakshatra not found")
    
    conn.commit()
    conn.close()
    
    return {"message": "Nakshatra updated successfully"}

@app.delete("/api/nakshatras/{nakshatra_id}")
async def delete_nakshatra(nakshatra_id: int, current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM nakshatras WHERE id=?", (nakshatra_id,))
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Nakshatra not found")
    
    conn.commit()
    conn.close()
    
    return {"message": "Nakshatra deleted successfully"}

@app.post("/api/marriage-analysis")
async def get_marriage_analysis(request: MarriageAnalysisRequest, current_user: User = Depends(get_current_user)):
    """Get marriage analysis for single chart or compatibility"""
    analyzer = MarriageAnalyzer()
    
    if request.analysis_type == "single":
        result = analyzer.analyze_single_chart(request.chart_data, request.birth_details)
    elif request.analysis_type == "compatibility":
        # For now, return placeholder for compatibility
        result = {
            "message": "Compatibility analysis coming soon",
            "chart_type": "compatibility"
        }
    else:
        raise HTTPException(status_code=400, detail="Invalid analysis type")
    
    return result

@app.post("/api/compatibility-analysis")
async def analyze_compatibility(request: CompatibilityRequest, current_user: User = Depends(get_current_user)):
    """Analyze compatibility between two birth charts"""
    from marriage_analysis.compatibility_analyzer import CompatibilityAnalyzer
    
    # Calculate both charts
    boy_chart = await calculate_chart(request.boy_birth_data, 'mean', current_user)
    girl_chart = await calculate_chart(request.girl_birth_data, 'mean', current_user)
    
    # Convert birth data to dict
    boy_birth = request.boy_birth_data.model_dump()
    girl_birth = request.girl_birth_data.model_dump()
    
    # Analyze compatibility
    analyzer = CompatibilityAnalyzer()
    result = analyzer.analyze_compatibility(boy_chart, girl_chart, boy_birth, girl_birth)
    
    return {
        "boy_details": boy_birth,
        "girl_details": girl_birth,
        "compatibility_analysis": result
    }

# Initialize prediction engine on startup
@app.on_event("startup")
async def startup_event():
    try:
        # Initialize daily prediction rules database
        prediction_engine = DailyPredictionEngine()
        # Reset rules to ensure we have the latest ones
        prediction_engine.reset_prediction_rules()
        print("Daily prediction engine initialized with updated rules")
    except Exception as e:
        print(f"Warning: Could not initialize prediction engine: {e}")
    
    # Initialize house combinations database
    try:
        init_house_combinations_db()
        print("House combinations database initialized")
    except Exception as e:
        print(f"Warning: Could not initialize house combinations database: {e}")

# Horoscope endpoints
@app.get("/api/horoscope/daily/{zodiac_sign}")
async def get_daily_horoscope(zodiac_sign: str, date: Optional[str] = None):
    try:
        if date:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
        else:
            date_obj = None
            
        horoscope = horoscope_api.get_daily_horoscope(zodiac_sign.capitalize(), date_obj)
        return horoscope
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/horoscope/weekly/{zodiac_sign}")
async def get_weekly_horoscope(zodiac_sign: str, date: Optional[str] = None):
    try:
        if date:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
        else:
            date_obj = None
            
        horoscope = horoscope_api.get_weekly_horoscope(zodiac_sign.capitalize(), date_obj)
        return horoscope
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/horoscope/monthly/{zodiac_sign}")
async def get_monthly_horoscope(zodiac_sign: str, date: Optional[str] = None):
    try:
        if date:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
        else:
            date_obj = None
            
        horoscope = horoscope_api.get_monthly_horoscope(zodiac_sign.capitalize(), date_obj)
        return horoscope
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/horoscope/yearly/{zodiac_sign}")
async def get_yearly_horoscope(zodiac_sign: str, date: Optional[str] = None):
    try:
        if date:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
        else:
            date_obj = None
            
        horoscope = horoscope_api.get_yearly_horoscope(zodiac_sign.capitalize(), date_obj)
        return horoscope
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/horoscope/all-signs")
async def get_all_daily_horoscopes(date: Optional[str] = None):
    try:
        zodiac_signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                       'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        
        if date:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
        else:
            date_obj = None
            
        horoscopes = {}
        for sign in zodiac_signs:
            horoscopes[sign.lower()] = horoscope_api.get_daily_horoscope(sign, date_obj)
            
        return horoscopes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Admin endpoints
@app.get("/api/admin/users")
async def get_admin_users(current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    cursor.execute("SELECT userid, name, phone, role, created_at FROM users ORDER BY created_at DESC")
    rows = cursor.fetchall()
    
    users = []
    for row in rows:
        # Get user subscriptions
        cursor.execute('''
            SELECT sp.platform, sp.plan_name, us.status, us.end_date
            FROM user_subscriptions us
            JOIN subscription_plans sp ON us.plan_id = sp.plan_id
            WHERE us.userid = ? AND us.status = 'active' AND us.end_date >= date('now')
        ''', (row[0],))
        
        subscriptions = {}
        for sub in cursor.fetchall():
            subscriptions[sub[0]] = {
                'plan_name': sub[1],
                'status': sub[2],
                'end_date': sub[3]
            }
        
        users.append({
            'userid': row[0],
            'name': row[1],
            'phone': row[2],
            'role': row[3],
            'created_at': row[4],
            'subscriptions': subscriptions
        })
    
    conn.close()
    return {'users': users}

@app.get("/api/admin/charts")
async def get_admin_charts(current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT bc.id, bc.userid, bc.name, bc.date, bc.time, bc.latitude, bc.longitude, bc.place, bc.gender, bc.created_at, u.name as user_name, u.phone
        FROM birth_charts bc
        JOIN users u ON bc.userid = u.userid
        ORDER BY bc.created_at DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    
    charts = []
    for row in rows:
        charts.append({
            'id': row[0],
            'userid': row[1],
            'name': row[2],
            'date': row[3],
            'time': row[4],
            'latitude': row[5],
            'longitude': row[6],
            'place': row[7],
            'gender': row[8],
            'created_at': row[9],
            'user_name': row[10],
            'user_phone': row[11]
        })
    
    return {'charts': charts}

@app.delete("/api/admin/users/{user_id}")
async def delete_admin_user(user_id: int, current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE userid=?', (user_id,))
    conn.commit()
    conn.close()
    return {"message": "User deleted successfully"}

@app.delete("/api/admin/charts/{chart_id}")
async def delete_admin_chart(chart_id: int, current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM birth_charts WHERE id=?', (chart_id,))
    conn.commit()
    conn.close()
    return {"message": "Chart deleted successfully"}

@app.put("/api/admin/users/{user_id}")
async def update_admin_user(user_id: int, user_data: dict, current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users 
        SET name=?, phone=?, role=?
        WHERE userid=?
    ''', (user_data['name'], user_data['phone'], user_data['role'], user_id))
    conn.commit()
    conn.close()
    return {"message": "User updated successfully"}

@app.put("/api/admin/users/{user_id}/subscription")
async def update_user_subscription(user_id: int, subscription_data: dict, current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    platform = subscription_data['platform']
    plan_name = subscription_data['plan_name']
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    # Get plan_id
    cursor.execute("SELECT plan_id FROM subscription_plans WHERE platform = ? AND plan_name = ?", (platform, plan_name))
    plan = cursor.fetchone()
    
    if not plan:
        conn.close()
        raise HTTPException(status_code=404, detail="Plan not found")
    
    plan_id = plan[0]
    
    # Deactivate existing subscription for this platform
    cursor.execute('''
        UPDATE user_subscriptions 
        SET status = 'inactive' 
        WHERE userid = ? AND plan_id IN (
            SELECT plan_id FROM subscription_plans WHERE platform = ?
        )
    ''', (user_id, platform))
    
    # Add new subscription
    from datetime import date, timedelta
    start_date = date.today()
    end_date = start_date + timedelta(days=365)  # 1 year
    
    cursor.execute('''
        INSERT INTO user_subscriptions (userid, plan_id, start_date, end_date, status)
        VALUES (?, ?, ?, ?, 'active')
    ''', (user_id, plan_id, start_date, end_date))
    
    conn.commit()
    conn.close()
    
    return {"message": "Subscription updated successfully"}

@app.get("/api/admin/subscription-plans")
async def get_admin_subscription_plans(current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    cursor.execute("SELECT platform, plan_name FROM subscription_plans WHERE is_active = 1 ORDER BY platform, plan_name")
    rows = cursor.fetchall()
    conn.close()
    
    plans = []
    for row in rows:
        plans.append({
            'platform': row[0],
            'plan_name': row[1]
        })
    
    return {'plans': plans}

if __name__ == "__main__":
    import uvicorn
    print("Starting Astrology API server on port 8001...")
    # Configure uvicorn with extended timeouts for AI requests
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8001,
        timeout_keep_alive=300,  # Keep connections alive for 5 minutes
        timeout_graceful_shutdown=60,  # Allow 60 seconds for graceful shutdown
        access_log=False,  # Disable access logs for performance
        limit_max_requests=1000,  # Prevent memory leaks
        limit_concurrency=100  # Limit concurrent connections
    )