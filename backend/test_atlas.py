"""Verify MongoDB Atlas connectivity using the application's configured URI."""
from pymongo import MongoClient

from app.core.config import settings


def main() -> int:
    if not settings.MONGODB_URL.startswith("mongodb+srv://"):
        print("MongoDB Atlas connection: NOT_CONFIGURED")
        return 1

    client = MongoClient(
        settings.MONGODB_URL,
        serverSelectionTimeoutMS=12_000,
    )
    try:
        client.admin.command("ping")
    except Exception as exc:
        print(f"MongoDB Atlas connection: FAIL ({type(exc).__name__})")
        return 1
    finally:
        client.close()

    print("MongoDB Atlas connection: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
