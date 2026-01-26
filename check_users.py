"""
Simple utility script to check and manage users in the database.

Run with: python check_users.py

Commands:
  python check_users.py                   - List all users
  python check_users.py --reset           - Delete database and start fresh
  python check_users.py --add EMAIL       - Add a test user with password "Test1234"
  python check_users.py --passwd EMAIL    - Reset user password to "Test1234"
"""

import sys
import os

# Add the parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auth.database import init_db, get_session, engine
from auth.models import User, Scenario, Base
from auth.security import hash_password
from datetime import datetime


def list_users():
    """List all users in the database."""
    init_db()
    
    with get_session() as session:
        users = session.query(User).all()
        
        if not users:
            print("\n[!] No users found in database.")
            print("    Run the app and create an account to get started.")
            return
        
        print(f"\n[*] Found {len(users)} user(s):\n")
        print("-" * 80)
        
        for user in users:
            scenarios = session.query(Scenario).filter_by(user_id=user.id).count()
            print(f"  Email:      {user.email}")
            print(f"  ID:         {user.id}")
            print(f"  Verified:   {'[YES]' if user.is_verified else '[NO]'}")
            print(f"  Created:    {user.created_at}")
            print(f"  Last Login: {user.last_login or 'Never'}")
            print(f"  Scenarios:  {scenarios}")
            print("-" * 80)


def reset_database():
    """Delete the database and start fresh."""
    from auth.config import DATABASE_URL
    
    # Get the database path
    if DATABASE_URL.startswith('sqlite:///'):
        db_path = DATABASE_URL.replace('sqlite:///', '')
        if not os.path.isabs(db_path):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(script_dir, db_path)
        
        if os.path.exists(db_path):
            confirm = input(f"\n[WARNING] This will DELETE the database at:\n   {db_path}\n\nType 'yes' to confirm: ")
            if confirm.lower() == 'yes':
                os.remove(db_path)
                print("[OK] Database deleted.")
                print("     Run the app to create a new database.")
            else:
                print("[X] Cancelled.")
        else:
            print(f"[INFO] Database not found at: {db_path}")
    else:
        print("[X] Reset only works with SQLite databases.")


def add_test_user(email: str):
    """Add a test user with a known password."""
    init_db()
    
    with get_session() as session:
        # Check if user exists
        existing = session.query(User).filter_by(email=email.lower()).first()
        if existing:
            print(f"[X] User {email} already exists.")
            return
        
        # Create user
        user = User(
            email=email.lower(),
            password_hash=hash_password("Test1234"),
            is_verified=True,
            created_at=datetime.utcnow()
        )
        session.add(user)
        session.commit()
        
        print(f"[OK] Created user: {email}")
        print(f"     Password: Test1234")
        print(f"     (Change this password after first login!)")


def reset_user_password(email: str):
    """Reset a user's password to Test1234."""
    init_db()
    
    with get_session() as session:
        user = session.query(User).filter_by(email=email.lower()).first()
        if not user:
            print(f"[X] User {email} not found.")
            return
        
        user.password_hash = hash_password("Test1234")
        session.commit()
        
        print(f"[OK] Password reset for: {email}")
        print(f"     New password: Test1234")
        print(f"     (Change this password after login!)")


def show_db_path():
    """Show the database file path."""
    from auth.config import DATABASE_URL
    
    if DATABASE_URL.startswith('sqlite:///'):
        db_path = DATABASE_URL.replace('sqlite:///', '')
        if not os.path.isabs(db_path):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(script_dir, db_path)
        
        exists = "[EXISTS]" if os.path.exists(db_path) else "[NOT CREATED YET]"
        print(f"\n[DB] Database path: {db_path}")
        print(f"     Status: {exists}")
    else:
        print(f"\n[DB] Database URL: {DATABASE_URL}")


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  Parkview CMA - Database Utility")
    print("=" * 50)
    
    show_db_path()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--reset":
            reset_database()
        elif sys.argv[1] == "--add" and len(sys.argv) > 2:
            add_test_user(sys.argv[2])
        elif sys.argv[1] == "--passwd" and len(sys.argv) > 2:
            reset_user_password(sys.argv[2])
        else:
            print("\nUsage:")
            print("  python check_users.py                   - List all users")
            print("  python check_users.py --reset           - Delete database")
            print("  python check_users.py --add EMAIL       - Add test user")
            print("  python check_users.py --passwd EMAIL    - Reset password")
    else:
        list_users()
    
    print()
