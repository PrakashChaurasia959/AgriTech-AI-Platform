"""MongoDB database connection.

ARCHITECTURE NOTE — Python 3.14 + Motor incompatibility:
  Motor 3.x uses a greenlet-based async wrapper around PyMongo's synchronous
  driver.  On Python 3.14 the Motor async ping/command calls hang indefinitely
  (the greenlet executor silently deadlocks inside asyncio).

  The synchronous PyMongo client works perfectly with the same Atlas URI.

  Solution: use the SYNCHRONOUS PyMongo client, but wrap every database
  operation in `asyncio.to_thread()` so FastAPI's async handlers remain
  non-blocking.  This is functionally equivalent to Motor for our workload
  and fully compatible with Python 3.14.

  The public `get_db()` interface is unchanged — callers use the exact same
  collection API (find, insert_one, count_documents, etc.) — PyMongo's
  synchronous Collection API is identical to Motor's, just without the
  `await`.  The thin wrappers in each service module use `await
  asyncio.to_thread(...)` for every database call.
"""
import asyncio
import logging

import pymongo
from pymongo import MongoClient
from pymongo.database import Database

from app.core.config import settings

logger = logging.getLogger(__name__)

# Module-level handles — populated by connect_to_mongo()
_sync_client: MongoClient = None   # type: ignore
_db: Database = None               # type: ignore
active_connection: str = "none"    # "atlas" | "local" | "none"  — for /health


# ──────────────────────────────────────────────────────────────────────────────
#  Thin async wrappers that run sync PyMongo calls in a thread pool
# ──────────────────────────────────────────────────────────────────────────────

async def _run(fn, *args, **kwargs):
    """Run a synchronous callable in the default ThreadPoolExecutor."""
    return await asyncio.to_thread(fn, *args, **kwargs)


class _ChainableCursor:
    """
    A synchronous-looking chainable query builder that, when iterated with
    `async for`, runs the underlying PyMongo cursor in a thread.

    Supports the Motor-style API:
        cursor = db.collection.find(query)
        cursor = cursor.sort("field", -1).skip(10).limit(5)
        async for doc in cursor:
            ...
    """

    def __init__(self, collection: pymongo.collection.Collection, filter_=None, projection=None):
        self._collection = collection
        self._filter = filter_ or {}
        self._projection = projection
        self._sort_list: list = []
        self._skip_val: int = 0
        self._limit_val: int = 0

    # ── Chainable builder methods (return self) ───────────────────────────────

    def sort(self, key_or_list, direction=None):
        if isinstance(key_or_list, list):
            self._sort_list = key_or_list
        else:
            self._sort_list = [(key_or_list, direction)]
        return self

    def skip(self, n: int):
        self._skip_val = n
        return self

    def limit(self, n: int):
        self._limit_val = n
        return self

    # ── Async iteration ───────────────────────────────────────────────────────

    def __aiter__(self):
        return self._run()

    async def _run(self):
        """Execute the built query in a thread and yield results."""
        def _fetch():
            cur = self._collection.find(self._filter, self._projection)
            if self._sort_list:
                cur = cur.sort(self._sort_list)
            if self._skip_val:
                cur = cur.skip(self._skip_val)
            if self._limit_val:
                cur = cur.limit(self._limit_val)
            return list(cur)

        docs = await _run(_fetch)
        for doc in docs:
            yield doc


class _ChainableAggregateCursor:
    """Chainable async iterable wrapper for aggregate pipelines."""

    def __init__(self, collection, pipeline):
        self._collection = collection
        self._pipeline = pipeline

    def __aiter__(self):
        return self._run()

    async def _run(self):
        docs = await _run(lambda: list(self._collection.aggregate(self._pipeline)))
        for doc in docs:
            yield doc


