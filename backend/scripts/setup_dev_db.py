#!/usr/bin/env python3
"""
Development database setup for FastAPI + SQLModel + Alembic
"""

import asyncio
import subprocess
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.core.database import check_database_health


async def create_database():
    """Create database if it doesn't exist"""
    
    # Extract database name from connection string
    db_url = str(settings.SQLALCHEMY_DATABASE_URI)
    db_name = db_url.split("/")[-1]
    
    print(f"🔍 Checking if database '{db_name}' exists...")
    
    health = await check_database_health()
    
    if health["status"] == "healthy":
        print("✅ Database already exists and is accessible")
        return True
    
    if health.get("error_type") == "database_not_found":
        print(f"📝 Creating database '{db_name}'...")
        
        try:
            # Use your database connection settings
            cmd = [
                "createdb",
                "-h", getattr(settings, 'DB_HOST', 'localhost'),
                "-p", str(getattr(settings, 'DB_PORT', 5432)),
                "-U", getattr(settings, 'DB_USERNAME', 'postgres'),
                db_name
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Database '{db_name}' created successfully!")
                return True
            else:
                print(f"❌ Failed to create database: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating database: {e}")
            return False
    
    print(f"❌ Database connection issue: {health.get('message', 'Unknown error')}")
    return False


async def run_migrations():
    """Run Alembic migrations"""
    print("🚀 Running Alembic migrations...")
    
    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"], 
            capture_output=True, 
            text=True,
            cwd=project_root
        )
        
        if result.returncode == 0:
            print("✅ Migrations completed successfully!")
            print(result.stdout)
            return True
        else:
            print(f"❌ Migration failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error running migrations: {e}")
        return False


async def main():
    """Main setup function"""
    print("🎯 FastVue Database Setup (SQLModel + Alembic)")
    print("=" * 50)
    
    # Check environment
    environment = getattr(settings, 'ENVIRONMENT', 'development')
    if environment != 'development':
        print(f"❌ This script is for development only. Current: {environment}")
        sys.exit(1)
    
    # Step 1: Create database
    if not await create_database():
        print("❌ Database creation failed")
        sys.exit(1)
    
    # Step 2: Run Alembic migrations
    if not await run_migrations():
        print("❌ Migrations failed")
        sys.exit(1)
    
    # Step 3: Final health check
    print("🔍 Final health check...")
    health = await check_database_health()
    
    if health["status"] == "healthy":
        print("🎉 Database setup completed successfully!")
        print("🚀 Ready to start FastAPI server:")
        print("   uvicorn app.main:app --reload")
    else:
        print("❌ Setup completed but health check failed")
        print(f"   Issue: {health.get('message')}")


if __name__ == "__main__":
    asyncio.run(main())