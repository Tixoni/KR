import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import typing as _t
import pytest

TEST_DIR = os.path.dirname(__file__)
SERVICE_ROOT = os.path.abspath(os.path.join(TEST_DIR, ".."))

# Use an isolated SQLite database for tests to avoid hitting Postgres
os.environ.setdefault("DATABASE_URL", "sqlite:///./auth_test.db")

if SERVICE_ROOT not in sys.path:
    sys.path.insert(0, SERVICE_ROOT)

from src.main import app  # noqa: E402
from src.database import get_db, Base  # noqa: E402


_engine = create_engine(
    os.environ["DATABASE_URL"],
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
Base.metadata.create_all(bind=_engine)


def _test_get_db() -> _t.Iterator[TestingSessionLocal]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def _override_db_dependency():
    app.dependency_overrides[get_db] = _test_get_db
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_db, None)
