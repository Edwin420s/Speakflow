"""
User Authentication and Management System
Follows Omi documentation for Firebase Auth integration and user profiles.
"""

import os
import structlog
import jwt
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import hashlib
import secrets

logger = structlog.get_logger()

class AuthProvider(str, Enum):
    """Supported authentication providers."""
    FIREBASE = "firebase"
    GOOGLE = "google"
    APPLE = "apple"
    EMAIL = "email"

@dataclass
class UserProfile:
    """User profile information following Omi documentation."""
    uid: str
    email: Optional[str]
    display_name: Optional[str]
    photo_url: Optional[str]
    auth_provider: AuthProvider
    created_at: datetime
    last_login: Optional[datetime]
    is_active: bool = True
    
    # Omi-specific fields
    device_preferences: Dict[str, Any] = None
    notification_settings: Dict[str, Any] = None
    subscription_tier: str = "free"  # free, pro, enterprise
    
    def __post_init__(self):
        if self.device_preferences is None:
            self.device_preferences = {
                "preferred_audio_codec": "opus",
                "sample_rate": 16000,
                "auto_transcribe": True,
                "language": "en"
            }
        if self.notification_settings is None:
            self.notification_settings = {
                "email_notifications": True,
                "push_notifications": True,
                "task_reminders": True,
                "conversation_summaries": True
            }

@dataclass
class AuthToken:
    """Authentication token information."""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    scope: str = "read write"
    
