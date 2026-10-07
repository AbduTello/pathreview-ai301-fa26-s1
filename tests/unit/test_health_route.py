"""Tests for the /health route's postgres probe."""

from typing import Any

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from api.routes.health import health_check


class SqliteBackedSession:
    """Async stand-in for AsyncSession that runs statements through real SQLAlchemy 2.x."""

    def __init__(self) -> None:
        self._session = Session(create_engine("sqlite://"))

    async def execute(self, statement):
        return self._session.execute(statement)

    def close(self) -> None:
        self._session.close()


async def _run_health_check(db) -> Any:
    # Other dependencies (e.g. redis, issue #62) may still fail and raise 503;
    # the body is the same either way.
    try:
        return await health_check(db=db)
    except HTTPException as exc:
        return exc.detail


@pytest.mark.unit
class TestHealthPostgresProbe:
    """The postgres probe must pass against a reachable database under SQLAlchemy 2.x."""

    @pytest.mark.asyncio
    async def test_postgres_reported_healthy_when_database_answers(self):
        db = SqliteBackedSession()
        try:
            body = await _run_health_check(db)
        finally:
            db.close()

        assert body["dependencies"]["postgres"] == "healthy"
