from __future__ import annotations

from sqlalchemy.exc import OperationalError

from backend.database import session as db_session


class _Boom:
    def __init__(self, *args, **kwargs):
        raise OperationalError("connect", {}, Exception("boom"))


def test_init_db_is_atomic_on_failure(monkeypatch):
    monkeypatch.setattr(db_session, "_engine", None)
    monkeypatch.setattr(db_session, "_session_factory", None)
    monkeypatch.setattr(db_session, "create_engine", _Boom)

    try:
        db_session.init_db("postgresql://localhost/test")
    except OperationalError:
        pass

    assert db_session._engine is None
    assert db_session._session_factory is None