class UserAuthManager:
    """
    User authentication and management system.
    Follows Omi documentation for Firebase Auth integration.
    """
    
    def __init__(self, jwt_secret: str):
        self.jwt_secret = jwt_secret
        self.users: Dict[str, UserProfile] = {}
        self.refresh_tokens: Dict[str, str] = {}  # refresh_token -> user_id
        
    def verify_firebase_token(self, id_token: str) -> Optional[str]:
        """
        Verify Firebase ID token and return user UID.
        
        Args:
            id_token: Firebase ID token
            
        Returns:
            User UID if valid, None otherwise
        """
        try:
            # In production, this would use Firebase Admin SDK
            # For demo, simulate token verification
            
            # Decode JWT (simplified - in production use Firebase SDK)
            decoded = jwt.decode(id_token, options={"verify_signature": False})
            
            uid = decoded.get("uid")
            email = decoded.get("email")
            display_name = decoded.get("name")
            photo_url = decoded.get("picture")
            
            if not uid:
                logger.warning("Invalid Firebase token - missing UID")
                return None
            
            # Create or update user profile
            self._create_or_update_user(
                uid=uid,
                email=email,
                display_name=display_name,
                photo_url=photo_url,
                auth_provider=AuthProvider.FIREBASE
            )
            
            return uid
            
        except Exception as e:
            logger.error("Firebase token verification failed", error=str(e))
            return None
    
    def verify_google_token(self, id_token: str) -> Optional[str]:
        """Verify Google OAuth token."""
        try:
            # In production, verify with Google OAuth2 API
            # For demo, simulate verification
            
            decoded = jwt.decode(id_token, options={"verify_signature": False})
            
            uid = f"google_{decoded.get('sub')}"
            email = decoded.get("email")
            display_name = decoded.get("name")
            photo_url = decoded.get("picture")
            
            if not decoded.get("sub"):
                logger.warning("Invalid Google token - missing subject")
                return None
            
            self._create_or_update_user(
                uid=uid,
                email=email,
                display_name=display_name,
                photo_url=photo_url,
                auth_provider=AuthProvider.GOOGLE
            )
            
            return uid
            
        except Exception as e:
            logger.error("Google token verification failed", error=str(e))
            return None
    
    def authenticate_with_email_password(self, email: str, password: str) -> Optional[str]:
        """Authenticate with email and password."""
        try:
            # Find user by email
            user = None
            for profile in self.users.values():
                if profile.email == email:
                    user = profile
                    break
            
            if not user:
                logger.warning("User not found", email=email)
                return None
            
            # In production, verify password hash
            # For demo, accept any password for existing users
            if user.auth_provider == AuthProvider.EMAIL:
                user.last_login = datetime.utcnow()
                return user.uid
            else:
                logger.warning("User not registered with email auth", email=email)
                return None
                
        except Exception as e:
            logger.error("Email authentication failed", email=email, error=str(e))
            return None
    
    def create_user_email_password(self, email: str, password: str, display_name: Optional[str] = None) -> Optional[str]:
        """Create new user with email and password."""
        try:
            # Check if user already exists
            for profile in self.users.values():
                if profile.email == email:
                    logger.warning("User already exists", email=email)
                    return None
            
            # Generate unique UID
            uid = f"email_{hashlib.sha256(email.encode()).hexdigest()[:16]}"
            
            # Create user profile
            self._create_or_update_user(
                uid=uid,
                email=email,
                display_name=display_name,
                photo_url=None,
                auth_provider=AuthProvider.EMAIL
            )
            
            # In production, hash and store password
            logger.info("User created successfully", uid=uid, email=email)
            return uid
            
        except Exception as e:
            logger.error("User creation failed", email=email, error=str(e))
            return None
    
    def generate_auth_tokens(self, uid: str) -> Optional[AuthToken]:
        """Generate access and refresh tokens for user."""
        try:
            if uid not in self.users:
                logger.error("User not found", uid=uid)
                return None
            
            # Generate access token (JWT)
            access_payload = {
                "uid": uid,
                "type": "access",
                "exp": datetime.utcnow() + timedelta(hours=1),
                "iat": datetime.utcnow()
            }
            access_token = jwt.encode(access_payload, self.jwt_secret, algorithm="HS256")
            
            # Generate refresh token
            refresh_token = secrets.token_urlsafe(32)
            self.refresh_tokens[refresh_token] = uid
            
            # Update last login
            self.users[uid].last_login = datetime.utcnow()
            
            return AuthToken(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=3600
            )
            
        except Exception as e:
            logger.error("Token generation failed", uid=uid, error=str(e))
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Refresh access token using refresh token."""
        try:
            if refresh_token not in self.refresh_tokens:
                logger.warning("Invalid refresh token")
                return None
            
            uid = self.refresh_tokens[refresh_token]
            if uid not in self.users:
                logger.error("User not found for refresh token", uid=uid)
                return None
            
            # Generate new access token
            access_payload = {
                "uid": uid,
                "type": "access",
                "exp": datetime.utcnow() + timedelta(hours=1),
                "iat": datetime.utcnow()
            }
            access_token = jwt.encode(access_payload, self.jwt_secret, algorithm="HS256")
            
            return access_token
            
        except Exception as e:
            logger.error("Token refresh failed", error=str(e))
            return None
    
    def verify_access_token(self, access_token: str) -> Optional[str]:
        """Verify access token and return user UID."""
        try:
            decoded = jwt.decode(access_token, self.jwt_secret, algorithms=["HS256"])
            
            if decoded.get("type") != "access":
                logger.warning("Invalid token type")
                return None
            
            uid = decoded.get("uid")
            if uid not in self.users:
                logger.warning("User not found", uid=uid)
                return None
            
            if not self.users[uid].is_active:
                logger.warning("User is inactive", uid=uid)
                return None
            
            return uid
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except Exception as e:
            logger.error("Token verification failed", error=str(e))
            return None
    
    def get_user_profile(self, uid: str) -> Optional[UserProfile]:
        """Get user profile by UID."""
        return self.users.get(uid)
    
    def update_user_profile(self, uid: str, updates: Dict[str, Any]) -> bool:
        """Update user profile."""
        try:
            if uid not in self.users:
                logger.error("User not found", uid=uid)
                return False
            
            user = self.users[uid]
            
            # Update allowed fields
            allowed_fields = ["display_name", "photo_url", "device_preferences", "notification_settings"]
            for field, value in updates.items():
                if field in allowed_fields:
                    setattr(user, field, value)
            
            logger.info("User profile updated", uid=uid, fields=list(updates.keys()))
            return True
            
        except Exception as e:
            logger.error("Profile update failed", uid=uid, error=str(e))
            return False
    
    def logout_user(self, refresh_token: str) -> bool:
        """Logout user by invalidating refresh token."""
        try:
            if refresh_token in self.refresh_tokens:
                del self.refresh_tokens[refresh_token]
                logger.info("User logged out successfully")
                return True
            else:
                logger.warning("Refresh token not found")
                return False
                
        except Exception as e:
            logger.error("Logout failed", error=str(e))
            return False
    
    def _create_or_update_user(self, uid: str, email: Optional[str], display_name: Optional[str], 
                              photo_url: Optional[str], auth_provider: AuthProvider):
        """Create or update user profile."""
        if uid in self.users:
            # Update existing user
            user = self.users[uid]
            user.last_login = datetime.utcnow()
            if display_name:
                user.display_name = display_name
            if photo_url:
                user.photo_url = photo_url
        else:
            # Create new user
            user = UserProfile(
                uid=uid,
                email=email,
                display_name=display_name,
                photo_url=photo_url,
                auth_provider=auth_provider,
                created_at=datetime.utcnow(),
                last_login=datetime.utcnow()
            )
            self.users[uid] = user
            logger.info("New user created", uid=uid, email=email, provider=auth_provider.value)

# Global auth manager instance
_auth_manager = None

def get_auth_manager() -> UserAuthManager:
    """Get global auth manager instance."""
    global _auth_manager
    if _auth_manager is None:
        jwt_secret = os.getenv("JWT_SECRET_KEY", "demo-secret-key-change-in-production")
        _auth_manager = UserAuthManager(jwt_secret)
    return _auth_manager

def create_demo_users():
    """Create demo users for testing."""
    auth_manager = get_auth_manager()
    
    # Create demo users
    demo_users = [
        {
            "uid": "demo_user_1",
            "email": "demo@speakflow.com",
            "display_name": "Demo User",
            "photo_url": "https://ui-avatars.com/api/?name=Demo+User&background=random",
            "auth_provider": AuthProvider.EMAIL
        },
        {
            "uid": "demo_user_2", 
            "email": "edwin@speakflow.com",
            "display_name": "Edwin",
            "photo_url": "https://ui-avatars.com/api/?name=Edwin&background=random",
            "auth_provider": AuthProvider.EMAIL
        }
    ]
    
    for user_data in demo_users:
        auth_manager._create_or_update_user(**user_data)
    
    logger.info("Demo users created", count=len(demo_users))
