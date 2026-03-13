import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
import structlog

from database import get_database, get_db_session, ApiKey, UsageLog
from models import ErrorResponse

logger = structlog.get_logger()

# Security configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class AuthManager:
    """Manages authentication and authorization."""
    
    def __init__(self):
        self.db = get_database()
    
    def hash_api_key(self, api_key: str) -> str:
        """Hash an API key for secure storage."""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def generate_api_key(self) -> str:
        """Generate a new API key."""
        return f"sk-{secrets.token_urlsafe(32)}"
    
    def create_api_key(self, name: str, created_by: Optional[str] = None, 
                      expires_in_days: Optional[int] = None) -> str:
        """
        Create a new API key.
        
        Args:
            name: Descriptive name for the API key
            created_by: Who created the key
            expires_in_days: Number of days until expiry (None for no expiry)
            
        Returns:
            The generated API key
        """
        api_key = self.generate_api_key()
        api_key_hash = self.hash_api_key(api_key)
        
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        session = self.db.get_session()
        try:
            db_key = ApiKey(
                key_hash=api_key_hash,
                name=name,
                created_by=created_by,
                expires_at=expires_at
            )
            session.add(db_key)
            session.commit()
            session.refresh(db_key)
            
            logger.info("API key created", 
                       key_id=db_key.id, 
                       name=name, 
                       expires_at=expires_at)
            
            return api_key
            
        except Exception as e:
            session.rollback()
            logger.error("Failed to create API key", error=str(e), name=name)
            raise
        finally:
            session.close()
    
    def validate_api_key(self, api_key: str) -> Optional[ApiKey]:
        """
        Validate an API key and return the corresponding database record.
        
        Args:
            api_key: The API key to validate
            
        Returns:
            ApiKey object if valid, None otherwise
        """
        if not api_key or not api_key.startswith("sk-"):
            return None
        
        api_key_hash = self.hash_api_key(api_key)
        
        session = self.db.get_session()
        try:
            db_key = session.query(ApiKey).filter(
                ApiKey.key_hash == api_key_hash,
                ApiKey.active == True
            ).first()
            
            if not db_key:
                return None
            
            # Check expiry
            if db_key.expires_at and db_key.expires_at < datetime.utcnow():
                logger.warning("API key expired", key_id=db_key.id, name=db_key.name)
                return None
            
            # Update usage
            db_key.usage_count += 1
            db_key.last_used = datetime.utcnow()
            session.commit()
            
            return db_key
            
        except Exception as e:
            session.rollback()
            logger.error("Error validating API key", error=str(e))
            return None
        finally:
            session.close()
    
    def revoke_api_key(self, key_id: int) -> bool:
        """
        Revoke an API key.
        
        Args:
            key_id: Database ID of the API key
            
        Returns:
            True if successful, False otherwise
        """
        session = self.db.get_session()
        try:
            db_key = session.query(ApiKey).filter(ApiKey.id == key_id).first()
            if not db_key:
                return False
            
            db_key.active = False
            session.commit()
            
            logger.info("API key revoked", key_id=key_id, name=db_key.name)
            return True
            
        except Exception as e:
            session.rollback()
            logger.error("Failed to revoke API key", error=str(e), key_id=key_id)
            return False
        finally:
            session.close()
    
    def list_api_keys(self, active_only: bool = True) -> List[ApiKey]:
        """
        List API keys.
        
        Args:
            active_only: Whether to only return active keys
            
        Returns:
            List of ApiKey objects
        """
        session = self.db.get_session()
        try:
            query = session.query(ApiKey)
            if active_only:
                query = query.filter(ApiKey.active == True)
            
            return query.all()
            
        except Exception as e:
            logger.error("Failed to list API keys", error=str(e))
            return []
        finally:
            session.close()

# Global auth manager instance
auth_manager = AuthManager()

async def get_current_api_key(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> ApiKey:
    """
    FastAPI dependency to get the current API key from request headers.
    
    Args:
        credentials: HTTP Bearer credentials from the request
        
    Returns:
        ApiKey object if authentication is successful
        
    Raises:
        HTTPException: If authentication fails
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "API key required"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    api_key = auth_manager.validate_api_key(credentials.credentials)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid or expired API key"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return api_key

async def log_api_usage(api_key: ApiKey, endpoint: str, method: str, 
                       ip_address: str, user_agent: str, 
                       request_size: int, response_size: int,
                       status_code: int, processing_time_ms: int,
                       error_message: Optional[str] = None):
    """
    Log API usage for monitoring and analytics.
    
    Args:
        api_key: The API key used for the request
        endpoint: API endpoint called
        method: HTTP method used
        ip_address: Client IP address
        user_agent: Client user agent string
        request_size: Size of request in bytes
        response_size: Size of response in bytes
        status_code: HTTP status code returned
        processing_time_ms: Processing time in milliseconds
        error_message: Error message if any
    """
    session = auth_manager.db.get_session()
    try:
        usage_log = UsageLog(
            api_key_id=api_key.id,
            endpoint=endpoint,
            method=method,
            ip_address=ip_address,
            user_agent=user_agent,
            request_size=request_size,
            response_size=response_size,
            status_code=status_code,
            processing_time_ms=processing_time_ms,
            error_message=error_message
        )
        session.add(usage_log)
        session.commit()
        
    except Exception as e:
        session.rollback()
        logger.error("Failed to log API usage", error=str(e))
    finally:
        session.close()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Token expiry time
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """
    Verify a JWT token.
    
    Args:
        token: JWT token to verify
        
    Returns:
        Decoded token data if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
