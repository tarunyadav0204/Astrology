from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import sqlite3
import jwt

# JWT Configuration
SECRET_KEY = "astrology-app-secret-key-2024"
ALGORITHM = "HS256"
security = HTTPBearer()

class User(BaseModel):
    userid: int
    name: str
    phone: str
    role: str

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        phone: str = payload.get("sub")
        if phone is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    cursor.execute("SELECT userid, name, phone, role FROM users WHERE phone = ?", (phone,))
    user = cursor.fetchone()
    conn.close()
    
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return User(userid=user[0], name=user[1], phone=user[2], role=user[3])