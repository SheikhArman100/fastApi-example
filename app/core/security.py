from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import re
from jose import JWTError, jwt
from .config import settings

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def parse_duration(duration_str: str) -> timedelta:
    """Parse duration string like '1m', '7d', '30s' into timedelta"""
    if not duration_str:
        return timedelta(minutes=15)  # Default

    # Match patterns like 1m, 7d, 30s, 2h
    match = re.match(r'^(\d+)([smhd])$', duration_str.lower())
    if not match:
        return timedelta(minutes=15)  # Default fallback

    value, unit = match.groups()
    value = int(value)

    if unit == 's':
        return timedelta(seconds=value)
    elif unit == 'm':
        return timedelta(minutes=value)
    elif unit == 'h':
        return timedelta(hours=value)
    elif unit == 'd':
        return timedelta(days=value)
    else:
        return timedelta(minutes=15)  # Default fallback

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Use configured expiry time from env
        expire = datetime.utcnow() + parse_duration(settings.access_token_expire_time)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.access_token_secret, algorithm="HS256")
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Use configured expiry time from env
        expire = datetime.utcnow() + parse_duration(settings.refresh_token_expire_time)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.refresh_token_secret, algorithm="HS256")
    return encoded_jwt

def verify_token(token: str, secret_key: str = None):
    """Verify JWT token and return payload"""
    try:
        if secret_key is None:
            secret_key = settings.access_token_secret
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        print(payload)
        return payload
    except JWTError:
        return None
