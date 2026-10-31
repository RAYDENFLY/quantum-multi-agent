"""Asynchronous SQLite WAL persistence and schema migration manager."""

import asyncio
from pathlib import Path
import time
from typing import Any, List, Optional, Sequence, Tuple
import aiosqlite

from quantum.core.logging import get_logger

logger = get_logger("storage.database")

PRAGMAS: List[str] = [
    "PRAGMA journal_mode = WAL;",
    "PRAGMA synchronous = NORMAL;",
    "PRAGMA foreign_keys = ON;",
    "PRAGMA busy_timeout = 5000;",
    "PRAGMA temp_store = MEMORY;",
    "PRAGMA cache_size = -8000;",
    "PRAGMA mmap_size = 33554432;",
]


class DatabaseManager:
    """Manages the application SQLite database, connection pragmas, and schema migrations."""

    def __init__(self, db_path: Path, migrations_dir: Optional[Path] = None) -> None:
        self.db_path = Path(db_path).resolve()
        self.migrations_dir = migrations_dir or (Path(__file__).parent / "migrations")
        self._connection: Optional[aiosqlite.Connection] = None
        self._lock = asyncio.Lock()
        self._initialized = False

    @property
    def is_connected(self) -> bool:
        """Check whether the active connection is open."""
        return self._connection is not None

    async def connect(self) -> aiosqlite.Connection:
        """Open database connection if not open and apply required performance pragmas."""
        async with self._lock:
            if self._connection is None:
                self.db_path.parent.mkdir(parents=True, exist_ok=True)
                self._connection = await aiosqlite.connect(str(self.db_path))
                self._connection.row_factory = aiosqlite.Row

                # Apply connection pragmas
                for pragma in PRAGMAS:
                    await self._connection.execute(pragma)
                await self._connection.commit()

                logger.info("SQLite connected at %s (WAL mode configured)", self.db_path)
            return self._connection

    async def initialize(self) -> None:
        """Connect to database, apply pragmas, and execute pending migrations."""
        if self._initialized:
            return

        conn = await self.connect()
        await self.apply_migrations(conn)
        self._initialized = True
        logger.info("SQLite database initialization completed successfully")

    async def apply_migrations(self, conn: Optional[aiosqlite.Connection] = None) -> int:
        """Apply all pending SQL migration files in chronological order."""
        active_conn = conn or await self.connect()

        # Ensure schema_migrations table exists
        await active_conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at_ms INTEGER NOT NULL
            );
            """
        )
        await active_conn.commit()

        # Fetch already applied versions
        async with active_conn.execute("SELECT version FROM schema_migrations") as cursor:
            rows = await cursor.fetchall()
            applied_versions = {row[0] for row in rows}

        if not self.migrations_dir.exists():
            logger.warning("Migrations directory not found: %s", self.migrations_dir)
            return 0

        migration_files = sorted(self.migrations_dir.glob("*.sql"))
        applied_count = 0

        for file_path in migration_files:
            try:
                version_str = file_path.name.split("_")[0]
                version = int(version_str)
            except (ValueError, IndexError):
                logger.warning("Skipping migration file with invalid version prefix: %s", file_path.name)
                continue

            if version in applied_versions:
                continue

            logger.info("Applying migration %d: %s", version, file_path.name)
            script_content = file_path.read_text(encoding="utf-8")

            # Execute migration and record in a single atomic transaction
            await active_conn.executescript(script_content)
            now_ms = int(time.time() * 1000)
            await active_conn.execute(
                "INSERT INTO schema_migrations (version, name, applied_at_ms) VALUES (?, ?, ?)",
                (version, file_path.name, now_ms),
            )
            await active_conn.commit()
            applied_count += 1
            logger.info("Successfully applied migration %d (%s)", version, file_path.name)

        return applied_count

    async def get_journal_mode(self) -> str:
        """Query and return current SQLite journal mode."""
        conn = await self.connect()
        async with conn.execute("PRAGMA journal_mode;") as cursor:
            row = await cursor.fetchone()
            return str(row[0]).upper() if row else "UNKNOWN"

    async def get_applied_migrations(self) -> List[Tuple[int, str, int]]:
        """Return list of applied migrations as (version, name, applied_at_ms)."""
        conn = await self.connect()
        async with conn.execute(
            "SELECT version, name, applied_at_ms FROM schema_migrations ORDER BY version ASC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [(r[0], r[1], r[2]) for r in rows]

    async def get_table_names(self) -> List[str]:
        """Query list of all user tables in the database."""
        conn = await self.connect()
        async with conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name ASC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [str(r[0]) for r in rows]

    async def execute(self, query: str, parameters: Sequence[Any] = ()) -> aiosqlite.Cursor:
        """Execute a single SQL command with parameters."""
        conn = await self.connect()
        return await conn.execute(query, parameters)

    async def execute_commit(self, query: str, parameters: Sequence[Any] = ()) -> aiosqlite.Cursor:
        """Execute a single SQL command and commit the transaction."""
        conn = await self.connect()
        cursor = await conn.execute(query, parameters)
        await conn.commit()
        return cursor

    async def fetch_one(self, query: str, parameters: Sequence[Any] = ()) -> Optional[aiosqlite.Row]:
        """Fetch a single matching row."""
        conn = await self.connect()
        async with conn.execute(query, parameters) as cursor:
            return await cursor.fetchone()

    async def fetch_all(self, query: str, parameters: Sequence[Any] = ()) -> List[aiosqlite.Row]:
        """Fetch all matching rows."""
        conn = await self.connect()
        async with conn.execute(query, parameters) as cursor:
            return await cursor.fetchall()

    async def close(self) -> None:
        """Safely close active database connection."""
        async with self._lock:
            if self._connection is not None:
                try:
                    await self._connection.close()
                    logger.info("SQLite connection closed cleanly")
                except Exception as e:
                    logger.warning("Error closing SQLite connection: %s", e)
                finally:
                    self._connection = None
                    self._initialized = False
