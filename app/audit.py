"""An append-only audit log of order events in MongoDB."""

from datetime import datetime, timezone

from pymongo import MongoClient

from app import config

_client = MongoClient(config.MONGODB_URI, serverSelectionTimeoutMS=5000)
_log = _client.get_default_database("app")["order_audit"]


def record(order_id: int, event: str, detail: dict | None = None) -> None:
    _log.insert_one(
        {
            "order_id": order_id,
            "event": event,
            "detail": detail or {},
            "at": datetime.now(timezone.utc),
        }
    )


def history(order_id: int) -> list[dict]:
    return [
        {"event": doc["event"], "detail": doc["detail"]}
        for doc in _log.find({"order_id": order_id}).sort("at", 1)
    ]
