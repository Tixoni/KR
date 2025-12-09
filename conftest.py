import os
import sys
import typing as t
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Force tests to use local SQLite instead of Postgres and skip heavy migrations
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("SKIP_TOURS_MIGRATE", "1")

ROOT = Path(__file__).resolve().parent
_AUTH_ENGINES: dict[str, tuple[object, object]] = {}
_BOOKING_ENGINES: dict[str, tuple[object, object]] = {}
_TOURS_ENGINES: dict[str, tuple[object, object]] = {}


def _ensure_path(path: Path):
    pstr = str(path)
    if pstr not in sys.path:
        sys.path.insert(0, pstr)


def _clear_src_modules():
    for name in list(sys.modules.keys()):
        if name == "src" or name.startswith("src."):
            del sys.modules[name]


def _in_service(request, name: str) -> bool:
    try:
        return name in Path(request.fspath).resolve().parts
    except Exception:
        return name in str(request.fspath)


# ---------- Auth service ----------
@pytest.fixture(autouse=True)
def _auth_service_overrides(request):
    if not _in_service(request, "auth-service"):
        yield
        return

    _ensure_path(ROOT / "auth-service")
    _clear_src_modules()

    from src.main import app  # type: ignore
    from src.database import get_db, Base  # type: ignore
    import src.models  # noqa: F401

    worker = os.getenv("PYTEST_XDIST_WORKER", "gw0")
    db_path = ROOT / f".auth_test_{worker}.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

    if worker not in _AUTH_ENGINES:
        engine = create_engine(
            os.environ["DATABASE_URL"],
            connect_args={"check_same_thread": False},
        )
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base.metadata.create_all(bind=engine, checkfirst=True)
        _AUTH_ENGINES[worker] = (engine, TestingSessionLocal)
    else:
        _, TestingSessionLocal = _AUTH_ENGINES[worker]

    def _test_get_db() -> t.Iterator[object]:
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


# ---------- Booking service ----------
@pytest.fixture(autouse=True)
def _booking_service_overrides(request):
    if not _in_service(request, "booking-service"):
        yield
        return

    _ensure_path(ROOT / "booking-service")
    _clear_src_modules()

    from src.main import app, get_current_user, security  # type: ignore
    from src.database import get_db, Base  # type: ignore
    import src.models  # noqa: F401

    worker = os.getenv("PYTEST_XDIST_WORKER", "gw0")
    db_path = ROOT / f".booking_test_{worker}.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

    if worker not in _BOOKING_ENGINES:
        engine = create_engine(
            os.environ["DATABASE_URL"],
            connect_args={"check_same_thread": False},
        )
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base.metadata.create_all(bind=engine, checkfirst=True)
        _BOOKING_ENGINES[worker] = (engine, TestingSessionLocal)
    else:
        _, TestingSessionLocal = _BOOKING_ENGINES[worker]

    def _test_get_db() -> t.Iterator[object]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    def _override_current_user() -> dict:
        return {"id": 1, "username": "test-user", "email": "test@example.com"}

    def _override_security():
        return SimpleNamespace(credentials="test-token")

    app.dependency_overrides[get_db] = _test_get_db
    app.dependency_overrides[get_current_user] = _override_current_user
    app.dependency_overrides[security] = _override_security
    try:
        yield
    finally:
        app.dependency_overrides.clear()


# ---------- Tours service ----------
@pytest.fixture(autouse=True)
def _tours_service_overrides(request):
    if not _in_service(request, "tours-service"):
        yield
        return

    _ensure_path(ROOT / "tours-service")
    _clear_src_modules()

    worker = os.getenv("PYTEST_XDIST_WORKER", "gw0")
    db_path = ROOT / f".tours_test_{worker}.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    _clear_src_modules()

    from src.main import app  # type: ignore
    from src.database import get_db, Base  # type: ignore
    import src.models  # noqa: F401

    if worker not in _TOURS_ENGINES:
        engine = create_engine(
            os.environ["DATABASE_URL"],
            connect_args={"check_same_thread": False},
        )
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base.metadata.create_all(bind=engine, checkfirst=True)
        _TOURS_ENGINES[worker] = (engine, TestingSessionLocal)
    else:
        _, TestingSessionLocal = _TOURS_ENGINES[worker]

    def _test_get_db() -> t.Iterator[object]:
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