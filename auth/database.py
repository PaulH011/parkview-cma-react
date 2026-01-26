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
if DATABASE_URL.startswith('sqlite:///') and not DATABASE_URL.startswith('sqlite:////'):
    # Relative path - make it relative to the app directory
    db_path = DATABASE_URL.replace('sqlite:///', '')
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_db_path = os.path.join(script_dir, db_path)
    DATABASE_URL = f'sqlite:///{full_db_path}'

engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    connect_args={'check_same_thread': False} if 'sqlite' in DATABASE_URL else {}
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
