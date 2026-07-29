"""Tests for the standalone MagicAir cloud client."""

from __future__ import annotations

from collections import deque
from typing import Any

import pytest

from custom_components.magicair.api import (
    MagicAirApi,
    MagicAirAuthenticationError,
)
from custom_components.magicair.const import API_BASE_URL, OAUTH_TOKEN_PATH


class FakeResponse:
    """Small aiohttp response double."""

    def __init__(self, status: int, payload: Any = None) -> None:
        self.status = status
        self._payload = payload
        self.released = False

    async def json(self, *, content_type: str | None = None) -> Any:
        """Return the configured JSON payload."""
        return self._payload

    def release(self) -> None:
        """Mark the response as released."""
        self.released = True


class FakeSession:
    """Small aiohttp session double with separate auth and API queues."""

    def __init__(
        self,
        *,
        auth: list[FakeResponse],
        requests: list[FakeResponse],
    ) -> None:
        self.auth_responses = deque(auth)
        self.request_responses = deque(requests)
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    async def post(self, url: str, **kwargs: Any) -> FakeResponse:
        """Return the next authentication response."""
        self.calls.append(("POST", url, kwargs))
        return self.auth_responses.popleft()

    async def request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> FakeResponse:
        """Return the next general API response."""
        self.calls.append((method, url, kwargs))
        return self.request_responses.popleft()


@pytest.mark.asyncio
async def test_get_locations_authenticates() -> None:
    """The client exchanges credentials for a token before loading homes."""
    session = FakeSession(
        auth=[
            FakeResponse(
                200,
                {
                "access_token": "access",
                "refresh_token": "refresh",
                },
            )
        ],
        requests=[
            FakeResponse(
                200,
                [{"guid": "home-id", "name": "Home", "zones": []}],
            )
        ],
    )
    api = MagicAirApi(session, "user@example.com", "password")  # type: ignore[arg-type]
    locations = await api.async_get_locations()

    assert locations[0]["guid"] == "home-id"
    assert session.calls[0][1] == f"{API_BASE_URL}{OAUTH_TOKEN_PATH}"
    assert session.calls[1][1] == f"{API_BASE_URL}/location"


@pytest.mark.asyncio
async def test_invalid_credentials() -> None:
    """Bad credentials raise an authentication-specific error."""
    session = FakeSession(auth=[FakeResponse(400)], requests=[])
    api = MagicAirApi(
        session,  # type: ignore[arg-type]
        "user@example.com",
        "bad-password",
    )
    with pytest.raises(MagicAirAuthenticationError):
        await api.async_get_locations()


@pytest.mark.asyncio
async def test_expired_token_is_refreshed() -> None:
    """A 401 causes one refresh-token exchange and a retry."""
    session = FakeSession(
        auth=[
            FakeResponse(
                200,
                {
                    "access_token": "first-access",
                    "refresh_token": "refresh",
                },
            ),
            FakeResponse(
                200,
                {
                    "access_token": "second-access",
                    "refresh_token": "second-refresh",
                },
            ),
        ],
        requests=[
            FakeResponse(401),
            FakeResponse(
                200,
                [{"guid": "home-id", "name": "Home", "zones": []}],
            ),
        ],
    )
    api = MagicAirApi(session, "user@example.com", "password")  # type: ignore[arg-type]
    locations = await api.async_get_locations()

    assert locations[0]["name"] == "Home"
    refresh_form = session.calls[2][2]["data"]
    assert refresh_form["grant_type"] == "refresh_token"


@pytest.mark.asyncio
async def test_command_waits_until_completed() -> None:
    """Queued device commands are polled to completion."""
    session = FakeSession(
        auth=[FakeResponse(200, {"access_token": "access"})],
        requests=[
            FakeResponse(
                200,
                {"task_id": "task-id", "status": "queued"},
            ),
            FakeResponse(
                200,
                {"task_id": "task-id", "status": "completed"},
            ),
        ],
    )
    api = MagicAirApi(session, "user@example.com", "password")  # type: ignore[arg-type]
    await api.async_execute_device_command(
        "device-id",
        "mode",
        {"is_on": True},
    )

    assert session.calls[1][1] == f"{API_BASE_URL}/device/device-id/mode"
    assert session.calls[2][1] == f"{API_BASE_URL}/task/task-id"
