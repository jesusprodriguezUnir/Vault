from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import time
from sqlalchemy.exc import OperationalError

# Docker Compose will provide this Env Var, or use localhost for hybrid run
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://vaultuser:vaultpassword@localhost:5432/vaultdb")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def wait_for_db():
    """Retry logic for database connection on startup."""
    max_retries = 10
    retry_interval = 2
    for i in range(max_retries):
        try:
            connection = engine.connect()
            connection.close()
            print("Database connection successful.")
            return
        except OperationalError:
            print(f"Database not ready. Retrying in {retry_interval}s... ({i+1}/{max_retries})")
            time.sleep(retry_interval)
    raise Exception("Could not connect to the database after several retries.")
