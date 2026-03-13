#!/usr/bin/env python3

import os
import sys
sys.path.append('/home/skywalker/Projects/prj/speakflow/Server')

from database import init_database
from auth import AuthManager

def create_demo_api_key():
    """Create a demo API key for testing"""
    
    # Initialize database first
    print("🔧 Initializing database...")
    init_database()
    
    # Create demo API key
    auth = AuthManager()
    demo_key = auth.create_api_key(
        name="demo-key",
        created_by="system",
        expires_in_days=365
    )
    
    print(f"✅ Demo API Key Created: {demo_key}")
    print("📝 Add this to your frontend .env.local:")
    print(f"VITE_API_KEY={demo_key}")
    
    return demo_key

if __name__ == "__main__":
    create_demo_api_key()
