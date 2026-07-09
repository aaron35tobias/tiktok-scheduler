from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import config
from models.base import Base

engine = create_engine(config.DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    # Import models here to ensure they are registered with Base
    import models.post
    Base.metadata.create_all(bind=engine)

def get_db_session():
    return SessionLocal()
