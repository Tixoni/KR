import os
import sys
import typing as _t

import pytest


SERVICE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "tours-service"))
if SERVICE_ROOT not in sys.path:
    sys.path.insert(0, SERVICE_ROOT)

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
def tours_service_overrides(request):
    # Apply only to tests located in tours-service/test
    if "tours-service" not in str(request.fspath):
        yield
        return

    app.dependency_overrides[get_db] = _fake_get_db
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_db, None)


