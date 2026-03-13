#!/usr/bin/env python3
"""
Initialize SpeakFlow with demo API key for Omi Builder Friday hackathon.
"""

import sys
import os

# Add the Server directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_database
from auth import AuthManager
import structlog

logger = structlog.get_logger()

def create_demo_api_key():
    """Create a demo API key for hackathon testing."""
    try:
        # Initialize database
        db = get_database()
        
        # Create auth manager
        auth_manager = AuthManager()
        
        # Create demo API key
        demo_key = auth_manager.create_api_key(
            name="omi-hackathon-demo",
            created_by="system",
            expires_in_days=365
        )
        
        print(f"✅ Demo API key created successfully!")
        print(f"🔑 API Key: {demo_key}")
        print(f"📝 Use this key to test the SpeakFlow API")
        print(f"🚀 Ready for Omi Builder Friday hackathon!")
        
        return demo_key
        
    except Exception as e:
        logger.error("Failed to create demo API key", error=str(e))
        print(f"❌ Failed to create demo API key: {str(e)}")
        return None

if __name__ == "__main__":
    create_demo_api_key()
