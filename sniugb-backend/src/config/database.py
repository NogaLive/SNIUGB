from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

DB_USER = os.getenv("DB_USER") or os.getenv("user")
DB_PASSWORD = os.getenv("DB_PASSWORD") or os.getenv("password")
DB_HOST = os.getenv("DB_HOST") or os.getenv("host","localhost")
DB_PORT = os.getenv("DB_PORT") or os.getenv("port","5432")
DB_NAME = os.getenv("DB_NAME") or os.getenv("dbname")
DB_SSLMODE = os.getenv("DB_SSLMODE","prefer")

DATABASE_URL = (
    f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode={DB_SSLMODE}"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=int(os.getenv("DB_POOL_SIZE","5")),
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW","10")),
    connect_args={"prepare_threshold": 0},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
