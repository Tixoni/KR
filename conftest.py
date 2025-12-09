import os
import sys
import typing as _t
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Force tests to use local SQLite instead of Postgres by default
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")


ROOT = Path(__file__).resolve().parent


def _ensure_path(path: Path):
    pstr = str(path)
    if pstr not in sys.path:
        sys.path.insert(0, pstr)


def _clear_src_modules():
    # Drop cached modules so each service loads its own src package
    for name in list(sys.modules.keys()):
        if name == "src" or name.startswith("src."):
            sys.modules.pop(name, None)


# ---------- Auth service fixtures ----------
@pytest.fixture(autouse=True)
def _auth_service_overrides(request):
    if "auth-service" not in str(request.fspath):
        yield
        return

    service_root = ROOT / "auth-service"
    _ensure_path(service_root)
    _clear_src_modules()

    from src.main import app  # type: ignore
    from src.database import get_db, Base  # type: ignore

    engine = create_engine(
        os.environ.get("DATABASE_URL", "sqlite:///./auth_test.db"),
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def _test_get_db() -> _t.Iterator[TestingSessionLocal]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _test_get_db
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_db, None)


# ---------- Booking service fixtures ----------
@pytest.fixture(autouse=True)
def _booking_service_overrides(request):
    if "booking-service" not in str(request.fspath):
        yield
        return

    service_root = ROOT / "booking-service"
    _ensure_path(service_root)
    _clear_src_modules()

    from src.main import app, get_current_user, security  # type: ignore
    from src.database import get_db, Base  # type: ignore

    engine = create_engine(
        os.environ.get("DATABASE_URL", "sqlite:///./booking_test.db"),
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

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

    app.dependency_overrides[get_db] = _test_get_db
    app.dependency_overrides[get_current_user] = _override_current_user
    app.dependency_overrides[security] = _override_security
    try:
        yield
    finally:
        app.dependency_overrides.clear()


# ---------- Tours service fixtures ----------
@pytest.fixture(autouse=True)
def _tours_service_overrides(request):
    if "tours-service" not in str(request.fspath):
        yield
        return

    service_root = ROOT / "tours-service"
    _ensure_path(service_root)
    _clear_src_modules()

    from src.main import app  # type: ignore
    from src.database import get_db  # type: ignore

    class _FakeQuery:
        def filter(self, *args, **kwargs):
            return self

        def offset(self, *args, **kwargs):
            return self

        def limit(self, *args, **kwargs):
            return self

        def all(self):
            return []

        def first(self):
            return None

    class _FakeSession:
        def query(self, *args, **kwargs):
            return _FakeQuery()

    def _fake_get_db() -> _t.Iterator[_FakeSession]:
        yield _FakeSession()

    app.dependency_overrides[get_db] = _fake_get_db
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_db, None)

