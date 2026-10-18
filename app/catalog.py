"""Product prices, cached in Redis."""

import json

import redis

from app import config

PRICES = {"keyboard": 49.0, "mouse": 19.5, "monitor": 189.0, "cable": 7.25}

_redis = redis.Redis.from_url(config.REDIS_URL, decode_responses=True)


def price_of(product: str) -> float | None:
    cached = _redis.get(f"price:{product}")
    if cached is not None:
        return json.loads(cached)
    price = PRICES.get(product)
    if price is not None:
        _redis.set(f"price:{product}", json.dumps(price), ex=300)
    return price


def allow_request(client: str) -> bool:
    """A fixed window of RATE_LIMIT_PER_MINUTE requests per client."""
    key = f"rate:{client}"
    count = _redis.incr(key)
    if count == 1:
        _redis.expire(key, 60)
    return count <= config.RATE_LIMIT_PER_MINUTE


def redis_client() -> redis.Redis:
    return _redis
