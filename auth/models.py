"""
SQLAlchemy models for authentication and scenarios.
"""

from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, ForeignKey,
    UniqueConstraint, create_engine
)
from sqlalchemy.orm import declarative_base, relationship
import uuid

Base = declarative_base()


def generate_uuid():
    """Generate a new UUID string."""
    return str(uuid.uuid4())


class User(Base):
    """User account model."""
    __tablename__ = 'users'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    scenarios = relationship('Scenario', back_populates='user', cascade='all, delete-orphan')
    verification_tokens = relationship('EmailVerificationToken', back_populates='user', cascade='all, delete-orphan')
    reset_tokens = relationship('PasswordResetToken', back_populates='user', cascade='all, delete-orphan')

    def to_dict(self):
        """Convert user to dictionary for session storage."""
        return {
            'id': self.id,
            'email': self.email,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
        }


class EmailVerificationToken(Base):
    """Email verification token model."""
    __tablename__ = 'email_verification_tokens'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    token = Column(String(64), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship('User', back_populates='verification_tokens')

    @property
    def is_expired(self):
        """Check if token has expired."""
        return datetime.utcnow() > self.expires_at

    @property
    def is_used(self):
        """Check if token has been used."""
        return self.used_at is not None


class PasswordResetToken(Base):
    """Password reset token model."""
    __tablename__ = 'password_reset_tokens'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    token = Column(String(64), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship('User', back_populates='reset_tokens')

    @property
    def is_expired(self):
        """Check if token has expired."""
        return datetime.utcnow() > self.expires_at

    @property
    def is_used(self):
        """Check if token has been used."""
        return self.used_at is not None


class Scenario(Base):
    """User scenario model - migrated from JSON storage."""
    __tablename__ = 'scenarios'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(255), nullable=False)
    base_currency = Column(String(3), default='USD')
    overrides = Column(Text, nullable=False, default='{}')  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)

    # Relationships
    user = relationship('User', back_populates='scenarios')

    # Unique constraint on user_id + name
    __table_args__ = (
        UniqueConstraint('user_id', 'name', name='uix_user_scenario_name'),
    )

    def to_dict(self):
        """Convert scenario to dictionary format matching old JSON structure."""
        import json
        return {
            'name': self.name,
            'timestamp': self.updated_at.isoformat() if self.updated_at else self.created_at.isoformat(),
            'base_currency': self.base_currency,
            'overrides': json.loads(self.overrides) if self.overrides else {}
        }
