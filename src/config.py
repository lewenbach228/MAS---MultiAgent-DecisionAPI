import os
from dotenv import load_dotenv

load_dotenv()


def getenv(key: str, default: str = "") -> str:
    return os.getenv(key, default)


GEMINI_API_KEY: str = getenv("GEMINI_API_KEY")
GEMINI_MODEL: str = getenv("GEMINI_MODEL", "gemini-2.5-flash")

DATABASE_URL: str = getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/p3_decision")

REDIS_URL: str = getenv("REDIS_URL", "redis://localhost:6379/0")

API_PORT: int = int(getenv("API_PORT", "8000"))
