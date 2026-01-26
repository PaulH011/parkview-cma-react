"""
Database connection and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import os

from auth.config import DATABASE_URL
from auth.models import Base

# Create engine
# For SQLite, we need to handle the path correctly on Windows
_db_url = DATABASE_URL

if _db_url.startswith('sqlite:///') and not _db_url.startswith('sqlite:////'):
    # Relative path - make it relative to the app directory (project root)
    db_path = _db_url.replace('sqlite:///', '')
    # Get the project root directory (parent of 'auth' folder)
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_db_path = os.path.join(script_dir, db_path)
    # Ensure the directory exists
    os.makedirs(os.path.dirname(full_db_path) if os.path.dirname(full_db_path) else '.', exist_ok=True)
    _db_url = f'sqlite:///{full_db_path}'

engine = create_engine(
    _db_url,
    echo=False,  # Set to True for SQL debugging
    connect_args={'check_same_thread': False} if 'sqlite' in _db_url else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize the database, creating all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)


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
