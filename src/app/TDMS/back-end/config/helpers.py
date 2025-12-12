from jose import jwt
import bcrypt
from datetime import datetime, timedelta
from config.settings import settings




def hash_password(password: str) -> str:
    # """Hash a password using bcrypt."""
    # if isinstance(password, str):
    #     password = password.encode('utf-8')
    # elif isinstance(password, bytes):
    #     password_bytes = password
    # else:
    #     raise ValueError("Password must be a str or bytes")
    # password_bytes = password_bytes[:72]
    # # Decode for Passlib; ignore errors to avoid decode issues
    # password_str = password_bytes.decode("utf-8", errors="ignore")
    # return pwd_context.hash(password_bytes.decode('utf-8', errors='ignore'))
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    # return pwd_context.verify(plain_password, hashed_password)
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

