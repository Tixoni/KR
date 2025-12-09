import os
import sys
import typing as _t

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


SERVICE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "auth-service"))
if SERVICE_ROOT not in sys.path:
    sys.path.insert(0, SERVICE_ROOT)

from src.main import app  # noqa: E402
from src.database import get_db, Base  # noqa: E402


_engine = create_engine(
    os.environ.get("DATABASE_URL", "sqlite:///./auth_test.db"),
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
def auth_service_overrides(request):
    # Apply only to tests located in auth-service/test
    if "auth-service" not in str(request.fspath):
        yield
        return

    app.dependency_overrides[get_db] = _test_get_db
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_db, None)


