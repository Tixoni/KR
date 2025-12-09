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
# Skip heavy migrations in tests
os.environ.setdefault("SKIP_TOURS_MIGRATE", "1")

ROOT = Path(__file__).resolve().parent
_AUTH_ENGINES = {}
_BOOKING_ENGINES = {}
_TOURS_ENGINES = {}


def _ensure_path(path: Path):
    pstr = str(path)
    if pstr not in sys.path:
        sys.path.insert(0, pstr)


def _in_service(request, service_name: str) -> bool:
    try:
        return service_name in Path(request.fspath).resolve().parts
    except Exception:
        return service_name in str(request.fspath)


def _clear_src_modules():
    # Drop cached modules so each service loads its own src package
    for name in list(sys.modules.keys()):
        if name == "src" or name.startswith("src."):
            sys.modules.pop(name, None)


# ---------- Auth service fixtures ----------
def _setup_auth():
    try:
        service_root = ROOT / "auth-service"
        _ensure_path(service_root)
        _clear_src_modules()
        from src.main import app  # type: ignore
        from src.database import get_db, Base  # type: ignore
        import src.models  # noqa: F401  # ensure models are registered
    except Exception:
        return None

    worker = os.getenv("PYTEST_XDIST_WORKER", "gw0")
    db_path = ROOT / f".auth_test_{worker}.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

    if worker not in _AUTH_ENGINES:
        engine = create_engine(
            os.environ["DATABASE_URL"],
            connect_args={"check_same_thread": False},
        )
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        # FIX: Сначала удаляем таблицы, потом создаём
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        _AUTH_ENGINES[worker] = (engine, TestingSessionLocal)
    else:
        _, TestingSessionLocal = _AUTH_ENGINES[worker]

    return app, get_db, TestingSessionLocal


@pytest.fixture(autouse=True)
def _auth_service_overrides(request):
    setup = _setup_auth()
    if setup is None:
        yield
        return

    app, get_db, TestingSessionLocal = setup

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
def _setup_booking():
    try:
        service_root = ROOT / "booking-service"
        _ensure_path(service_root)
        _clear_src_modules()
        from src.main import app, get_current_user, security  # type: ignore
        from src.database import get_db, Base  # type: ignore
        import src.models  # noqa: F401  # register models
    except Exception:
        return None

    worker = os.getenv("PYTEST_XDIST_WORKER", "gw0")
    db_path = ROOT / f".booking_test_{worker}.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

    if worker not in _BOOKING_ENGINES:
        engine = create_engine(
            os.environ["DATABASE_URL"],
            connect_args={"check_same_thread": False},
        )
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        # FIX: Сначала удаляем таблицы, потом создаём
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        _BOOKING_ENGINES[worker] = (engine, TestingSessionLocal)
    else:
        _, TestingSessionLocal = _BOOKING_ENGINES[worker]

    return app, get_db, get_current_user, security, TestingSessionLocal


@pytest.fixture(autouse=True)
def _booking_service_overrides(request):
    setup = _setup_booking()
    if setup is None:
        yield
        return

    app, get_db, get_current_user, security, TestingSessionLocal = setup

    def _test_get_db() -> _t.Iterator[TestingSessionLocal]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    def _override_current_user() -> dict:
        # Возвращаем словарь вместо строки для совместимости
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


# ---------- Tours service fixtures ----------
@pytest.fixture(autouse=True)
def _tours_service_overrides(request):
    try:
        service_root = ROOT / "tours-service"
        _ensure_path(service_root)
        _clear_src_modules()

        # Use an isolated sqlite DB per worker with real models so queries succeed with empty data
        worker = os.getenv("PYTEST_XDIST_WORKER", "gw0")
        db_path = ROOT / f".tours_test_{worker}.db"
        os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
        _clear_src_modules()

        from src.main import app  # type: ignore
        from src.database import get_db, Base  # type: ignore
        import src.models  # noqa: F401  # register models
    except Exception:
        yield
        return

    if worker not in _TOURS_ENGINES:
        engine = create_engine(
            os.environ["DATABASE_URL"],
            connect_args={"check_same_thread": False},
        )
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        # FIX: Сначала удаляем таблицы, потом создаём
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        _TOURS_ENGINES[worker] = (engine, TestingSessionLocal)
    else:
        engine, TestingSessionLocal = _TOURS_ENGINES[worker]

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


# ---------- Cleanup after all tests ----------
@pytest.fixture(scope="session", autouse=True)
def cleanup_test_dbs():
    """Clean up test database files after all tests."""
    yield
    
    # Удаляем все тестовые файлы БД
    import glob
    test_dbs = glob.glob(str(ROOT / ".*_test_*.db"))
    for db_file in test_dbs:
        try:
            os.remove(db_file)
            print(f"Cleaned up test DB: {db_file}")
        except Exception as e:
            print(f"Failed to clean up {db_file}: {e}")