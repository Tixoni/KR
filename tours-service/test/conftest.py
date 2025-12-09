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


class _FakeQuery:
    def filter(self, *args, **kwargs):
        return self

    def offset(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def all(self):
        return []


class _FakeSession:
    def query(self, *args, **kwargs):
        return _FakeQuery()


def _fake_get_db() -> _t.Iterator[_FakeSession]:
    yield _FakeSession()


@pytest.fixture(autouse=True)
def _override_db_dependency():
    app.dependency_overrides[get_db] = _fake_get_db
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_db, None)


