"""The orders database (Postgres) and the legacy billing database (MySQL)."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app import config


class Base(DeclarativeBase):
    pass


class LegacyBase(DeclarativeBase):
    pass


engine = create_engine(config.sqlalchemy_url(config.DATABASE_URL), pool_pre_ping=True)
legacy_engine = create_engine(config.sqlalchemy_url(config.LEGACY_DB_URL), pool_pre_ping=True)
Session = sessionmaker(bind=engine, expire_on_commit=False)
LegacySession = sessionmaker(bind=legacy_engine, expire_on_commit=False)


def init_db() -> None:
    from app import models  # noqa: F401  registers the tables

    Base.metadata.create_all(engine)
    LegacyBase.metadata.create_all(legacy_engine)