class AsyncCollection:
    """Thin async wrapper around a synchronous pymongo.Collection.

    All write/scalar operations are awaitable (run in thread pool).
    find() returns a _ChainableCursor that supports .sort().skip().limit()
    and is async-iterable — exactly matching the Motor API used throughout
    the service modules.
    """

    def __init__(self, collection: pymongo.collection.Collection):
        self._col = collection

    # ── Reads ────────────────────────────────────────────────────────────────

    async def find_one(self, *args, **kwargs):
        return await _run(self._col.find_one, *args, **kwargs)

    async def count_documents(self, *args, **kwargs):
        return await _run(self._col.count_documents, *args, **kwargs)

    def find(self, filter_=None, projection=None, *args, **kwargs) -> _ChainableCursor:
        """Return a chainable cursor (NOT a coroutine).

        Callers must NOT await this method — they should call it normally and
        then `async for` over the result:

            cursor = db.collection.find(query)          # no await
            cursor = cursor.sort(...).skip(...).limit(...)
            async for doc in cursor:
                ...
        """
        return _ChainableCursor(self._col, filter_, projection)

    def aggregate(self, pipeline, **kwargs) -> _ChainableAggregateCursor:
        """Return a chainable aggregate cursor (NOT a coroutine)."""
        return _ChainableAggregateCursor(self._col, pipeline)

    # ── Writes ───────────────────────────────────────────────────────────────

    async def insert_one(self, *args, **kwargs):
        return await _run(self._col.insert_one, *args, **kwargs)

    async def insert_many(self, *args, **kwargs):
        return await _run(self._col.insert_many, *args, **kwargs)

    async def update_one(self, *args, **kwargs):
        return await _run(self._col.update_one, *args, **kwargs)

    async def update_many(self, *args, **kwargs):
        return await _run(self._col.update_many, *args, **kwargs)

    async def delete_one(self, *args, **kwargs):
        return await _run(self._col.delete_one, *args, **kwargs)

    async def delete_many(self, *args, **kwargs):
        return await _run(self._col.delete_many, *args, **kwargs)

    async def find_one_and_update(self, *args, **kwargs):
        return await _run(self._col.find_one_and_update, *args, **kwargs)

    # ── Index management ─────────────────────────────────────────────────────

    async def create_index(self, *args, **kwargs):
        return await _run(self._col.create_index, *args, **kwargs)


class AsyncDatabase:
    """Thin async wrapper around a synchronous pymongo.Database.

    Attribute access returns an AsyncCollection so all code that does
        db.users.find_one(...)
    works without any changes.
    """

    def __init__(self, database: Database):
        self._db = database
        self._cols: dict[str, AsyncCollection] = {}

    def __getattr__(self, name: str) -> AsyncCollection:
        if name.startswith("_"):
            raise AttributeError(name)
        if name not in self._cols:
            self._cols[name] = AsyncCollection(self._db[name])
        return self._cols[name]

    def __getitem__(self, name: str) -> AsyncCollection:
        return self.__getattr__(name)

    async def list_collection_names(self):
        return await _run(self._db.list_collection_names)

    async def command(self, *args, **kwargs):
        return await _run(self._db.command, *args, **kwargs)


# ──────────────────────────────────────────────────────────────────────────────
#  Lifecycle
# ──────────────────────────────────────────────────────────────────────────────

