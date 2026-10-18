"""Every setting comes from the environment."""

import os

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://app:app@localhost:5432/app")
LEGACY_DB_URL = os.environ.get("LEGACY_DB_URL", "mysql://app:app@localhost:3306/legacy")
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/app")
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
AMQP_URL = os.environ.get("AMQP_URL", "amqp://app:app@localhost:5672/")
ORDER_EVENTS_QUEUE = "order_events"
RATE_LIMIT_PER_MINUTE = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "600"))


def sqlalchemy_url(url: str) -> str:
    """The URL with the driver SQLAlchemy needs for it."""
    scheme, _, rest = url.partition("://")
    if scheme in ("postgres", "postgresql"):
        return f"postgresql+psycopg://{rest}"
    if scheme == "mysql":
        return f"mysql+pymysql://{rest}"
    return url
