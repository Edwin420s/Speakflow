from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import os
from typing import Optional
import structlog

logger = structlog.get_logger()

Base = declarative_base()

class Transcript(Base):
    """Database model for storing conversation transcripts."""
    __tablename__ = "transcripts"
    
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed = Column(Boolean, default=False)
    task_count = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<Transcript(id={self.id}, created_at={self.created_at}, task_count={self.task_count})>"

class Task(Base):
    """Database model for storing extracted tasks."""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    transcript_id = Column(Integer, nullable=False, index=True)
    task = Column(String(500), nullable=False)
    assigned_to = Column(String(100), nullable=True)
    deadline = Column(String(50), nullable=True)
    completed = Column(Boolean, default=False)
    trello_card_id = Column(String(50), nullable=True)
    trello_card_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Task(id={self.id}, task={self.task[:50]}..., assigned_to={self.assigned_to})>"

class ApiKey(Base):
    """Database model for API key management."""
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    key_hash = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    created_by = Column(String(100), nullable=True)
    
    def __repr__(self):
        return f"<ApiKey(id={self.id}, name={self.name}, active={self.active})>"

class UsageLog(Base):
    """Database model for API usage logging."""
    __tablename__ = "usage_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    api_key_id = Column(Integer, nullable=True, index=True)
    endpoint = Column(String(100), nullable=False)
    method = Column(String(10), nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    request_size = Column(Integer, nullable=True)
    response_size = Column(Integer, nullable=True)
    status_code = Column(Integer, nullable=False)
    processing_time_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<UsageLog(id={self.id}, endpoint={self.endpoint}, status={self.status_code})>"

class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self, database_url: Optional[str] = None):
        if database_url is None:
            # Use SQLite by default, fallback to PostgreSQL if configured
            database_url = os.getenv("DATABASE_URL", "sqlite:///./speakflow.db")
        
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        logger.info("Database initialized", database_url=database_url.split('://')[0] + '://***')
    
    def create_tables(self):
        """Create all database tables."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error("Failed to create database tables", error=str(e))
            raise
    
    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()
    
    def close(self):
        """Close database connections."""
        self.engine.dispose()
        logger.info("Database connections closed")

# Global database instance
db_manager = None

def get_database() -> DatabaseManager:
    """Get the global database manager instance."""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager

def init_database():
    """Initialize the database."""
    db = get_database()
    db.create_tables()
    logger.info("Database initialization completed")

def get_db_session():
    """Dependency to get database session."""
    db = get_database()
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()