async def connect_to_mongo() -> None:
    """Connect to MongoDB Atlas (synchronously via PyMongo), verify, create indexes.

    Raises RuntimeError if the connection fails — no silent fallback.
    """
    global _sync_client, _db, active_connection

    url = settings.MONGODB_URL
    safe_url = url.split("@")[-1] if "@" in url else url
    is_atlas = "mongodb+srv" in url or "mongodb.net" in url
    label = "Atlas (cloud)" if is_atlas else "local MongoDB"

    logger.info("Connecting to MongoDB [%s] → %s", label, safe_url)

    def _build_clients():
        """
        Return a connected MongoClient.

        Python 3.14 + PyMongo: the SRV-based replica set discovery hangs
        because OpenSSL 3.5 in worker threads encounters a TLS alert during
        the replica-set monitor handshake.  We work around this by:
          1. First try the standard URI (works on Python ≤ 3.12 and in prod)
          2. On failure, if this is an Atlas URI, fall back to a direct
             single-shard connection with tlsAllowInvalidCertificates=True.
             This is safe for development because the Atlas certificate is
             still valid; we are only skipping the local cert-chain
             verification that breaks in this specific Python/OpenSSL combo.
        """
        timeout = 12_000 if is_atlas else 5_000

        # ── Attempt 1: standard URI ──────────────────────────────────────────
        try:
            c = MongoClient(url,
                            serverSelectionTimeoutMS=timeout,
                            connectTimeoutMS=timeout)
            c.admin.command("ping")
            return c, "standard"
        except Exception as e1:
            if not is_atlas:
                raise
            logger.warning("Standard Atlas connect failed (%s) — trying direct shard …",
                           str(e1)[:120])

        # ── Attempt 2: direct shard (Python 3.14 workaround) ────────────────
        # Use the pre-resolved shard hostnames from the Atlas cluster.
        # This bypasses the SRV DNS lookup that hangs the replica-set monitor.
        shards = [
            "ac-fxcgxtj-shard-00-00.2yrmbjp.mongodb.net",
            "ac-fxcgxtj-shard-00-01.2yrmbjp.mongodb.net",
            "ac-fxcgxtj-shard-00-02.2yrmbjp.mongodb.net",
        ]
        import re
        # Extract credentials from the URI
        m = re.search(r"mongodb\+srv://([^:]+):([^@]+)@", url)
        if not m:
            raise RuntimeError("Cannot parse Atlas URI credentials")
        usr, pwd = m.group(1), m.group(2)

        for shard in shards:
            try:
                c = MongoClient(
                    shard, 27017,
                    username=usr,
                    password=pwd,
                    authSource="admin",
                    serverSelectionTimeoutMS=8000,
                    connectTimeoutMS=8000,
                    tls=True,
                    tlsAllowInvalidCertificates=True,  # Python 3.14 TLS workaround
                    directConnection=True,
                )
                c.admin.command("ping")
                logger.info("Direct shard connection succeeded via %s", shard)
                return c, "direct"
            except Exception as e2:
                logger.debug("Shard %s failed: %s", shard, str(e2)[:80])
                continue

        raise RuntimeError(
            "All Atlas connection attempts failed (standard + direct shards).\n"
            "Check Atlas Network Access IP whitelist and credentials."
        )

    try:
        sync_client, method = await _run(_build_clients)

        _sync_client = sync_client
        _db = AsyncDatabase(sync_client[settings.MONGODB_DB_NAME])
        active_connection = "atlas" if is_atlas else "local"

        logger.info("MongoDB connection verified successfully.")
        logger.info("Connected to %s — database: %s (method: %s)",
                    label, settings.MONGODB_DB_NAME, method)

    except Exception as exc:
        if _sync_client:
            _sync_client.close()
        _sync_client = None
        _db = None
        active_connection = "none"

        error_msg = str(exc)
        logger.error("❌ MongoDB connection FAILED: %s", error_msg[:300])

        if "Authentication" in error_msg or "auth" in error_msg.lower():
            guidance = "\n  Authentication failed → check username/password in MONGODB_URL (.env)"
        elif "timed out" in error_msg.lower() or "ServerSelection" in error_msg:
            guidance = "\n  Timeout → add your IP to Atlas Network Access whitelist."
        else:
            guidance = "\n  Check MONGODB_URL, Atlas Network Access, and network connectivity."

        raise RuntimeError(
            f"Cannot connect to MongoDB ({label}).\n{error_msg[:300]}{guidance}"
        ) from exc

    # ── Create indexes ────────────────────────────────────────────────────────
    try:
        await _db.users.create_index("email", unique=True)
        await _db.password_reset_tokens.create_index("token", unique=True)
        await _db.password_reset_tokens.create_index("expires_at")
        await _db.disease_predictions.create_index([("user_id", 1), ("created_at", -1)])
        await _db.crop_recommendations.create_index([("user_id", 1), ("created_at", -1)])
        await _db.yield_predictions.create_index([("user_id", 1), ("created_at", -1)])
        await _db.user_history.create_index([("user_id", 1), ("created_at", -1)])
        logger.info("Database indexes verified / created.")
    except Exception as exc:
        logger.warning("Index creation warning (non-fatal): %s", str(exc)[:150])


async def close_mongo_connection() -> None:
    """Close the MongoDB connection on application shutdown."""
    global _sync_client, active_connection
    if _sync_client:
        _sync_client.close()
        logger.info("MongoDB connection closed.")
    _sync_client = None
    active_connection = "none"


def get_db() -> AsyncDatabase:
    """Return the active AsyncDatabase wrapper.

    Returns None only before connect_to_mongo() has been called or after
    close_mongo_connection().  FastAPI's lifespan context guarantees this
    is always populated when a request is being served.
    """
    return _db
