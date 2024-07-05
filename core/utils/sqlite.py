from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()

SQLALCHEMY_DATABASE_URL = "sqlite:///./sqlite.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base.metadata.create_all(bind=engine) # Initialized in the main.py lifespan method

def get_db():
    db = SessionLocal()
    try:
        print("------====>>>>> Opening DB Connection <<<<<====------")
        yield db
    finally:
        print("------====>>>>> Closing DB Connection <<<<<====------")
        db.close()