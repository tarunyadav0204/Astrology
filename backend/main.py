from fastapi import FastAPI, Depends, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator
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
from career_analysis.career_ai_router import router as career_ai_router
from panchang.panchang_routes import router as panchang_router
from panchang.muhurat_routes import router as muhurat_router
from muhurat_routes import router as childbirth_router
from health.health_routes import router as health_router
from wealth.wealth_routes import router as wealth_router
from chat.chat_routes import router as chat_router
from nakshatra.nakshatra_routes import router as nakshatra_router
from festivals.routes import router as festivals_router
from chat_history.routes import router as chat_history_router, init_chat_tables
from chat_history.admin_routes import router as chat_admin_router
from credits.routes import router as credits_router
from education.routes import router as education_router
from marriage.marriage_routes import router as marriage_router
from progeny.progeny_routes import router as progeny_router
from trading_routes import router as trading_router
from yogini_dasha_routes import router as yogini_dasha_router
from physical_scan_routes import router as physical_scan_router
from physical_feedback_routes import router as physical_feedback_router
from numerology_routes import router as numerology_router
import math
from datetime import timedelta
import signal
import sys
import atexit
import logging
from encryption_utils import EncryptionManager
try:
    encryptor = EncryptionManager()
except ValueError as e:
    print(f"WARNING: Encryption not configured: {e}")
    encryptor = None

# Configure logging for shutdown events
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server_shutdown.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def log_shutdown(reason):
    logger.critical(f"SERVER SHUTDOWN: {reason}")
    try:
        logger.critical(f"Memory: {psutil.Process().memory_info().rss / 1024 / 1024:.2f}MB")
        logger.critical(f"Connections: {len(psutil.Process().connections())}")
    except:
        pass

def signal_handler(signum, frame):
    signal_names = {signal.SIGTERM: "SIGTERM", signal.SIGINT: "SIGINT"}
    log_shutdown(f"Signal {signal_names.get(signum, signum)}")
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)
atexit.register(lambda: logger.critical("Server shutdown completed"))


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

# Install psutil if not available
try:
    import psutil
except ImportError:
    print("Installing psutil for memory monitoring...")
    import subprocess
    subprocess.check_call(["pip", "install", "psutil"])
    import psutil

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

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        import time
        import gc
        start_time = time.time()
        
        # Log incoming request
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {request.method} {request.url.path} - Client: {request.client.host if request.client else 'unknown'}")
        
        response = await call_next(request)
        
        # Log response and cleanup
        process_time = time.time() - start_time
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Response: {response.status_code} - Time: {process_time:.2f}s")
        
        # Force garbage collection after heavy requests
        if process_time > 5.0 or request.url.path in ["/api/calculate-chart", "/api/chat", "/api/ai-insights"]:
            gc.collect()
        
        return response

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(TimeoutMiddleware)

# CORS configuration for multiple domains
allowed_origins = [
    "https://astrovishnu.com",
    "https://www.astrovishnu.com",
    "https://astroroshni.com",
    "https://www.astroroshni.com",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001"
]

