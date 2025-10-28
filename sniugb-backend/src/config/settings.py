
from pydantic import BaseModel
import os

class Settings(BaseModel):
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = [o.strip() for o in os.getenv("CORS_ORIGINS","http://localhost:4200").split(",")]
    jwt_secret: str = os.getenv("JWT_SECRET","change-me")
    access_token_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    refresh_token_days: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS","15"))
    sentry_dsn: str | None = os.getenv("SENTRY_DSN")
    db_user: str = os.getenv("DB_USER", os.getenv("user",""))
    db_password: str = os.getenv("DB_PASSWORD", os.getenv("password",""))
    db_host: str = os.getenv("DB_HOST", os.getenv("host","localhost"))
    db_port: str = os.getenv("DB_PORT", os.getenv("port","5432"))
    db_name: str = os.getenv("DB_NAME", os.getenv("dbname",""))
    db_sslmode: str = os.getenv("DB_SSLMODE","prefer")

settings = Settings()
