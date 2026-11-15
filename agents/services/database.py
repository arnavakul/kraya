import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is missing from .env")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
    pool_timeout=30,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

def test_database_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version();"))
            print("Database connection successful!")
            print(result.scalar())
            return True

    except Exception as error:
        print("Database connection failed!")
        print(f"Error: {error}")
        return False