# Add development origins if in development mode
if os.getenv('ENVIRONMENT', 'development') == 'development':
    allowed_origins.append("*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
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
app.include_router(career_ai_router, prefix="/api")
app.include_router(panchang_router, prefix="/api/panchang")
app.include_router(muhurat_router, prefix="/api")
app.include_router(childbirth_router, prefix="/api")
# Note: childbirth_router already includes vehicle and griha pravesh endpoints
app.include_router(health_router, prefix="/api")
app.include_router(wealth_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(nakshatra_router, prefix="/api")
app.include_router(festivals_router, prefix="/api")
app.include_router(chat_history_router, prefix="/api")
app.include_router(chat_admin_router, prefix="/api")
app.include_router(credits_router, prefix="/api/credits")
app.include_router(education_router, prefix="/api")
app.include_router(marriage_router, prefix="/api")
app.include_router(progeny_router, prefix="/api")
app.include_router(trading_router, prefix="/api")
app.include_router(yogini_dasha_router, prefix="/api")
app.include_router(physical_scan_router, prefix="/api")
app.include_router(physical_feedback_router, prefix="/api")
app.include_router(numerology_router, prefix="/api")




# Root endpoint for health check
@app.get("/")
async def root():
    return {"message": "Astrology API", "docs": "/api/docs", "version": "1.0.0"}

# Dedicated health check endpoint for GCP
@app.get("/health")
async def root_health():
    return {"status": "healthy", "message": "Astrology API is running"}

@app.get("/healthz")
async def kubernetes_health():
    return {"status": "ok"}

@app.get("/readiness")
async def readiness_check():
    try:
        # Quick database check
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        return {"status": "ready"}
    except:
        return {"status": "not ready"}, 503

@app.get("/api/test")
async def test_endpoint():
    return {"status": "ok", "message": "API is working", "timestamp": datetime.now().isoformat()}

@app.get("/api/test-gemini")
async def test_gemini_connectivity():
    """Test Gemini API connectivity and configuration"""
    import os
    import requests
    
    # Check API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return {"success": False, "error": "GEMINI_API_KEY not set"}
    
    # Test network connectivity
    try:
        response = requests.get('https://generativelanguage.googleapis.com', timeout=10)
        network_ok = True
        network_status = response.status_code
    except Exception as e:
        network_ok = False
        network_status = str(e)
    
    # Test Gemini API
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        # Simple test request
        response = model.generate_content("Hello, just testing connectivity")
        gemini_ok = True
        gemini_response = response.text[:100] if response.text else "No response text"
    except Exception as e:
        gemini_ok = False
        gemini_response = str(e)
    
    return {
        "success": network_ok and gemini_ok,
        "api_key_present": bool(api_key),
        "api_key_length": len(api_key) if api_key else 0,
        "network_connectivity": {
            "success": network_ok,
            "status": network_status
        },
        "gemini_api": {
            "success": gemini_ok,
            "response": gemini_response
        }
    }

# Remove custom /docs override - let FastAPI handle it automatically
# GCP health checks will use the default FastAPI /docs endpoint

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
    relation: Optional[str] = "other"
    
    class Config:
        # Allow string coercion for timezone field
        str_strip_whitespace = True
        
    @validator('timezone')
    def validate_timezone(cls, v):
        if v is None:
            return "UTC+5:30"  # Default to IST
        return str(v).strip()

class TransitRequest(BaseModel):
    birth_data: BirthData
    transit_date: str

class UserCreate(BaseModel):
    name: str
    phone: str
    password: str
    email: Optional[str] = None
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

class NumerologyRequest(BaseModel):
    name: str
    dob: str  # Format: YYYY-MM-DD
    target_date: Optional[str] = None  # For forecast

class NameOptimizationRequest(BaseModel):
    name: str
    system: str = 'chaldean'  # 'chaldean' or 'pythagorean'

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
SECRET_KEY = os.getenv('JWT_SECRET')
if not SECRET_KEY:
    raise ValueError("JWT_SECRET environment variable is required")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 43200  # 1 month (30 days)
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
                email TEXT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Add email column if it doesn't exist (backward compatibility)
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN email TEXT NULL')
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
        
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
                relation TEXT DEFAULT 'other',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (userid) REFERENCES users (userid),
                UNIQUE(userid, name, date, time, latitude, longitude)
            )
        ''')
        
        # Add relation column if it doesn't exist (backward compatibility)
        try:
            cursor.execute('ALTER TABLE birth_charts ADD COLUMN relation TEXT DEFAULT "other"')
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
        
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
    init_chat_tables()
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

class UserRegistrationWithBirth(BaseModel):
    name: str
    phone: str
    password: str
    email: str
    birth_details: Optional[BirthData] = None
    role: str = "user"

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
        "INSERT INTO users (name, phone, password, role, email) VALUES (?, ?, ?, ?, ?)",
        (user_data.name, user_data.phone, hashed_password, user_data.role, user_data.email)
    )
    conn.commit()
    
    cursor.execute("SELECT userid, name, phone, role, email FROM users WHERE phone = ?", (user_data.phone,))
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
            "role": user[3],
            "email": user[4] if len(user) > 4 else None
        },
        "self_birth_chart": None  # No birth chart in regular registration
    }

@app.post("/api/register-with-birth")
async def register_with_birth(user_data: UserRegistrationWithBirth):
    """Register user with birth details for mobile app"""
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT phone FROM users WHERE phone = ?", (user_data.phone,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Phone number already registered")
    
    # Create user
    hashed_password = hash_password(user_data.password)
    cursor.execute(
        "INSERT INTO users (name, phone, password, role, email) VALUES (?, ?, ?, ?, ?)",
        (user_data.name, user_data.phone, hashed_password, user_data.role, user_data.email)
    )
    conn.commit()
    
    cursor.execute("SELECT userid, name, phone, role, email FROM users WHERE phone = ?", (user_data.phone,))
    user = cursor.fetchone()
    
    # Create birth chart if provided
    birth_chart_data = None
    if user_data.birth_details:
        birth_data = user_data.birth_details
        if encryptor:
            enc_name = encryptor.encrypt(birth_data.name)
            enc_date = encryptor.encrypt(birth_data.date)
            enc_time = encryptor.encrypt(birth_data.time)
            enc_lat = encryptor.encrypt(str(birth_data.latitude))
            enc_lon = encryptor.encrypt(str(birth_data.longitude))
            enc_place = encryptor.encrypt(birth_data.place or '')
        else:
            enc_name, enc_date, enc_time = birth_data.name, birth_data.date, birth_data.time
            enc_lat, enc_lon, enc_place = str(birth_data.latitude), str(birth_data.longitude), birth_data.place or ''

        cursor.execute('''
            INSERT INTO birth_charts (userid, name, date, time, latitude, longitude, timezone, place, gender, relation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'self')
        ''', (user[0], enc_name, enc_date, enc_time, enc_lat, enc_lon, 
            birth_data.timezone, enc_place, birth_data.gender or '', 'self'))

        
        chart_id = cursor.lastrowid
        birth_chart_data = {
            'id': chart_id,
            'name': birth_data.name,
            'date': birth_data.date,
            'time': birth_data.time,
            'latitude': birth_data.latitude,
            'longitude': birth_data.longitude,
            'timezone': birth_data.timezone,
            'place': birth_data.place or '',
            'gender': birth_data.gender or '',
            'relation': 'self'
        }
    
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
            "role": user[3],
            "email": user[4] if len(user) > 4 else None
        },
        "self_birth_chart": birth_chart_data
    }

@app.post("/api/login")
async def login(user_data: UserLogin):
    conn = None
    try:
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        cursor.execute("SELECT userid, name, phone, password, role, email FROM users WHERE phone = ?", (user_data.phone,))
        user = cursor.fetchone()
        
        if not user:
            print(f"User not found for phone: {user_data.phone}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        password_valid = verify_password(user_data.password, user[3])
        
        if not password_valid:
            print(f"CRITICAL: Password verification failed for user: {user_data.phone}")
            print(f"Hash: {user[3][:20]}...")
            print(f"Hash format valid: {user[3].startswith('$2b$')}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Get user's active subscriptions
        cursor.execute('''
            SELECT sp.platform, sp.plan_name, sp.features, us.status, us.end_date
            FROM user_subscriptions us
            JOIN subscription_plans sp ON us.plan_id = sp.plan_id
            WHERE us.userid = ? AND us.status = 'active' AND us.end_date >= date('now')
        ''', (user[0],))
        
        subscriptions = cursor.fetchall()
        
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
        
        # Get user's "self" birth chart if exists
        cursor.execute('''
            SELECT id, name, date, time, latitude, longitude, timezone, place, gender, relation, created_at
            FROM birth_charts 
            WHERE userid = ? AND relation = 'self'
            ORDER BY created_at DESC 
            LIMIT 1
        ''', (user[0],))
        
        self_birth_chart = cursor.fetchone()
        birth_chart_data = None

        if self_birth_chart and encryptor:
            birth_chart_data = {
                'id': self_birth_chart[0],
                'name': encryptor.decrypt(self_birth_chart[1]),
                'date': encryptor.decrypt(self_birth_chart[2]),
                'time': encryptor.decrypt(self_birth_chart[3]),
                'latitude': float(encryptor.decrypt(str(self_birth_chart[4]))),
                'longitude': float(encryptor.decrypt(str(self_birth_chart[5]))),
                'timezone': self_birth_chart[6],
                'place': encryptor.decrypt(self_birth_chart[7] or ''),
                'gender': self_birth_chart[8] or '',
                'relation': self_birth_chart[9] or 'self',
                'created_at': self_birth_chart[10]
            }
        elif self_birth_chart:
            # No encryption
            birth_chart_data = {
                'id': self_birth_chart[0],
                'name': self_birth_chart[1],
                'date': self_birth_chart[2],
                'time': self_birth_chart[3],
                'latitude': self_birth_chart[4],
                'longitude': self_birth_chart[5],
                'timezone': self_birth_chart[6],
                'place': self_birth_chart[7] or '',
                'gender': self_birth_chart[8] or '',
                'relation': self_birth_chart[9] or 'self',
                'created_at': self_birth_chart[10]
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
                "email": user[5] if len(user) > 5 else None,
                "subscriptions": user_subscriptions
            },
            "self_birth_chart": birth_chart_data
        }
    except HTTPException:
        # Re-raise HTTP exceptions (like 401) without modification
        raise
    except Exception as e:
        import traceback
        error_details = {
            'error_type': type(e).__name__,
            'error_message': str(e),
            'traceback': traceback.format_exc()
        }
        print(f"Login error details: {error_details}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")
    finally:
        if conn:
            conn.close()

@app.get("/api/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.get("/api/admin/check-password-hashes")
async def check_password_hashes():
    """Admin endpoint to check password hash integrity"""
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT userid, phone, password, created_at FROM users")
    users = cursor.fetchall()
    conn.close()
    
    results = []
    for user in users:
        userid, phone, password_hash, created_at = user
        
        # Check hash format
        is_bcrypt = password_hash.startswith('$2b$')
        hash_length = len(password_hash)
        
        # Test with a dummy password to see if hash structure is valid
        try:
            bcrypt.checkpw(b'test', password_hash.encode('utf-8'))
            hash_structure_valid = True
        except Exception as e:
            hash_structure_valid = False
            
        results.append({
            'userid': userid,
            'phone': phone[-4:],  # Only show last 4 digits
            'created_at': created_at,
            'is_bcrypt_format': is_bcrypt,
            'hash_length': hash_length,
            'hash_structure_valid': hash_structure_valid,
            'hash_preview': password_hash[:20] + '...' if len(password_hash) > 20 else password_hash
        })
    
    return {'users': results, 'total_users': len(results)}

@app.post("/api/admin/test-password")
async def test_password(request: dict):
    """Test if a password works for a specific user"""
    phone = request.get('phone')
    test_passwords = request.get('passwords', [])
    
    if not phone or not test_passwords:
        raise HTTPException(status_code=400, detail="Phone and passwords array required")
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT password FROM users WHERE phone = ?", (phone,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    stored_hash = user[0]
    results = []
    
    for pwd in test_passwords:
        try:
            is_valid = verify_password(pwd, stored_hash)
            results.append({'password': pwd, 'valid': is_valid})
        except Exception as e:
            results.append({'password': pwd, 'valid': False, 'error': str(e)})
    
    return {'phone': phone[-4:], 'results': results}



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

@app.post("/api/send-registration-otp")
async def send_registration_otp(request: SendResetCode):
    import random
    import secrets
    from datetime import datetime, timedelta
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    # Check if phone already exists
    cursor.execute("SELECT userid FROM users WHERE phone = ?", (request.phone,))
    existing_user = cursor.fetchone()
    
    if existing_user:
        conn.close()
        raise HTTPException(status_code=409, detail="Phone number already registered")
    
    # Generate 6-digit code and secure token
    code = str(random.randint(100000, 999999))
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(minutes=10)  # 10 minute expiry
    
    # Store registration OTP code
    cursor.execute(
        "INSERT INTO password_reset_codes (phone, code, token, expires_at) VALUES (?, ?, ?, ?)",
        (request.phone, code, token, expires_at)
    )
    conn.commit()
    conn.close()
    
    # Send SMS with code
    from sms_service import sms_service
    sms_sent = sms_service.send_reset_code(request.phone, code)
    
    response = {
        "message": f"Registration OTP sent to {request.phone}"
    }
    
    # Development mode: show code if SMS failed and not in production
    is_development = os.getenv('ENVIRONMENT', 'development') == 'development'
    if not sms_sent and is_development:
        response["dev_code"] = code
        response["message"] += " (Development: SMS disabled, code shown below)"
    
    return response

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
    
    response = {
        "message": f"Reset code sent to {request.phone}",
        "user_name": user[1]
    }
    
    # Development mode: show code if SMS failed and not in production
    is_development = os.getenv('ENVIRONMENT', 'development') == 'development'
    if not sms_sent and is_development:
        response["dev_code"] = code
        response["message"] += " (Development: SMS disabled, code shown below)"
    
    return response

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

@app.get("/api/user/self-birth-chart")
async def get_self_birth_chart(current_user: User = Depends(get_current_user)):
    """Get user's self birth chart"""
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    # Debug: Check all charts for this user
    cursor.execute('''
        SELECT id, name, date, time, relation, created_at
        FROM birth_charts WHERE userid = ?
        ORDER BY created_at DESC
    ''', (current_user.userid,))
    
    all_charts = cursor.fetchall()
    print(f"DEBUG: User {current_user.userid} has {len(all_charts)} total charts:")
    for chart in all_charts:
        print(f"  Chart ID: {chart[0]}, Name: {chart[1]}, Relation: {chart[4]}, Created: {chart[5]}")
    
    # Look for chart with relation = 'self'
    cursor.execute('''
        SELECT id, name, date, time, latitude, longitude, timezone, place, gender
        FROM birth_charts WHERE userid = ? AND relation = 'self'
        ORDER BY created_at DESC LIMIT 1
    ''', (current_user.userid,))
    
    result = cursor.fetchone()
    print(f"DEBUG: Self chart query result: {result}")
    
    if not result:
        conn.close()
        return {"has_self_chart": False}

    # Decrypt data
    birth_chart_id = result[0]
    if encryptor:
        name = encryptor.decrypt(result[1])
        date = encryptor.decrypt(result[2])
        time = encryptor.decrypt(result[3])
        lat = float(encryptor.decrypt(str(result[4])))
        lon = float(encryptor.decrypt(str(result[5])))
        place = encryptor.decrypt(result[7])
    else:
        name, date, time = result[1], result[2], result[3]
        lat, lon, place = result[4], result[5], result[7]

    conn.close()
    return {
        "has_self_chart": True,
        "birth_chart_id": birth_chart_id,
        "name": name,
        "date": date,
        "time": time,
        "latitude": lat,
        "longitude": lon,
        "timezone": result[6],
        "place": place,
        "gender": result[8]
    }


@app.put("/api/user/self-birth-chart")
async def update_self_birth_chart(birth_data: BirthData, clear_existing: bool = True, current_user: User = Depends(get_current_user)):
    """Update user's self birth chart"""
    print(f"DEBUG: update_self_birth_chart called for user {current_user.userid}, clear_existing={clear_existing}")
    print(f"DEBUG: Birth data - name: {birth_data.name}, date: {birth_data.date}")
    
    conn = None
    try:
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        
        # Prepare encrypted data for comparison
        if encryptor:
            enc_name = encryptor.encrypt(birth_data.name)
            enc_date = encryptor.encrypt(birth_data.date)
            enc_time = encryptor.encrypt(birth_data.time)
            enc_lat = encryptor.encrypt(str(birth_data.latitude))
            enc_lon = encryptor.encrypt(str(birth_data.longitude))
            enc_place = encryptor.encrypt(birth_data.place or '')
        else:
            enc_name, enc_date, enc_time = birth_data.name, birth_data.date, birth_data.time
            enc_lat, enc_lon, enc_place = str(birth_data.latitude), str(birth_data.longitude), birth_data.place or ''
        
        # Find existing chart with matching encrypted data
        cursor.execute('''
            SELECT id FROM birth_charts 
            WHERE userid = ? AND name = ? AND date = ? AND time = ? 
            AND latitude = ? AND longitude = ?
        ''', (current_user.userid, enc_name, enc_date, enc_time, enc_lat, enc_lon))
        
        existing_chart = cursor.fetchone()
        
        if existing_chart:
            # Update existing chart to set relation = 'self'
            if clear_existing:
                cursor.execute("UPDATE birth_charts SET relation = 'other' WHERE userid = ? AND relation = 'self'", (current_user.userid,))
            
            cursor.execute("UPDATE birth_charts SET relation = 'self' WHERE id = ?", (existing_chart[0],))
            print(f"DEBUG: Updated existing chart {existing_chart[0]} to relation='self'")
            birth_chart_id = existing_chart[0]
        else:
            if clear_existing:
                # Only change other charts from 'self' to 'other', don't delete them
                cursor.execute("UPDATE birth_charts SET relation = 'other' WHERE userid = ? AND relation = 'self'", (current_user.userid,))
            
            cursor.execute('''
                INSERT INTO birth_charts (userid, name, date, time, latitude, longitude, timezone, place, gender, relation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (current_user.userid, enc_name, enc_date, enc_time, enc_lat, enc_lon, 
                birth_data.timezone, enc_place, birth_data.gender or '', 'self'))
            birth_chart_id = cursor.lastrowid
            print(f"DEBUG: Inserted new chart as relation='self' with id={birth_chart_id}")

        conn.commit()
        print(f"DEBUG: Successfully updated self birth chart for user {current_user.userid}, id={birth_chart_id}")
        return {"message": "Self birth chart updated successfully", "birth_chart_id": birth_chart_id}
        
    except sqlite3.Error as e:
        print(f"ERROR: Database error in update_self_birth_chart: {str(e)}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        print(f"ERROR: Exception in update_self_birth_chart: {str(e)}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update self birth chart: {str(e)}")
    finally:
        if conn:
            conn.close()

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

@app.get("/api/system-status")
async def system_status():
    try:
        import psutil
        import gc
        import threading
        
        process = psutil.Process()
        
        # Memory info
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        memory_percent = process.memory_percent()
        
        # CPU info
        cpu_percent = process.cpu_percent(interval=1)
        
        # System info
        system_memory = psutil.virtual_memory()
        system_cpu = psutil.cpu_percent(interval=1)
        
        # Thread info
        thread_count = threading.active_count()
        
        # Connection info
        connections = len(process.connections())
        
        # Force garbage collection
        gc.collect()
        
        return {
            "process": {
                "memory_mb": round(memory_mb, 2),
                "memory_percent": round(memory_percent, 2),
                "cpu_percent": cpu_percent,
                "threads": thread_count,
                "connections": connections
            },
            "system": {
                "memory_total_gb": round(system_memory.total / 1024 / 1024 / 1024, 2),
                "memory_used_percent": system_memory.percent,
                "cpu_percent": system_cpu
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/keepalive")
async def keepalive():
    """Simple endpoint to keep server alive"""
    return {"status": "alive", "timestamp": datetime.now().isoformat()}

@app.get("/api/resource-monitor")
async def resource_monitor():
    """Detailed resource monitoring"""
    try:
        import psutil
        import asyncio
        
        process = psutil.Process()
        
        # Get current event loop info
        loop = asyncio.get_event_loop()
        
        return {
            "memory_mb": round(process.memory_info().rss / 1024 / 1024, 2),
            "cpu_percent": process.cpu_percent(),
            "open_files": len(process.open_files()),
            "connections": len(process.connections()),
            "threads": process.num_threads(),
            "event_loop_running": loop.is_running(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/health-detailed")
async def health_detailed():
    """Detailed health check with resource usage"""
    try:
        import psutil
        process = psutil.Process()
        
        # Test database
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        conn.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "users": user_count,
            "memory_mb": round(process.memory_info().rss / 1024 / 1024, 2),
            "cpu_percent": process.cpu_percent(),
            "connections": len(process.connections()),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/calculate-chart-only")
async def calculate_chart_only(birth_data: BirthData, node_type: str = 'mean', current_user: User = Depends(get_current_user)):
    # Calculate chart without saving to database
    return await _calculate_chart_data(birth_data, node_type)

@app.post("/api/calculate-all-charts")
async def calculate_all_charts(birth_data: BirthData, current_user: User = Depends(get_current_user)):
    """Calculate all charts at once for instant switching"""
    try:
        # Calculate base chart
        base_chart = await _calculate_chart_data(birth_data, 'mean')
        
        # Calculate all divisional charts
        divisions = [9, 10, 12, 16, 20, 24, 30, 40, 45, 60]
        divisional_charts = {}
        
        for division in divisions:
            try:
                div_result = await calculate_divisional_chart({
                    'birth_data': birth_data.model_dump(),
                    'division': division
                }, current_user)
                divisional_charts[f'd{division}'] = div_result['divisional_chart']
            except Exception as e:
                print(f"Error calculating D{division}: {e}")
                continue
        
        # Calculate transit chart
        try:
            transit_request = TransitRequest(
                birth_data=birth_data,
                transit_date=datetime.now().strftime('%Y-%m-%d')
            )
            transit_chart = await calculate_transits(transit_request)
            divisional_charts['transit'] = transit_chart
        except Exception as e:
            print(f"Error calculating transit: {e}")
        
        return {
            'lagna': base_chart,
            'divisional_charts': divisional_charts,
            'calculated_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch calculation failed: {str(e)}")

@app.post("/api/calculate-chart")
async def calculate_chart(birth_data: BirthData, node_type: str = 'mean', current_user: User = Depends(get_current_user)):
    # CRITICAL: Validate coordinates before saving
    if not birth_data.latitude or not birth_data.longitude:
        raise HTTPException(status_code=400, detail="Valid coordinates required. Please select location from suggestions.")
    
    # Store birth data in database (update if exists for current user only)
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    if encryptor:
        enc_name = encryptor.encrypt(birth_data.name)
        enc_date = encryptor.encrypt(birth_data.date)
        enc_time = encryptor.encrypt(birth_data.time)
        enc_lat = encryptor.encrypt(str(birth_data.latitude))
        enc_lon = encryptor.encrypt(str(birth_data.longitude))
        enc_place = encryptor.encrypt(birth_data.place)
    else:
        enc_name, enc_date, enc_time = birth_data.name, birth_data.date, birth_data.time
        enc_lat, enc_lon, enc_place = str(birth_data.latitude), str(birth_data.longitude), birth_data.place

    # Check if chart exists for this user with same details
    cursor.execute('''
        SELECT id FROM birth_charts 
        WHERE userid = ? AND name = ? AND date = ? AND time = ? AND latitude = ? AND longitude = ?
    ''', (current_user.userid, enc_name, enc_date, enc_time, enc_lat, enc_lon))
    
    existing_chart = cursor.fetchone()
    
    if existing_chart:
        # Update existing chart for this user
        cursor.execute('''
            UPDATE birth_charts 
            SET timezone=?, place=?, gender=?, relation=?
            WHERE id=?
        ''', (birth_data.timezone, enc_place, birth_data.gender, birth_data.relation or 'other', existing_chart[0]))
    else:
        # Insert new chart for this user
        cursor.execute('''
            INSERT INTO birth_charts (userid, name, date, time, latitude, longitude, timezone, place, gender, relation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (current_user.userid, enc_name, enc_date, enc_time, enc_lat, enc_lon, 
            birth_data.timezone, enc_place, birth_data.gender, birth_data.relation or 'other'))

    conn.commit()
    conn.close()
    
    # Calculate and return chart data
    return await _calculate_chart_data(birth_data, node_type)

async def _calculate_chart_data(birth_data: BirthData, node_type: str = 'mean'):
    print(f"🔍 CHART CALCULATION DEBUG for {birth_data.name}:")
    print(f"📅 Date: {birth_data.date}")
    print(f"🕐 Time: {birth_data.time}")
    print(f"🌍 Location: {birth_data.latitude}, {birth_data.longitude}")
    print(f"⏰ Original Timezone: {birth_data.timezone}")
    # Calculate Julian Day with proper timezone handling
    time_parts = birth_data.time.split(':')
    hour = float(time_parts[0]) + float(time_parts[1])/60
    print(f"🕐 Parsed hour: {hour}")
    
    # Parse timezone offset (e.g., "UTC+5:30" -> 5.5, "UTC+5" -> 5.0)
    tz_offset = 0
    if birth_data.timezone.startswith('UTC'):
        tz_str = birth_data.timezone[3:]  # Remove 'UTC'
        print(f"⏰ Timezone string after UTC removal: '{tz_str}'")
        if tz_str:
            if ':' in tz_str:
                # Handle UTC+5:30 format
                sign = 1 if tz_str[0] == '+' else -1
                parts = tz_str[1:].split(':')
                tz_offset = sign * (float(parts[0]) + float(parts[1])/60)
                print(f"⏰ Parsed timezone offset (with minutes): {tz_offset}")
            else:
                # Handle UTC+5 format
                tz_offset = float(tz_str)
                print(f"⏰ Parsed timezone offset (hours only): {tz_offset}")
    else:
        # Default to IST for Indian coordinates
        if 6.0 <= birth_data.latitude <= 37.0 and 68.0 <= birth_data.longitude <= 97.0:
            tz_offset = 5.5
            print(f"⏰ Using default IST offset: {tz_offset}")
        else:
            print(f"⏰ Non-Indian coordinates, using offset: {tz_offset}")
    
    # Convert local time to UTC
    utc_hour = hour - tz_offset
    print(f"🌍 UTC hour calculated: {utc_hour} (local {hour} - offset {tz_offset})")
    
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
    
    # Add InduLagna
    from calculators.indu_lagna_calculator import InduLagnaCalculator
    indu_calc = InduLagnaCalculator({
        'ascendant': ascendant_sidereal,
        'planets': planets
    })
    indu_data = indu_calc.get_indu_lagna_data()
    planets['InduLagna'] = indu_data
    
    # Calculate house positions for all planets using Whole Sign system
    # In Whole Sign houses, each house is exactly 30 degrees starting from ascendant sign
    for planet_name in planets:
        planet_longitude = planets[planet_name]['longitude']
        planet_sign = int(planet_longitude / 30)
        
        # Calculate house number using Whole Sign system
        # House 1 starts from ascendant sign
        house_number = ((planet_sign - ascendant_sign) % 12) + 1
        planets[planet_name]['house'] = house_number
    
    print(f"✅ Chart calculation completed for {birth_data.name}")
    print(f"📊 Final Moon data: Sign {planets['Moon']['sign']} ({['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'][planets['Moon']['sign']]})")
    
    return {
        "planets": planets,
        "houses": houses,
        "ayanamsa": ayanamsa,
        "ascendant": ascendant_sidereal
    }

@app.post("/api/calculate-transits")
async def calculate_transits(request: TransitRequest):
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
            SELECT id, userid, name, date, time, latitude, longitude, timezone, created_at, place, gender, relation FROM birth_charts 
            WHERE userid = ? AND name LIKE ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (current_user.userid, search_pattern, limit))
    else:
        print("No search query, returning all charts")
        cursor.execute('SELECT id, userid, name, date, time, latitude, longitude, timezone, created_at, place, gender, relation FROM birth_charts WHERE userid = ? ORDER BY created_at DESC LIMIT ?', (current_user.userid, limit,))
    
    rows = cursor.fetchall()
    conn.close()

    charts = []
    for row in rows:
        if encryptor:
            chart = {
                'id': row[0],
                'userid': row[1],
                'name': encryptor.decrypt(row[2]),
                'date': encryptor.decrypt(row[3]),
                'time': encryptor.decrypt(row[4]),
                'latitude': float(encryptor.decrypt(str(row[5]))),
                'longitude': float(encryptor.decrypt(str(row[6]))),
                'timezone': row[7],
                'created_at': row[8],
                'place': encryptor.decrypt(row[9] if row[9] else ''),
                'gender': row[10] if row[10] else '',
                'relation': row[11] if len(row) > 11 and row[11] else 'other'
            }
        else:
            chart = {
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
                'gender': row[10] if row[10] else '',
                'relation': row[11] if len(row) > 11 and row[11] else 'other'
            }
        charts.append(chart)

    return {"charts": charts}


@app.put("/api/birth-charts/{chart_id}")
async def update_birth_chart(chart_id: int, birth_data: BirthData):
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    # cursor.execute('''
    #     UPDATE birth_charts 
    #     SET name=?, date=?, time=?, latitude=?, longitude=?, timezone=?, place=?, gender=?, relation=?
    #     WHERE id=?
    # ''', (birth_data.name, birth_data.date, birth_data.time, 
    #       birth_data.latitude, birth_data.longitude, birth_data.timezone, birth_data.place, birth_data.gender, birth_data.relation or 'other', chart_id))
    # AFTER:
    if encryptor:
        enc_name = encryptor.encrypt(birth_data.name)
        enc_date = encryptor.encrypt(birth_data.date)
        enc_time = encryptor.encrypt(birth_data.time)
        enc_lat = encryptor.encrypt(str(birth_data.latitude))
        enc_lon = encryptor.encrypt(str(birth_data.longitude))
        enc_place = encryptor.encrypt(birth_data.place)
    else:
        enc_name, enc_date, enc_time = birth_data.name, birth_data.date, birth_data.time
        enc_lat, enc_lon, enc_place = str(birth_data.latitude), str(birth_data.longitude), birth_data.place

    cursor.execute('''
        UPDATE birth_charts 
        SET name=?, date=?, time=?, latitude=?, longitude=?, timezone=?, place=?, gender=?, relation=?
        WHERE id=?
    ''', (enc_name, enc_date, enc_time, enc_lat, enc_lon, 
        birth_data.timezone, enc_place, birth_data.gender, birth_data.relation or 'other', chart_id))

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
    try:
        from panchang.panchang_calculator import PanchangCalculator
        
        birth_data = request.birth_data
        panchang_calc = PanchangCalculator()
        
        # Validate required fields
        if not hasattr(birth_data, 'latitude') or not hasattr(birth_data, 'longitude'):
            raise HTTPException(status_code=422, detail="Missing latitude or longitude in birth_data")
        
        # Handle timezone conversion
        timezone = birth_data.timezone if birth_data.timezone else 'UTC+5:30'
        if isinstance(timezone, (int, float)):
            if timezone >= 0:
                hours = int(timezone)
                minutes = int((timezone - hours) * 60)
                timezone = f'UTC+{hours}:{minutes:02d}'
            else:
                hours = int(abs(timezone))
                minutes = int((abs(timezone) - hours) * 60)
                timezone = f'UTC-{hours}:{minutes:02d}'
        
        # Use comprehensive panchang calculation
        panchang_data = panchang_calc.calculate_panchang(
            request.transit_date,
            float(birth_data.latitude),
            float(birth_data.longitude),
            str(timezone)
        )
        
        return panchang_data
        
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Invalid data format: {str(e)}")
    except AttributeError as e:
        raise HTTPException(status_code=422, detail=f"Missing required field: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating panchang: {str(e)}")

@app.post("/api/calculate-birth-panchang")
async def calculate_birth_panchang(birth_data: BirthData):
    try:
        # Use existing calculate_panchang with birth date as transit date
        request = TransitRequest(
            birth_data=birth_data,
            transit_date=birth_data.date
        )
        return await calculate_panchang(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating birth panchang: {str(e)}")



@app.post("/api/calculate-divisional-chart")
async def calculate_divisional_chart(request: dict, current_user: User = Depends(get_current_user)):
    """Calculate accurate divisional charts using proper Vedic formulas"""
    birth_data = BirthData(**request['birth_data'])
    division_number = request.get('division', 9)
    

    
    # First get the basic chart without saving to database
    chart_data = await _calculate_chart_data(birth_data, 'mean')
    
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
    try:
        from shared.dasha_calculator import DashaCalculator
        
        print(f"🔍 Dasha calculation for: {birth_data.name}, timezone: {birth_data.timezone}")
        
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
        
        print(f"✅ Dasha calculation successful, got {len(dasha_data.get('maha_dashas', []))} maha dashas")
        
        # Format maha_dashas for API response
        maha_dashas = []
        for maha in dasha_data.get('maha_dashas', []):
            maha_dashas.append({
                'planet': maha['planet'],
                'start': maha['start'].strftime('%Y-%m-%d'),
                'end': maha['end'].strftime('%Y-%m-%d'),
                'years': maha['years']
            })
        
        result = {
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
        
        print(f"📤 Returning dasha result with {len(result['maha_dashas'])} periods")
        return result
        
    except Exception as e:
        print(f"❌ Dasha calculation error: {str(e)}")
        import traceback
        print(f"📍 Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Dasha calculation failed: {str(e)}")

@app.post("/api/calculate-cascading-dashas")
async def calculate_cascading_dashas(request: dict):
    """Calculate complete cascading dasha hierarchy for a given date"""
    try:
        from shared.dasha_calculator import DashaCalculator
        
        print(f"🔍 Cascading dasha request: {request.keys()}")
        
        birth_data = BirthData(**request['birth_data'])
        target_date = datetime.strptime(request.get('target_date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d')
        
        print(f"📊 Processing cascading dashas for: {birth_data.name}, timezone: {birth_data.timezone}")
        
    except Exception as e:
        print(f"❌ Input validation error: {str(e)}")
        return {
            'maha_dashas': [],
            'antar_dashas': [],
            'pratyantar_dashas': [],
            'sookshma_dashas': [],
            'prana_dashas': [],
            'current_dashas': {},
            'error': f'Input validation error: {str(e)}'
        }
    
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
    print(f"🔄 Calling calculate_current_dashas with target_date: {target_date}")
    current_dashas = calculator.calculate_current_dashas(birth_dict, target_date)
    print(f"📊 Current dashas result keys: {list(current_dashas.keys())}")
    print(f"📊 Maha dashas in result: {len(current_dashas.get('maha_dashas', []))}")
    
    if current_dashas.get('maha_dashas'):
        print(f"📊 First maha dasha: {current_dashas['maha_dashas'][0]}")
    
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
    
    print(f"📈 Got {len(maha_dashas)} maha dashas from calculator")
    
    result = {
        'maha_dashas': maha_dashas,
        'antar_dashas': [],
        'pratyantar_dashas': [],
        'sookshma_dashas': [],
        'prana_dashas': [],
        'current_dashas': current_dashas.get('current_dashas', {})
    }
    
    print(f"🎯 Current maha found: {current_maha['planet'] if current_maha else 'None'}")
    
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
        print(f"🔄 Calculating antar dashas for {current_maha['planet']}")
        antar_result = await calculate_sub_dashas(antar_request)
        result['antar_dashas'] = antar_result['sub_dashas']
        print(f"📊 Got {len(result['antar_dashas'])} antar dashas")
        
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
                    print(f"🎪 Got {len(result['prana_dashas'])} prana dashas")
    
    print(f"✅ Cascading dasha calculation complete. Returning {len(result['maha_dashas'])} maha, {len(result['antar_dashas'])} antar, {len(result['pratyantar_dashas'])} pratyantar, {len(result['sookshma_dashas'])} sookshma, {len(result['prana_dashas'])} prana dashas")
    return result

@app.post("/api/calculate-sub-dashas")
async def calculate_sub_dashas(request: dict):
    """Calculate sub-dashas (Antar, Pratyantar, Sookshma, Prana) for given parent dasha"""
    try:
        from event_prediction.config import DASHA_PERIODS, PLANET_ORDER
    except ImportError:
        DASHA_PERIODS = {
            'Ketu': 7, 'Venus': 20, 'Sun': 6, 'Moon': 10, 'Mars': 7,
            'Rahu': 18, 'Jupiter': 16, 'Saturn': 19, 'Mercury': 17
        }
        PLANET_ORDER = ['Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury']
    
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
    from calculators.ashtakavarga import AshtakavargaCalculator
    
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
        chart_data = await calculate_transits(transit_request)
    else:
        # For birth charts (lagna, navamsa), use birth positions - DON'T SAVE TO DATABASE
        chart_data = await _calculate_chart_data(birth_data, 'mean')
    
    calculator = AshtakavargaCalculator(birth_data, chart_data)
    
    sarva = calculator.calculate_sarvashtakavarga()
    analysis = calculator.get_ashtakavarga_analysis(chart_type)
    
    # Format Ashtakvarga data for chart display
    chart_ashtakavarga = {}
    ascendant_sign = int(chart_data.get('ascendant', 0) / 30) if chart_data.get('ascendant') else 0
    
    for sign_num in range(12):
        house_num = ((sign_num - ascendant_sign) % 12) + 1
        bindus = sarva['sarvashtakavarga'].get(str(sign_num), 0)
        chart_ashtakavarga[str(house_num)] = {
            'bindus': bindus,
            'sign': sign_num,
            'strength': 'Strong' if bindus >= 30 else 'Weak' if bindus <= 25 else 'Moderate'
        }
    
    return {
        "ashtakavarga": sarva,
        "analysis": analysis,
        "chart_type": chart_type,
        "chart_data": chart_data,  # Include chart_data for oracle calculations
        "chart_ashtakavarga": chart_ashtakavarga  # Formatted for chart widget
    }

@app.post("/api/ashtakavarga/transit-analysis")
async def get_transit_ashtakavarga(request: dict, current_user: User = Depends(get_current_user)):
    """Get Ashtakavarga analysis for transit date"""
    from calculators.ashtakavarga_transit import AshtakavargaTransitCalculator
    
    birth_data = BirthData(**request['birth_data'])
    transit_date = request.get('transit_date', datetime.now().strftime('%Y-%m-%d'))
    
    chart_data = await _calculate_chart_data(birth_data, 'mean')
    calculator = AshtakavargaTransitCalculator(birth_data, chart_data)
    
    transit_av = calculator.calculate_transit_ashtakavarga(transit_date)
    recommendations = calculator.get_transit_recommendations(transit_date)
    comparison = calculator.compare_birth_transit_strength(transit_date)
    
    return {
        "transit_date": transit_date,
        "transit_ashtakavarga": transit_av,
        "recommendations": recommendations,
        "birth_transit_comparison": comparison
    }

@app.post("/api/ashtakavarga/monthly-forecast")
async def get_monthly_ashtakavarga_forecast(request: dict, current_user: User = Depends(get_current_user)):
    """Get monthly Ashtakavarga forecast"""
    from calculators.ashtakavarga_transit import AshtakavargaTransitCalculator
    
    birth_data = BirthData(**request['birth_data'])
    start_date = datetime.strptime(request.get('start_date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d')
    
    chart_data = await _calculate_chart_data(birth_data, 'mean')
    calculator = AshtakavargaTransitCalculator(birth_data, chart_data)
    
    forecast = []
    for i in range(0, 30, 7):
        check_date = start_date + timedelta(days=i)
        recommendations = calculator.get_transit_recommendations(check_date.strftime('%Y-%m-%d'))
        
        forecast.append({
            "date": check_date.strftime('%Y-%m-%d'),
            "week": f"Week {i//7 + 1}",
            "strength": recommendations['transit_strength'],
            "key_activities": recommendations['favorable_activities'][:2] if recommendations['favorable_activities'] else []
        })
    
    return {
        "forecast_period": f"{start_date.strftime('%Y-%m-%d')} to {(start_date + timedelta(days=30)).strftime('%Y-%m-%d')}",
        "weekly_forecast": forecast
    }

@app.post("/api/ashtakavarga/predict-events")
async def predict_ashtakavarga_events(request: dict, current_user: User = Depends(get_current_user)):
    """Predict events using Ashtakavarga for specific year"""
    from calculators.ashtakavarga_events import AshtakavargaEventPredictor
    
    birth_data = BirthData(**request['birth_data'])
    year = request.get('year', datetime.now().year)
    
    chart_data = await _calculate_chart_data(birth_data, 'mean')
    predictor = AshtakavargaEventPredictor(birth_data, chart_data)
    
    events = predictor.predict_events_for_year(year)
    
    return {
        "year": year,
        "events": events,
        "total_events": len(events)
    }

@app.post("/api/ashtakavarga/predict-specific-event")
async def predict_specific_event(request: dict, current_user: User = Depends(get_current_user)):
    """Predict timing for specific events like marriage, career, etc."""
    from calculators.ashtakavarga_events import AshtakavargaEventPredictor
    
    birth_data = BirthData(**request['birth_data'])
    event_type = request.get('event_type', 'marriage')
    start_year = request.get('start_year', datetime.now().year)
    end_year = request.get('end_year', start_year + 5)
    
    chart_data = await _calculate_chart_data(birth_data, 'mean')
    predictor = AshtakavargaEventPredictor(birth_data, chart_data)
    
    predictions = predictor.predict_specific_event_timing(event_type, start_year, end_year)
    
    return {
        "event_type": event_type,
        "period": f"{start_year}-{end_year}",
        "predictions": predictions
    }

@app.post("/api/ashtakavarga/daily-strength")
async def get_daily_ashtakavarga_strength(request: dict, current_user: User = Depends(get_current_user)):
    """Get Ashtakavarga strength for specific date"""
    from calculators.ashtakavarga_events import AshtakavargaEventPredictor
    
    birth_data = BirthData(**request['birth_data'])
    date = request.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    chart_data = await _calculate_chart_data(birth_data, 'mean')
    predictor = AshtakavargaEventPredictor(birth_data, chart_data)
    
    daily_analysis = predictor.get_daily_ashtakavarga_strength(date)
    
    return daily_analysis

@app.post("/api/ashtakavarga/oracle-insight")
async def get_ashtakavarga_oracle_insight(request: dict, current_user: User = Depends(get_current_user)):
    """Generate Gemini-powered Ashtakvarga Oracle insights"""
    try:
        from calculators.ashtakvarga_oracle import get_oracle_instance
        
        birth_data = request['birth_data']
        ashtakvarga_data = request['ashtakvarga_data']
        date = request.get('date', datetime.now().strftime('%Y-%m-%d'))
        query_type = request.get('query_type', 'general')
        
        oracle = get_oracle_instance()
        complete_oracle = oracle.generate_complete_oracle(birth_data, ashtakvarga_data, date, query_type)
        
        # Return complete oracle data including timeline_events
        return complete_oracle
        
    except Exception as e:
        print(f"Oracle insight error: {str(e)}")
        return {
            "oracle_message": "The cosmic energies are aligning. Your Ashtakvarga reveals hidden patterns of strength and opportunity.",
            "power_actions": [
                {"type": "do", "text": "Focus on morning activities"},
                {"type": "do", "text": "Wear bright colors today"},
                {"type": "avoid", "text": "Avoid major decisions after sunset"}
            ],
            "cosmic_strength": 65,
            "pillar_insights": [f"Sign {i+1} holds cosmic significance in your chart." for i in range(12)]
        }

# Timeline endpoint removed - frontend handles timeline data from oracle-insight response

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
async def get_nakshatras_public():
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
        init_chat_tables()
        print("House combinations and chat history databases initialized")
    except Exception as e:
        print(f"Warning: Could not initialize additional databases: {e}")
    
    # Timezone auto-fix disabled - manual correction required

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

@app.post("/api/admin/fix-timezones")
async def fix_database_timezones(current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    # Fix problematic formats with proper IST handling
    cursor.execute("""SELECT id, latitude, longitude, timezone FROM birth_charts 
                     WHERE timezone LIKE '%/%' OR timezone = 'Asia/Kolkata' 
                     OR timezone LIKE 'UTC+%:%' OR timezone LIKE 'UTC-%:%'
                     OR timezone LIKE 'UTC+%.%:%' OR timezone LIKE 'UTC-%.%:%'""")
    charts = cursor.fetchall()
    
    fixed_count = 0
    for chart_id, lat, lng, old_tz in charts:
        if lat and lng:
            # Calculate proper timezone with 30-minute precision
            offset = lng / 15.0
            hours = int(offset)
            minutes = int((abs(offset) - abs(hours)) * 60)
            
            if minutes == 30:
                new_tz = f"UTC{'+' if offset >= 0 else '-'}{abs(hours)}:30"
            else:
                new_tz = f"UTC{'+' if offset >= 0 else '-'}{abs(hours)}"
            
            cursor.execute("UPDATE birth_charts SET timezone = ? WHERE id = ?", (new_tz, chart_id))
            fixed_count += 1
    
    conn.commit()
    conn.close()
    
    return {"message": f"Fixed {fixed_count} timezone records"}

@app.post("/api/calculate-kalchakra-dasha")
async def calculate_kalchakra_dasha(request: dict):
    """Calculate Kalchakra Dasha periods"""
    try:
        # Validate request structure
        if not request or 'birth_data' not in request:
            return {"system": "Kalchakra", "error": "Missing birth_data in request"}
        
        # Get manushya rule option (default: always-reverse for BPHS authenticity)
        manushya_rule = request.get('manushya_rule', 'always-reverse')
        
        # Import calculator
        from calculators.bphs_kalachakra_calculator import BPHSKalachakraCalculator
        
        # Validate and parse birth data
        birth_data = BirthData(**request['birth_data'])
        
        # Convert timezone to offset if needed
        timezone_offset = birth_data.timezone
        if isinstance(timezone_offset, str):
            if timezone_offset.startswith('UTC'):
                tz_str = timezone_offset[3:]
                if tz_str and ':' in tz_str:
                    sign = 1 if tz_str[0] == '+' else -1
                    parts = tz_str[1:].split(':')
                    timezone_offset = sign * (float(parts[0]) + float(parts[1])/60)
                else:
                    timezone_offset = 5.5  # Default IST
            else:
                timezone_offset = 5.5
        
        birth_dict = {
            'date': birth_data.date,
            'time': birth_data.time,
            'timezone_offset': timezone_offset
        }
        
        # Parse target date if provided
        target_date = None
        if request.get('target_date'):
            from datetime import datetime as dt
            target_date = dt.strptime(request['target_date'], '%Y-%m-%d')
        
        # Initialize Swiss Ephemeris first
        import swisseph as swe
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        
        # Initialize calculator and compute
        calculator = BPHSKalachakraCalculator()
        kalchakra_data = calculator.calculate_kalchakra_dasha(birth_dict, target_date)
        
        if 'error' in kalchakra_data:
            return kalchakra_data
        
        # Format mahadashas for response
        maha_dashas = []
        for maha in kalchakra_data.get('mahadashas', []):
            maha_dashas.append({
                'planet': maha.get('name', maha.get('planet', 'Unknown')),
                'start': maha.get('start', maha.get('start_iso', maha.get('start_date', ''))),
                'end': maha.get('end', maha.get('end_iso', maha.get('end_date', ''))),
                'years': maha['years']
            })
        
        # Format periods for mobile app with current marking
        from datetime import datetime, timezone
        current_date = datetime.now(timezone.utc)
        
        periods = []
        for i, maha in enumerate(kalchakra_data.get('mahadashas', [])):
            # Check if this is the current period
            try:
                start_date = datetime.fromisoformat(maha['start'].replace('Z', '+00:00'))
                end_date = datetime.fromisoformat(maha['end'].replace('Z', '+00:00'))
                is_current = start_date <= current_date < end_date
            except:
                is_current = False
            
            periods.append({
                'name': maha.get('name', 'Unknown'),
                'sign': maha.get('sign', 1),
                'start_date': maha['start'],
                'end_date': maha['end'],
                'duration_years': maha['years'],
                'gati': maha.get('gati', 'Normal'),
                'current': is_current
            })
        
        # No need for deity classification in sign-based system
        
        return {
            "system": kalchakra_data.get('system', 'Kalchakra (BPHS Authentic)'),
            "mahadashas": kalchakra_data.get('mahadashas', []),
            "current_mahadasha": kalchakra_data.get('current_mahadasha', {}),
            "current_antardasha": kalchakra_data.get('current_antardasha', {}),
            "all_antardashas": kalchakra_data.get('all_antardashas', []),
            "nakshatra": kalchakra_data.get('nakshatra', 1),
            "pada": kalchakra_data.get('pada', 1),
            "direction": kalchakra_data.get('direction', 'Savya'),
            "cycle_len": kalchakra_data.get('cycle_len', 100),
            "deha": kalchakra_data.get('deha', 'Aries'),
            "jeeva": kalchakra_data.get('jeeva', 'Pisces'),
            "sequence": kalchakra_data.get('sequence_names', [])
        }
        
    except ImportError as e:
        return {"system": "Kalchakra", "error": f"Calculator import failed: {str(e)}"}
    except Exception as e:
        import traceback
        print(f"Kalchakra calculation error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return {"system": "Kalchakra", "error": f"Calculation failed: {str(e)}"}

@app.post("/api/jaimini-antardashas")
async def get_jaimini_antardashas(request: dict):
    """Get all antardashas for a mahadasha"""
    try:
        from calculators.jaimini_kalachakra_calculator import JaiminiKalachakraCalculator
        from calculators.chart_calculator import ChartCalculator
        
        # Get chart data from session or calculate
        birth_data = BirthData(**request.get('birth_data', {}))
        chart_calc = ChartCalculator({})
        chart_data = chart_calc.calculate_chart(birth_data)
        
        calculator = JaiminiKalachakraCalculator(chart_data)
        antardashas = calculator.get_all_antardashas_for_maha(
            request['maha_sign'],
            request['maha_start_jd'],
            request['maha_end_jd']
        )
        
        return {"antardashas": antardashas}
        
    except Exception as e:
        return {"error": f"Antardasha calculation failed: {str(e)}"}

@app.post("/api/jaimini-antar-details")
async def get_jaimini_antar_details(request: dict):
    """Get detailed information for an antardasha"""
    try:
        from calculators.jaimini_kalachakra_calculator import JaiminiKalachakraCalculator
        from calculators.chart_calculator import ChartCalculator
        
        # Get chart data from session or calculate
        birth_data = BirthData(**request.get('birth_data', {}))
        chart_calc = ChartCalculator({})
        chart_data = chart_calc.calculate_chart(birth_data)
        
        calculator = JaiminiKalachakraCalculator(chart_data)
        details = calculator.get_antardasha_details(
            request['maha_sign'],
            request['antar_sign']
        )
        
        return details
        
    except Exception as e:
        return {"error": f"Antar details calculation failed: {str(e)}"}

@app.post("/api/calculate-jaimini-kalchakra-dasha")
async def calculate_jaimini_kalchakra_dasha(request: dict):
    """Calculate Jaimini Kalchakra Dasha with reversals and jumps"""
    try:
        from calculators.jaimini_kalachakra_calculator import JaiminiKalachakraCalculator
        from calculators.chart_calculator import ChartCalculator
        
        # Validate request
        if not request or 'birth_data' not in request:
            return {"system": "Jaimini Kalchakra", "error": "Missing birth_data in request"}
        
        # Parse birth data
        birth_data = BirthData(**request['birth_data'])
        
        # Convert timezone to offset
        timezone_offset = birth_data.timezone
        if isinstance(timezone_offset, str):
            if timezone_offset.startswith('UTC'):
                tz_str = timezone_offset[3:]
                if tz_str and ':' in tz_str:
                    sign = 1 if tz_str[0] == '+' else -1
                    parts = tz_str[1:].split(':')
                    timezone_offset = sign * (float(parts[0]) + float(parts[1])/60)
                else:
                    timezone_offset = 5.5
            else:
                timezone_offset = 5.5
        
        # Calculate birth chart first
        chart_calc = ChartCalculator({})
        chart_data = chart_calc.calculate_chart(birth_data)
        
        # Initialize Jaimini calculator
        calculator = JaiminiKalachakraCalculator(chart_data)
        
        # Calculate Jaimini Kalchakra
        birth_dict = {
            'date': birth_data.date,
            'time': birth_data.time,
            'timezone_offset': timezone_offset
        }
        
        # Use current date for marking current periods
        from datetime import datetime, timezone
        current_date = datetime.now(timezone.utc)
        
        jaimini_data = calculator.calculate_jaimini_kalachakra_dasha(birth_dict, current_date)
        
        print(f"DEBUG: Jaimini calculation result keys: {list(jaimini_data.keys()) if jaimini_data else 'None'}")
        
        if 'error' in jaimini_data:
            print(f"ERROR: Jaimini calculation failed: {jaimini_data['error']}")
            return jaimini_data
        
        if not jaimini_data.get('mahadashas'):
            print("ERROR: No mahadashas returned from Jaimini calculation")
            return {"system": "Jaimini Kalchakra", "error": "No mahadashas calculated"}
        
        print(f"DEBUG: Found {len(jaimini_data.get('mahadashas', []))} mahadashas")
        
        periods = []
        current_period_found = False
        
        for maha in jaimini_data.get('mahadashas', []):
            # Parse dates for comparison
            try:
                start_date = datetime.fromisoformat(maha['start_iso'].replace('Z', '+00:00'))
                end_date = datetime.fromisoformat(maha['end_iso'].replace('Z', '+00:00'))
                
                # Check if this is the current period (only mark first one found)
                is_current = not current_period_found and start_date <= current_date < end_date
                if is_current:
                    current_period_found = True
            except Exception as e:
                print(f"Date parsing error: {e}")
                is_current = False
            
            period_data = {
                'id': f"{maha['sign_name']}_{maha['start_iso']}",  # Unique ID
                'sign': maha['sign_name'],
                'start': maha['start_iso'],
                'end': maha['end_iso'],
                'planet': maha['sign_name'],
                'start_date': maha['start_iso'],
                'end_date': maha['end_iso'],
                'duration_years': maha['years'],
                'chakra': maha['chakra'],
                'direction': maha['direction'],
                'cycle': maha.get('cycle', 1),
                'current': is_current
            }
            periods.append(period_data)
            if is_current:
                print(f"DEBUG: Current Jaimini period found: {maha['sign_name']} ({maha['start_iso']} to {maha['end_iso']})")
        
        current_count = len([p for p in periods if p['current']])
        print(f"DEBUG: Total Jaimini periods: {len(periods)}, Current periods: {current_count}")
        
        if current_count == 0:
            print("WARNING: No current period found in Jaimini Kalchakra")
        elif current_count > 1:
            print(f"WARNING: Multiple current periods found: {current_count}")
        
        return {
            "system": jaimini_data.get('system', 'Jaimini Kalchakra'),
            "periods": periods,
            "current_dashas": {
                "mahadasha": jaimini_data.get('current_mahadasha', {}),
                "antardasha": jaimini_data.get('current_antardasha', {})
            },
            "maha_dashas": periods,  # Add this for cascading dasha compatibility
            "janma_rashi": jaimini_data.get('janma_rashi_name', 'Aries'),
            "chakra1_direction": jaimini_data.get('chakra1_direction', 'Forward'),
            "chakra2_direction": jaimini_data.get('chakra2_direction', 'Backward'),
            "chakra1_signs": jaimini_data.get('chakra1_signs', []),
            "chakra2_signs": jaimini_data.get('chakra2_signs', []),
            "skipped_rashis": jaimini_data.get('skipped_rashis', []),
            "reversals": jaimini_data.get('reversals', []),
            "jumps": jaimini_data.get('jumps', []),
            "total_cycle_years": jaimini_data.get('total_cycle_years', 100),
            "predictions": jaimini_data.get('predictions', {}),
            "interpretations": jaimini_data.get('interpretations', {}),
            "cards": jaimini_data.get('cards', {})
        }
        
    except ImportError as e:
        return {"system": "Jaimini Kalchakra", "error": f"Calculator import failed: {str(e)}"}
    except Exception as e:
        import traceback
        print(f"Jaimini Kalchakra calculation error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return {"system": "Jaimini Kalchakra", "error": f"Calculation failed: {str(e)}"}

@app.post("/api/calculate-jaimini-kalchakra-cascading")
async def calculate_jaimini_kalchakra_cascading(request: dict):
    """Calculate cascading Jaimini Kalchakra dasha hierarchy for a given date"""
    try:
        from calculators.jaimini_kalachakra_calculator import JaiminiKalachakraCalculator
        from calculators.chart_calculator import ChartCalculator
        
        birth_data = BirthData(**request['birth_data'])
        target_date_str = request.get('target_date', datetime.now().strftime('%Y-%m-%d'))
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d')
        
        # Calculate birth chart
        chart_calc = ChartCalculator({})
        chart_data = chart_calc.calculate_chart(birth_data)
        
        # Initialize Jaimini calculator
        calculator = JaiminiKalachakraCalculator(chart_data)
        
        # Calculate Jaimini Kalchakra
        timezone_offset = birth_data.timezone
        if isinstance(timezone_offset, str):
            if timezone_offset.startswith('UTC'):
                tz_str = timezone_offset[3:]
                if tz_str and ':' in tz_str:
                    sign = 1 if tz_str[0] == '+' else -1
                    parts = tz_str[1:].split(':')
                    timezone_offset = sign * (float(parts[0]) + float(parts[1])/60)
                else:
                    timezone_offset = 5.5
            else:
                timezone_offset = 5.5
        
        birth_dict = {
            'date': birth_data.date,
            'time': birth_data.time,
            'timezone_offset': timezone_offset
        }
        
        jaimini_data = calculator.calculate_jaimini_kalachakra_dasha(birth_dict, target_date)
        
        if 'error' in jaimini_data:
            return {
                'maha_dashas': [],
                'antar_dashas': [],
                'pratyantar_dashas': [],
                'sookshma_dashas': [],
                'prana_dashas': [],
                'current_dashas': {},
                'error': jaimini_data['error']
            }
        
        # Format maha dashas
        maha_dashas = []
        for maha in jaimini_data.get('mahadashas', []):
            try:
                start_date = datetime.fromisoformat(maha['start_iso'].replace('Z', '+00:00'))
                end_date = datetime.fromisoformat(maha['end_iso'].replace('Z', '+00:00'))
                is_current = start_date <= target_date < end_date
            except:
                is_current = False
            
            maha_dashas.append({
                'planet': maha['sign_name'],  # Use sign name as "planet" for compatibility
                'sign': maha['sign_name'],
                'start': maha['start_iso'],
                'end': maha['end_iso'],
                'current': is_current,
                'years': maha['years'],
                'chakra': maha['chakra'],
                'direction': maha['direction']
            })
        
        # Find current maha for antardasha calculation
        current_maha = None
        for maha in maha_dashas:
            if maha['current']:
                current_maha = maha
                break
        
        result = {
            'maha_dashas': maha_dashas,
            'antar_dashas': [],
            'pratyantar_dashas': [],
            'sookshma_dashas': [],
            'prana_dashas': [],
            'current_dashas': {
                'mahadasha': jaimini_data.get('current_mahadasha', {}),
                'antardasha': jaimini_data.get('current_antardasha', {})
            }
        }
        
        # Calculate antardasha if current maha exists
        if current_maha:
            try:
                antar_request = {
                    'birth_data': birth_dict,
                    'maha_sign': current_maha['sign'],
                    'target_date': target_date_str
                }
                antar_response = await calculate_jaimini_kalchakra_antardasha(antar_request)
                
                if 'antar_periods' in antar_response:
                    antar_dashas = []
                    for antar in antar_response['antar_periods']:
                        antar_dashas.append({
                            'planet': antar['sign'],
                            'sign': antar['sign'],
                            'start': antar['start_date'],
                            'end': antar['end_date'],
                            'current': antar['current'],
                            'years': antar['years']
                        })
                    result['antar_dashas'] = antar_dashas
            except Exception as e:
                print(f"Antardasha calculation error: {e}")
        
        return result
        
    except Exception as e:
        import traceback
        print(f"Jaimini cascading calculation error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return {
            'maha_dashas': [],
            'antar_dashas': [],
            'pratyantar_dashas': [],
            'sookshma_dashas': [],
            'prana_dashas': [],
            'current_dashas': {},
            'error': f'Calculation failed: {str(e)}'
        }

@app.post("/api/calculate-jaimini-kalchakra-antardasha")
async def calculate_jaimini_kalchakra_antardasha(request: dict):
    """Calculate Jaimini Kalchakra antardasha periods for selected mahadasha"""
    try:
        from calculators.jaimini_kalachakra_calculator import JaiminiKalachakraCalculator
        from calculators.chart_calculator import ChartCalculator
        from datetime import datetime, timezone
        
        birth_data = BirthData(**request['birth_data'])
        maha_sign = request['maha_sign']
        
        # Convert timezone to offset
        timezone_offset = birth_data.timezone
        if isinstance(timezone_offset, str):
            if timezone_offset.startswith('UTC'):
                tz_str = timezone_offset[3:]
                if tz_str and ':' in tz_str:
                    sign = 1 if tz_str[0] == '+' else -1
                    parts = tz_str[1:].split(':')
                    timezone_offset = sign * (float(parts[0]) + float(parts[1])/60)
                else:
                    timezone_offset = 5.5
            else:
                timezone_offset = 5.5
        
        # Calculate birth chart
        chart_calc = ChartCalculator({})
        chart_data = chart_calc.calculate_chart(birth_data)
        
        # Initialize calculator
        calculator = JaiminiKalachakraCalculator(chart_data)
        
        birth_dict = {
            'date': birth_data.date,
            'time': birth_data.time,
            'timezone_offset': timezone_offset
        }
        
        # Get full Jaimini data
        jaimini_data = calculator.calculate_jaimini_kalachakra_dasha(birth_dict)
        
        if 'error' in jaimini_data:
            return jaimini_data
        
        # Find the current mahadasha (the one that contains current date)
        current_date = datetime.now(timezone.utc)
        selected_maha = None
        for maha in jaimini_data.get('mahadashas', []):
            start_date = datetime.fromisoformat(maha['start_iso'].replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(maha['end_iso'].replace('Z', '+00:00'))
            if maha['sign_name'] == maha_sign and start_date <= current_date < end_date:
                selected_maha = maha
                break
        
        # If no current period found, find the first future period with this sign
        if not selected_maha:
            for maha in jaimini_data.get('mahadashas', []):
                start_date = datetime.fromisoformat(maha['start_iso'].replace('Z', '+00:00'))
                if maha['sign_name'] == maha_sign and start_date > current_date:
                    selected_maha = maha
                    break
        
        if not selected_maha:
            return {"error": "Selected mahadasha not found"}
        
        # Calculate antardashas for this mahadasha
        full_sequence = []
        for maha in jaimini_data.get('mahadashas', []):
            full_sequence.append(maha['sign'])
        
        # Generate antardasha sequence starting from selected sign
        maha_sign_num = selected_maha['sign']
        try:
            start_idx = full_sequence.index(maha_sign_num)
        except ValueError:
            start_idx = 0
        
        antar_sequence = []
        for i in range(len(full_sequence)):
            antar_sequence.append(full_sequence[(start_idx + i) % len(full_sequence)])
        
        # Calculate proportional antardashas based on sign durations
        maha_total_days = selected_maha['end_jd'] - selected_maha['start_jd']
        
        # Use classical fixed durations instead of navamsa calculation
        sign_durations = calculator.CLASSICAL_YEARS
        
        # Calculate total duration for antardashas in this sequence
        total_duration = sum(sign_durations.get(sign_num, 1.0) for sign_num in antar_sequence)
        
        antar_periods = []
        cursor_jd = selected_maha['start_jd']
        
        for sign_num in antar_sequence:
            # Use proportional duration based on sign strength
            sign_duration = sign_durations.get(sign_num, 1.0)
            proportion = sign_duration / total_duration if total_duration > 0 else 1.0 / len(antar_sequence)
            days = maha_total_days * proportion
            
            # Check if current
            current_jd = calculator._current_jd(datetime.utcnow().replace(tzinfo=timezone.utc))
            is_current = cursor_jd <= current_jd < cursor_jd + days
            
            antar_periods.append({
                'sign': calculator.SIGN_NAMES[sign_num],
                'start_date': calculator._jd_to_iso_utc(cursor_jd),
                'end_date': calculator._jd_to_iso_utc(cursor_jd + days - 1/86400.0),
                'years': round(days / 365.2425, 2),
                'current': is_current
            })
            cursor_jd += days
        
        return {
            "maha_sign": maha_sign,
            "antar_periods": antar_periods
        }
        
    except Exception as e:
        import traceback
        print(f"Jaimini antardasha calculation error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return {"error": f"Calculation failed: {str(e)}"}

@app.post("/api/calculate-kalchakra-antardasha")
async def calculate_kalchakra_antardasha(request: dict):
    """Calculate BPHS Kalchakra antardasha periods for selected mahadasha"""
    try:
        from calculators.bphs_kalachakra_calculator import BPHSKalachakraCalculator
        
        birth_data = BirthData(**request['birth_data'])
        maha_sign = request.get('maha_sign', request.get('maha_planet'))  # Support both keys
        target_date = request.get('target_date')
        
        # Convert timezone to offset if needed
        timezone_offset = birth_data.timezone
        if isinstance(timezone_offset, str):
            if timezone_offset.startswith('UTC'):
                tz_str = timezone_offset[3:]
                if tz_str and ':' in tz_str:
                    sign = 1 if tz_str[0] == '+' else -1
                    parts = tz_str[1:].split(':')
                    timezone_offset = sign * (float(parts[0]) + float(parts[1])/60)
                else:
                    timezone_offset = 5.5
            else:
                timezone_offset = 5.5
        
        birth_dict = {
            'date': birth_data.date,
            'time': birth_data.time,
            'timezone_offset': timezone_offset
        }
        
        calculator = BPHSKalachakraCalculator()
        
        # Parse target date if provided
        current_date = None
        if target_date:
            try:
                current_date = datetime.strptime(target_date, '%Y-%m-%d')
            except:
                current_date = datetime.now()
        
        # Get full kalchakra data
        kalchakra_data = calculator.calculate_kalchakra_dasha(birth_dict, current_date)
        
        if 'error' in kalchakra_data:
            return kalchakra_data
        
        # Find the selected mahadasha by sign name
        selected_maha = None
        for maha in kalchakra_data.get('mahadashas', []):
            if maha['name'] == maha_sign:
                selected_maha = maha
                break
        
        if not selected_maha:
            return {'error': 'Selected mahadasha not found'}
        
        # Calculate antardasha periods for this mahadasha using sign sequence
        sequence = kalchakra_data.get('sequence', [])
        
        # Get antardasha sequence starting from maha sign
        maha_sign_num = selected_maha['sign']
        try:
            start_idx = sequence.index(maha_sign_num)
        except ValueError:
            start_idx = 0
        
        antar_sequence = [sequence[(start_idx + i) % len(sequence)] for i in range(len(sequence))]
        
        maha_total_days = selected_maha['end_jd'] - selected_maha['start_jd']
        cycle_years = kalchakra_data.get('cycle_len', 100)
        
        antar_periods = []
        cursor_jd = selected_maha['start_jd']
        
        for sign_num in antar_sequence:
            sign_name = calculator.SIGN_NAMES[sign_num]
            antar_proportion = calculator.SIGN_YEARS[sign_num] / cycle_years
            antar_days = maha_total_days * antar_proportion
            end_jd = cursor_jd + antar_days
            
            # Check if this is current period
            is_current = False
            if current_date:
                current_jd = calculator._parse_birth_jd({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'time': '12:00',
                    'timezone_offset': 0
                })
                is_current = cursor_jd <= current_jd < end_jd
            
            antar_periods.append({
                'name': sign_name,
                'sign': sign_num,
                'start': calculator._jd_to_iso_utc(cursor_jd),
                'end': calculator._jd_to_iso_utc(end_jd - 1/86400.0),
                'start_jd': cursor_jd,
                'end_jd': end_jd,
                'years': round(antar_days / 365.2425, 4),
                'current': is_current
            })
            
            cursor_jd = end_jd
        
        return {
            'system': 'BPHS Kalchakra Antardasha',
            'maha_sign': maha_sign,
            'antar_periods': antar_periods,
            'sequence': antar_sequence
        }
        
    except Exception as e:
        return {'error': f'Antardasha calculation error: {str(e)}'}

@app.post("/api/calculate-jaimini-kalchakra-antardasha")
async def calculate_jaimini_kalchakra_antardasha_frontend(request: dict):
    """Frontend-compatible endpoint for Jaimini Kalchakra antardasha periods"""
    try:
        from calculators.jaimini_kalachakra_calculator import JaiminiKalachakraCalculator
        from calculators.chart_calculator import ChartCalculator
        from datetime import datetime, timezone
        
        birth_data = BirthData(**request['birth_data'])
        maha_sign = request['maha_sign']
        
        # Convert timezone to offset
        timezone_offset = birth_data.timezone
        if isinstance(timezone_offset, str):
            if timezone_offset.startswith('UTC'):
                tz_str = timezone_offset[3:]
                if tz_str and ':' in tz_str:
                    sign = 1 if tz_str[0] == '+' else -1
                    parts = tz_str[1:].split(':')
                    timezone_offset = sign * (float(parts[0]) + float(parts[1])/60)
                else:
                    timezone_offset = 5.5
            else:
                timezone_offset = 5.5
        
        # Calculate birth chart
        chart_calc = ChartCalculator({})
        chart_data = chart_calc.calculate_chart(birth_data)
        
        # Initialize calculator
        calculator = JaiminiKalachakraCalculator(chart_data)
        
        birth_dict = {
            'date': birth_data.date,
            'time': birth_data.time,
            'timezone_offset': timezone_offset
        }
        
        # Get full Jaimini data
        jaimini_data = calculator.calculate_jaimini_kalachakra_dasha(birth_dict)
        
        if 'error' in jaimini_data:
            return jaimini_data
        
        # Find the selected mahadasha
        selected_maha = None
        for maha in jaimini_data.get('mahadashas', []):
            if maha['sign_name'] == maha_sign:
                selected_maha = maha
                break
        
        if not selected_maha:
            return {"error": "Selected mahadasha not found"}
        
        # Calculate antardashas for this mahadasha
        full_sequence = []
        for maha in jaimini_data.get('mahadashas', []):
            full_sequence.append(maha['sign'])
        
        # Generate antardasha sequence starting from selected sign
        maha_sign_num = selected_maha['sign']
        try:
            start_idx = full_sequence.index(maha_sign_num)
        except ValueError:
            start_idx = 0
        
        antar_sequence = []
        for i in range(len(full_sequence)):
            antar_sequence.append(full_sequence[(start_idx + i) % len(full_sequence)])
        
        # Calculate proportional antardashas based on sign durations
        maha_total_days = selected_maha['end_jd'] - selected_maha['start_jd']
        
        # Use classical fixed durations
        sign_durations = calculator.CLASSICAL_YEARS
        
        # Calculate total duration for antardashas in this sequence
        total_duration = sum(sign_durations.get(sign_num, 1.0) for sign_num in antar_sequence)
        
        antar_periods = []
        cursor_jd = selected_maha['start_jd']
        current_jd = calculator._current_jd(datetime.utcnow().replace(tzinfo=timezone.utc))
        
        for sign_num in antar_sequence:
            # Use proportional duration based on sign strength
            sign_duration = sign_durations.get(sign_num, 1.0)
            proportion = sign_duration / total_duration if total_duration > 0 else 1.0 / len(antar_sequence)
            days = maha_total_days * proportion
            
            # Check if current
            is_current = cursor_jd <= current_jd < cursor_jd + days
            
            antar_periods.append({
                'sign': calculator.SIGN_NAMES[sign_num],
                'start_date': calculator._jd_to_iso_utc(cursor_jd),
                'end_date': calculator._jd_to_iso_utc(cursor_jd + days - 1/86400.0),
                'years': round(days / 365.2425, 2),
                'current': is_current
            })
            cursor_jd += days
        
        return {
            "antar_periods": antar_periods
        }
        
    except Exception as e:
        import traceback
        print(f"Jaimini antardasha calculation error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return {"error": f"Calculation failed: {str(e)}"}

@app.post("/api/jaimini-rashi-skip-reasons")
async def get_jaimini_rashi_skip_reasons(request: dict):
    """Get detailed reasons why a rashi is skipped in Jaimini Kalchakra"""
    try:
        from calculators.jaimini_rashi_strength import JaiminiRashiStrength
        from calculators.chart_calculator import ChartCalculator
        
        # Get chart data
        birth_data = BirthData(**request.get('birth_data', {}))
        chart_calc = ChartCalculator({})
        chart_data = chart_calc.calculate_chart(birth_data)
        
        # Get rashi index (0-11)
        rashi_index = request['rashi_index']
        threshold = request.get('threshold', 25.0)
        
        # Calculate skip reasons
        strength_calc = JaiminiRashiStrength(chart_data)
        skip_reasons = strength_calc.get_skip_reasons(rashi_index, threshold)
        
        return skip_reasons
        
    except Exception as e:
        return {"error": f"Skip reasons calculation failed: {str(e)}"}

@app.get("/api/kalchakra-dasha-info")
async def get_kalchakra_dasha_info():
    """Get information about BPHS Kalchakra Dasha system"""
    try:
        from calculators.bphs_kalachakra_calculator import BPHSKalachakraCalculator
        calculator = BPHSKalachakraCalculator()
        summary = calculator.get_bphs_summary()
        return summary
    except ImportError:
        return {
            "system_name": "Kalchakra Dasha",
            "error": "Calculator not available"
        }

@app.post("/api/calculate-lifetime-gatis")
async def calculate_lifetime_gatis(request: dict):
    """Calculate all Gati periods in user's lifetime for BPHS Kalchakra"""
    try:
        from calculators.bphs_kalachakra_calculator import BPHSKalachakraCalculator
        
        birth_data = BirthData(**request['birth_data'])
        
        # Convert timezone to offset if needed
        timezone_offset = birth_data.timezone
        if isinstance(timezone_offset, str):
            if timezone_offset.startswith('UTC'):
                tz_str = timezone_offset[3:]
                if tz_str and ':' in tz_str:
                    sign = 1 if tz_str[0] == '+' else -1
                    parts = tz_str[1:].split(':')
                    timezone_offset = sign * (float(parts[0]) + float(parts[1])/60)
                else:
                    timezone_offset = 5.5
            else:
                timezone_offset = 5.5
        
        birth_dict = {
            'date': birth_data.date,
            'time': birth_data.time,
            'timezone_offset': timezone_offset
        }
        
        calculator = BPHSKalachakraCalculator()
        gati_analysis = calculator.get_lifetime_gatis(birth_dict)
        
        if 'error' in gati_analysis:
            return gati_analysis
        
        # Add Gati meanings for interpretation
        gati_meanings = calculator.get_gati_meanings()
        
        return {
            "gati_analysis": gati_analysis,
            "gati_meanings": gati_meanings,
            "birth_info": {
                "name": birth_data.name,
                "date": birth_data.date
            }
        }
        
    except ImportError:
        return {"error": "BPHS Kalchakra calculator not available"}
    except Exception as e:
        return {"error": f"Gati analysis failed: {str(e)}"}

@app.post("/api/scan-life-events")
async def scan_life_events(request: dict, current_user: User = Depends(get_current_user)):
    """Scan user's timeline for major life events using astronomical data"""
    try:
        from calculators.life_event_scanner import LifeEventScanner
        from calculators.chart_calculator import ChartCalculator
        from calculators.real_transit_calculator import RealTransitCalculator
        from shared.dasha_calculator import DashaCalculator
        
        birth_data = BirthData(**request['birth_data'])
        start_age = request.get('start_age', 18)
        end_age = request.get('end_age', 50)
        
        # Initialize calculators
        chart_calculator = ChartCalculator({})
        dasha_calculator = DashaCalculator()
        real_transit_calculator = RealTransitCalculator()
        
        # Initialize life event scanner
        scanner = LifeEventScanner(
            chart_calculator=chart_calculator,
            dasha_calculator=dasha_calculator,
            real_transit_calculator=real_transit_calculator
        )
        
        # Convert birth data to dict format
        birth_dict = {
            'name': birth_data.name,
            'date': birth_data.date,
            'time': birth_data.time,
            'latitude': birth_data.latitude,
            'longitude': birth_data.longitude,
            'timezone': birth_data.timezone,
            'place': birth_data.place or '',
            'gender': birth_data.gender or ''
        }
        
        # Scan timeline for events
        events = scanner.scan_timeline(birth_dict, start_age, end_age)
        
        return {
            "birth_info": {
                "name": birth_data.name,
                "date": birth_data.date
            },
            "scan_parameters": {
                "start_age": start_age,
                "end_age": end_age
            },
            "events": events,
            "algorithm_info": {
                "method": "Double Transit Analysis",
                "data_source": "Swiss Ephemeris (Real Astronomical Data)",
                "accuracy": "High - Uses actual planetary positions",
                "features": [
                    "Real Saturn/Jupiter transits",
                    "Vimshottari Dasha activation",
                    "7th/10th house significance analysis",
                    "Multi-layer confirmation system"
                ]
            }
        }
        
    except ImportError as e:
        return {"error": f"Required calculator not available: {str(e)}"}
    except Exception as e:
        import traceback
        print(f"Life event scanning error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return {"error": f"Life event scanning failed: {str(e)}"}

@app.get("/api/gati-meanings")
async def get_gati_meanings():
    """Get Gati interpretations and meanings"""
    try:
        from calculators.bphs_kalachakra_calculator import BPHSKalachakraCalculator
        calculator = BPHSKalachakraCalculator()
        return calculator.get_gati_meanings()
    except ImportError:
        return {
            "Manduka": {
                "name": "Manduka (Frog)",
                "description": "Sudden jumps and unexpected changes",
                "themes": ["Rapid progress", "Unexpected opportunities", "Quick transformations"]
            },
            "Simhavalokana": {
                "name": "Simhavalokana (Lion)", 
                "description": "Powerful, focused transformation",
                "themes": ["Leadership emergence", "Major life changes", "Authoritative periods"]
            },
            "Markata": {
                "name": "Markata (Monkey)",
                "description": "Restless energy and multiple directions", 
                "themes": ["Versatility", "Multiple interests", "Adaptability"]
            }
        }

@app.get("/api/analysis-pricing")
async def get_analysis_pricing():
    """Get pricing for different analysis types"""
    try:
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        
        # Check if analysis_pricing table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='analysis_pricing'")
        if not cursor.fetchone():
            # Create table if it doesn't exist
            cursor.execute('''
                CREATE TABLE analysis_pricing (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_type TEXT UNIQUE NOT NULL,
                    credits INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert default pricing
            default_pricing = [
                ('career', 10),
                ('wealth', 5),
                ('health', 5),
                ('marriage', 5),
                ('education', 5),
                ('progeny', 15)
            ]
            
            for analysis_type, credits in default_pricing:
                cursor.execute(
                    "INSERT INTO analysis_pricing (analysis_type, credits) VALUES (?, ?)",
                    (analysis_type, credits)
                )
            
            conn.commit()
        
        # Fetch current pricing
        cursor.execute("SELECT analysis_type, credits FROM analysis_pricing")
        pricing_data = cursor.fetchall()
        conn.close()
        
        pricing = {}
        for analysis_type, credits in pricing_data:
            pricing[analysis_type] = credits
        
        return {"pricing": pricing}
        
    except Exception as e:
        return {"error": f"Failed to fetch pricing: {str(e)}", "pricing": {
            "career": 10,
            "wealth": 5,
            "health": 5,
            "marriage": 5,
            "education": 5,
            "progeny": 15
        }}

@app.post("/api/ashtakavarga/complete-oracle")
async def get_complete_ashtakavarga_oracle(request: dict, current_user: User = Depends(get_current_user)):
    """Get complete oracle response with both insights and timeline in single call"""
    try:
        from calculators.ashtakvarga_oracle import get_oracle_instance
        
        birth_data = request['birth_data']
        ashtakvarga_data = request['ashtakvarga_data']
        date = request.get('date', datetime.now().strftime('%Y-%m-%d'))
        query_type = request.get('query_type', 'general')
        timeline_years = request.get('timeline_years', 3)
        
        oracle = get_oracle_instance()
        complete_response = oracle.generate_complete_oracle(birth_data, ashtakvarga_data, date, query_type, timeline_years)
        
        return complete_response
        
    except Exception as e:
        print(f"Complete oracle error: {str(e)}")
        return {
            "oracle_message": "Oracle service temporarily unavailable.",
            "power_actions": [{"type": "error", "text": "Service unavailable"}],
            "cosmic_strength": 50,
            "pillar_insights": ["Service temporarily unavailable." for _ in range(12)],
            "timeline_events": [],
            "error": str(e)
        }

@app.post("/api/ashtakavarga/life-predictions")
async def generate_ashtakavarga_life_predictions(request: dict, current_user: User = Depends(get_current_user)):
    """Generate life predictions using Vinay Aditya's 'Dots of Destiny' methodology"""
    try:
        from calculators.ashtakavarga import AshtakavargaCalculator
        
        birth_data = BirthData(**request['birth_data'])
        
        # Calculate chart data
        chart_data = await _calculate_chart_data(birth_data, 'mean')
        
        # Calculate dasha data
        dasha_data = await calculate_accurate_dasha(birth_data)
        
        # Calculate current transits
        transit_request = TransitRequest(
            birth_data=birth_data,
            transit_date=datetime.now().strftime('%Y-%m-%d')
        )
        transit_data = await calculate_transits(transit_request)
        
        # Initialize Ashtakavarga calculator
        calculator = AshtakavargaCalculator(birth_data, chart_data)
        
        # Generate life predictions using Vinay Aditya's methodology
        predictions = calculator.generate_life_predictions(dasha_data, transit_data['planets'])
        
        return {
            "birth_info": {
                "name": birth_data.name,
                "date": birth_data.date
            },
            "predictions": predictions,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Life predictions error: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return {
            "error": f"Life predictions generation failed: {str(e)}",
            "methodology": "Based on Vinay Aditya's 'Dots of Destiny: Applications of Ashtakavarga' and K.N. Rao's teachings"
        }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Astrology API server on port 8001...")
    
    try:
        # Get port from environment for GCP deployment
        port = int(os.getenv('PORT', 8001))
        
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=port,
            timeout_keep_alive=300,
            timeout_graceful_shutdown=60,
            access_log=False,  # Disable for performance in production
            limit_max_requests=2000,
            limit_concurrency=500  # Higher for load balancer
        )
    except Exception as e:
        log_shutdown(f"Exception: {str(e)}")
        raise