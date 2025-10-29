import os
import sys


TEST_DIR = os.path.dirname(__file__)
SERVICE_ROOT = os.path.abspath(os.path.join(TEST_DIR, ".."))

if SERVICE_ROOT not in sys.path:
    sys.path.insert(0, SERVICE_ROOT)

# Provide a DB override that doesn't hit a real database
import typing as _t  # noqa: E402
import pytest  # noqa: E402
from src.main import app  # noqa: E402
from src.database import get_db  # noqa: E402


class _FakeSession:
    def execute(self, *args, **kwargs):  # health may call raw SQL
        class _Res:
            def fetchone(self):
                return (1,)
        return _Res()


def _fake_get_db() -> _t.Iterator[_FakeSession]:
    yield _FakeSession()


@pytest.fixture(autouse=True)
def _override_db_dependency():
    app.dependency_overrides[get_db] = _fake_get_db
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_db, None)


