"""Database configuration and setup for Vocalis"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from typing import Generator
import os

# Database URLs
PRODUCTION_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./vocalis.db"  # Main production database
)
DEMO_DATABASE_URL = os.getenv(
    "DEMO_DATABASE_URL",
    "sqlite:///./demo.db"  # Separate demo database
)
DEMO_ACCOUNT_EMAIL = "doctor@hopital-demo.fr"

# Create engines
def _create_engine(database_url):
    """Create SQLAlchemy engine with appropriate settings"""
    kwargs = {
        "echo": os.getenv("SQL_DEBUG", "false").lower() == "true",
    }

    # SQLite needs special handling
    if database_url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        kwargs["pool_pre_ping"] = True  # Verify connections before using

    return create_engine(database_url, **kwargs)

prod_engine = _create_engine(PRODUCTION_DATABASE_URL)
demo_engine = _create_engine(DEMO_DATABASE_URL)

# Session factories
ProdSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=prod_engine,
)

DemoSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=demo_engine,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""
    pass


def get_db() -> Generator[Session, None, None]:
    """Dependency to get production database session"""
    db = ProdSessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_demo_db() -> Generator[Session, None, None]:
    """Dependency to get demo database session"""
    db = DemoSessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_for_user(email: str) -> Generator[Session, None, None]:
    """Get appropriate database session based on user email

    Demo accounts use demo.db, all other accounts use vocalis.db
    """
    is_demo = email.lower() == DEMO_ACCOUNT_EMAIL.lower()
    session_local = DemoSessionLocal if is_demo else ProdSessionLocal
    db = session_local()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables in both databases"""
    Base.metadata.create_all(bind=prod_engine)
    Base.metadata.create_all(bind=demo_engine)
