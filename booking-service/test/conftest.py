import os
import sys
from types import SimpleNamespace
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import typing as _t
import pytest

TEST_DIR = os.path.dirname(__file__)
SERVICE_ROOT = os.path.abspath(os.path.join(TEST_DIR, ".."))

# Use isolated SQLite DB for tests
os.environ.setdefault("DATABASE_URL", "sqlite:///./booking_test.db")

if SERVICE_ROOT not in sys.path:
    sys.path.insert(0, SERVICE_ROOT)

from src.main import app, get_current_user, security  # noqa: E402
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


def _override_current_user() -> str:
    return "test-user"


def _override_security():
    return SimpleNamespace(credentials="test-token")


@pytest.fixture(autouse=True)
def _override_dependencies():
    app.dependency_overrides[get_db] = _test_get_db
    app.dependency_overrides[get_current_user] = _override_current_user
    app.dependency_overrides[security] = _override_security
    try:
        yield
    finally:
        app.dependency_overrides.clear()
