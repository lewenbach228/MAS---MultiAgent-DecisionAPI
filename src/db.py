import json
import uuid
import os
from datetime import datetime

try:
    import asyncpg
except ImportError:
    asyncpg = None

try:
    import aiosqlite
except ImportError:
    aiosqlite = None

from src.config import DATABASE_URL
from src.domain import CandidateProfile, Criterion, Decision

_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "decisions.db")


def _row_to_decision(row) -> Decision | None:
    if not row:
        return None
    criteria_data = json.loads(row["criteria_json"])
    criteria = [Criterion(**{k: v for k, v in c.items() if k in ("name", "score", "weight", "justification")}) for c in criteria_data]
    return Decision(
        id=row["id"],
        job=row["job"],
        candidate=CandidateProfile(name=row["candidate_name"], criteria=criteria),
        created_at=datetime.fromisoformat(row["created_at"]),
    )


class Db:
    def __init__(self) -> None:
        self._pool: asyncpg.Pool | None = None
        self._sqlite: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        if asyncpg is not None:
            try:
                dsn = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
                self._pool = await asyncpg.create_pool(dsn, min_size=1, max_size=4)
            except Exception:
                self._pool = None

        if self._pool:
            await self._migrate_asyncpg()
        elif aiosqlite is not None:
            os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
            self._sqlite = await aiosqlite.connect(_DB_PATH)
            self._sqlite.row_factory = aiosqlite.Row
            await self._sqlite.execute("PRAGMA journal_mode=WAL")
            await self._migrate_sqlite()
            print(f"DB: SQLite -> {_DB_PATH}")
        else:
            print("WARNING: aucun driver DB, mode memoire uniquement")

    async def _migrate_asyncpg(self) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS decisions (
                    id TEXT PRIMARY KEY, job TEXT NOT NULL,
                    candidate_name TEXT NOT NULL, utility_score REAL NOT NULL,
                    criteria_json TEXT NOT NULL, created_at TEXT NOT NULL
                )
            """)

    async def _migrate_sqlite(self) -> None:
        await self._sqlite.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id TEXT PRIMARY KEY, job TEXT NOT NULL,
                candidate_name TEXT NOT NULL, utility_score REAL NOT NULL,
                criteria_json TEXT NOT NULL, created_at TEXT NOT NULL
            )
        """)
        await self._sqlite.commit()

    async def save_decision(self, job: str, profile: CandidateProfile) -> str:
        decision_id = f"dec_{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat()
        criteria_json = json.dumps(profile.to_dict()["criteria"])

        if self._pool:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    "INSERT INTO decisions VALUES ($1,$2,$3,$4,$5,$6)",
                    decision_id, job, profile.name, profile.utility_score,
                    criteria_json, now,
                )
        elif self._sqlite:
            await self._sqlite.execute(
                "INSERT INTO decisions VALUES (?,?,?,?,?,?)",
                (decision_id, job, profile.name, profile.utility_score,
                 criteria_json, now),
            )
            await self._sqlite.commit()
        return decision_id

    async def get_decision(self, decision_id: str) -> Decision | None:
        if self._pool:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow("SELECT * FROM decisions WHERE id = $1", decision_id)
                return _row_to_decision(row) if row else None
        elif self._sqlite:
            cur = await self._sqlite.execute("SELECT * FROM decisions WHERE id = ?", (decision_id,))
            row = await cur.fetchone()
            return _row_to_decision(row) if row else None
        return None

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
        if self._sqlite:
            await self._sqlite.close()
