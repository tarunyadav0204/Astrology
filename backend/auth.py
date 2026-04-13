from fastapi import Depends, HTTPException, Request
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

# Standard Bearer. auto_error=False so we can fall back when Authorization is stripped by a proxy/CDN.
security = HTTPBearer(auto_error=False)

# Duplicate of Authorization for clients where the edge strips `Authorization` but keeps custom headers.
MOBILE_AUTH_FALLBACK_HEADER = "X-AstroRoshni-Authorization"


def _extract_bearer_token(request: Request, credentials: Optional[HTTPAuthorizationCredentials]) -> Optional[str]:
    if credentials is not None and credentials.credentials:
        t = str(credentials.credentials).strip()
        if t:
            return t
    auth = request.headers.get("Authorization")
    if auth:
        auth = str(auth).strip()
        if auth.lower().startswith("bearer "):
            t = auth[7:].strip()
            if t:
                return t
    alt = request.headers.get(MOBILE_AUTH_FALLBACK_HEADER)
    if not alt:
        return None
    alt = str(alt).strip()
    if alt.lower().startswith("bearer "):
        return alt[7:].strip() or None
    return alt or None


def extract_request_bearer_token(request: Request) -> Optional[str]:
    """Same as get_current_user token resolution, without Depends (for middleware logging)."""
    return _extract_bearer_token(request, None)


class User(BaseModel):
    userid: int
    name: str
    phone: str
    role: str
    signup_client: Optional[str] = None


def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    token = _extract_bearer_token(request, credentials)
    if not token:
        raise HTTPException(status_code=403, detail="Not authenticated")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
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