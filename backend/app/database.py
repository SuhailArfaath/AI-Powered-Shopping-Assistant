from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

# PostgreSQL (Products + Chat History)
pg_engine = create_engine(settings.postgres_url, pool_pre_ping=True)
PG_SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=pg_engine)

# MySQL (Orders)
my_engine = create_engine(settings.mysql_url, pool_pre_ping=True)
MY_SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=my_engine)

Base = declarative_base()

def get_pg_db():
    db = PG_SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_my_db():
    db = MY_SessionLocal()
    try:
        yield db
    finally:
        db.close()
