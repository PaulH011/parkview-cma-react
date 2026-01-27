"""
Database connection and session management.

Supports both SQLite (local development) and PostgreSQL (Supabase/production).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import os

from auth.config import DATABASE_URL
from auth.models import Base

# Track if database has been initialized this session
_db_initialized = False

# Create engine
_db_url = DATABASE_URL

# Configure based on database type
engine_kwargs = {
    'echo': False,  # Set to True for SQL debugging
}

if _db_url.startswith('sqlite'):
    # SQLite configuration (local development fallback)
    if _db_url.startswith('sqlite:///') and not _db_url.startswith('sqlite:////'):
        # Relative path - make it relative to the app directory (project root)
        db_path = _db_url.replace('sqlite:///', '')
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        full_db_path = os.path.join(script_dir, db_path)
        os.makedirs(os.path.dirname(full_db_path) if os.path.dirname(full_db_path) else '.', exist_ok=True)
        _db_url = f'sqlite:///{full_db_path}'
    engine_kwargs['connect_args'] = {'check_same_thread': False}
    
elif _db_url.startswith('postgresql'):
    # PostgreSQL configuration (Supabase/production)
    # Connection pool settings optimized for low-latency operations
    engine_kwargs.update({
        'pool_size': 3,           # Smaller pool for serverless (reduces idle connections)
        'max_overflow': 5,        # Additional connections allowed beyond pool_size
        'pool_timeout': 10,       # Shorter timeout for faster failure detection
        'pool_recycle': 300,      # Recycle connections every 5 minutes (Supabase may close idle)
        'pool_pre_ping': False,   # Disable pre-ping to reduce latency (pool_recycle handles stale)
    })

engine = create_engine(_db_url, **engine_kwargs)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize the database, creating all tables if they don't exist.

    Only runs once per application session to avoid repeated metadata checks.
    """
    global _db_initialized
    if _db_initialized:
        return
    Base.metadata.create_all(bind=engine)
    _db_initialized = True


@contextmanager
def get_session():
    """Get a database session with automatic cleanup."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db_session() -> Session:
    """Get a database session (caller must close)."""
    return SessionLocal()
