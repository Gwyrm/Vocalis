"""Database configuration and setup for Vocalis"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os

# Database configuration
# For demo/development, use SQLite. For production, set DATABASE_URL env variable
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./vocalis_demo.db"  # SQLite for demo, no PostgreSQL required
)

# Create engine
kwargs = {
    "echo": os.getenv("SQL_DEBUG", "false").lower() == "true",
}

# SQLite needs special handling
if DATABASE_URL.startswith("sqlite"):
    kwargs["connect_args"] = {"check_same_thread": False}
else:
    kwargs["pool_pre_ping"] = True  # Verify connections before using

engine = create_engine(DATABASE_URL, **kwargs)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""
    pass


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
