import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# ADVANCED LEVEL: Construct DB Path relative to the current file to prevent CWD issues across environments
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Absolute Database URL ensures Railway and Local execution remains consistent
DB_PATH = os.path.join(DATA_DIR, "faculty_automation.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Using pool_pre_ping for connection robustness
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False},
    pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
