from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings


def _is_sqlite(database_url: str) -> bool:
    return make_url(database_url).drivername.startswith("sqlite")


def _ensure_sqlite_parent_dir(database_url: str) -> None:
    url = make_url(database_url)
    if not url.drivername.startswith("sqlite") or not url.database:
        return
    if url.database == ":memory:":
        return
    Path(url.database).parent.mkdir(parents=True, exist_ok=True)


def _engine_kwargs(database_url: str) -> dict:
    if _is_sqlite(database_url):
        _ensure_sqlite_parent_dir(database_url)
        return {"connect_args": {"check_same_thread": False}}

    return {
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20,
    }


engine = create_engine(settings.database_url, **_engine_kwargs(settings.database_url))

if _is_sqlite(settings.database_url):
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all_tables():
    Base.metadata.create_all(bind=engine)
