from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import jwt

# JWT Configuration
import os
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("JWT_SECRET")
if not SECRET_KEY:
    raise ValueError("JWT_SECRET environment variable is required")
ALGORITHM = "HS256"
security = HTTPBearer()

class User(BaseModel):
    userid: int
    name: str
    phone: str
    role: str
    signup_client: Optional[str] = None

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        phone: str = payload.get("sub")
        if phone is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    from db import get_conn, execute

    with get_conn() as conn:
        cur = execute(
            conn,
            "SELECT userid, name, phone, role, signup_client FROM users WHERE phone = ?",
            (phone,),
        )
        user = cur.fetchone()
    
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    sc = user[4] if len(user) > 4 else None
    if sc is not None and str(sc).strip() == "":
        sc = None
    return User(userid=user[0], name=user[1], phone=user[2], role=user[3], signup_client=sc)