import pytest

from app import create_app
from app.catalog import redis_client


@pytest.fixture()
def client():
    # Every test starts with fresh rate-limit windows.
    for key in redis_client().scan_iter("rate:*"):
        redis_client().delete(key)
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()
