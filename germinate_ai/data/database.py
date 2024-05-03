from typing import Any, Literal

from loguru import logger
from sqlalchemy import JSON, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from germinate_ai.config import settings

DB_URL = settings.database_url


def create_db_engine(db_url=DB_URL):
    """Create a SQLAlchemy engine."""
    engine = create_engine(db_url)
    return engine


def get_db_session(engine=None, db_url: str = DB_URL):
    """Create a SQLAlchemy session factory."""
    if engine is None:
        engine = create_db_engine(db_url)
    Session = sessionmaker(autoflush=False, bind=engine)
    return Session


class Base(DeclarativeBase):
    type_annotation_map = {dict[str, Any]: JSON}


def create_tables(engine=None):
    """Create all defined tables -- DEV ONLY."""
    if engine is None:
        engine = create_db_engine(db_url=DB_URL)
    logger.info("Creating all tables...")
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get a SQLALchemy session."""
    Session = get_db_session()
    with Session() as db:
        yield db


def test_db_connection(db: Session) -> Exception | Literal[True]:
    """Test connection to DB."""
    try:
        db.execute(select(1))
        return True
    except Exception as e:
        return e
