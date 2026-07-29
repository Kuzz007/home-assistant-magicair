"""Asynchronous client for the unofficial MagicAir cloud API."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Any

from aiohttp import ClientError, ClientResponse, ClientSession, ClientTimeout

from .const import (
    API_BASE_URL,
    DEFAULT_REQUEST_TIMEOUT,
    OAUTH_CLIENT_ID,
    OAUTH_CLIENT_SECRET,
    OAUTH_TOKEN_PATH,
)


class MagicAirError(Exception):
    """Base class for MagicAir errors."""


class MagicAirAuthenticationError(MagicAirError):
    """Raised when MagicAir rejects the account credentials."""


class MagicAirConnectionError(MagicAirError):
    """Raised when the MagicAir cloud cannot be reached."""


class MagicAirLocationNotFoundError(MagicAirError):
    """Raised when the configured MagicAir home no longer exists."""


class MagicAirCommandError(MagicAirError):
    """Raised when a device command fails or times out."""


class MagicAirApi:
    """Client for the MagicAir cloud used by the official applications."""

    def __init__(
        self,
        session: ClientSession,
        username: str,
        password: str,
        *,
        request_timeout: int = DEFAULT_REQUEST_TIMEOUT,
    ) -> None:
        """Initialize the client."""
        self._session = session
        self._username = username
        self._password = password
        self._timeout = ClientTimeout(total=request_timeout)
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._auth_lock = asyncio.Lock()

    async def async_get_locations(self) -> list[dict[str, Any]]:
        """Return every home available to the account."""
        result = await self._async_request("GET", "/location")
        if not isinstance(result, list):
            raise MagicAirError("MagicAir returned an invalid locations response")
        return [location for location in result if isinstance(location, dict)]

    async def async_get_location(self, location_id: str) -> dict[str, Any]:
        """Return one home by its stable GUID."""
        locations = await self.async_get_locations()
        for location in locations:
            if location.get("guid") == location_id:
                return location
        raise MagicAirLocationNotFoundError(
            "The configured MagicAir home is no longer available"
        )

    async def async_execute_device_command(
        self,
        device_id: str,
        command_type: str,
        payload: Mapping[str, Any],
    ) -> None:
        """Execute a command against a MagicAir device."""
        await self._async_execute_command(
            f"/device/{device_id}/{command_type}",
            payload,
        )

    async def async_execute_zone_command(
        self,
        zone_id: str,
        payload: Mapping[str, Any],
    ) -> None:
        """Change a MagicAir zone mode."""
        await self._async_execute_command(f"/zone/{zone_id}/mode", payload)

    async def _async_execute_command(
        self,
        endpoint: str,
        payload: Mapping[str, Any],
    ) -> None:
        result = await self._async_request("POST", endpoint, json=dict(payload))
        if not isinstance(result, dict):
            raise MagicAirCommandError("MagicAir returned an invalid command response")

        task_id = result.get("task_id")
        if not task_id or result.get("status") == "completed":
            return

        for attempt in range(1, 6):
            status = result.get("status")
            if status not in {"queued", "delivered"}:
                raise MagicAirCommandError(
                    f"MagicAir command ended with unexpected status: {status}"
                )
            await asyncio.sleep(attempt * 0.1)
            result = await self._async_request("GET", f"/task/{task_id}")
            if not isinstance(result, dict):
                raise MagicAirCommandError(
                    "MagicAir returned an invalid task response"
                )
            if result.get("status") == "completed":
                return

        raise MagicAirCommandError("MagicAir command did not complete in time")

    async def _async_request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> Any:
        for attempt in range(2):
            await self._async_ensure_token()
            headers = dict(kwargs.pop("headers", {}))
            headers["Authorization"] = f"Bearer {self._access_token}"

            try:
                response = await self._session.request(
                    method,
                    f"{API_BASE_URL}{endpoint}",
                    headers=headers,
                    timeout=self._timeout,
                    **kwargs,
                )
            except (ClientError, TimeoutError) as err:
                raise MagicAirConnectionError(
                    "Unable to connect to the MagicAir cloud"
                ) from err

            if response.status == 401 and attempt == 0:
                response.release()
                self._access_token = None
                continue
            if response.status == 401:
                response.release()
                raise MagicAirAuthenticationError("MagicAir authentication expired")

            return await self._async_decode_response(response)

        raise MagicAirAuthenticationError("MagicAir authentication expired")

    async def _async_ensure_token(self) -> None:
        if self._access_token:
            return

        async with self._auth_lock:
            if self._access_token:
                return

            if self._refresh_token:
                try:
                    await self._async_authenticate(
                        {
                            "grant_type": "refresh_token",
                            "refresh_token": self._refresh_token,
                            "client_id": OAUTH_CLIENT_ID,
                            "client_secret": OAUTH_CLIENT_SECRET,
                        }
                    )
                    return
                except MagicAirAuthenticationError:
                    self._refresh_token = None

            await self._async_authenticate(
                {
                    "grant_type": "password",
                    "username": self._username,
                    "password": self._password,
                    "client_id": OAUTH_CLIENT_ID,
                    "client_secret": OAUTH_CLIENT_SECRET,
                }
            )

    async def _async_authenticate(self, form: Mapping[str, str]) -> None:
        try:
            response = await self._session.post(
                f"{API_BASE_URL}{OAUTH_TOKEN_PATH}",
                data=form,
                timeout=self._timeout,
            )
        except (ClientError, TimeoutError) as err:
            raise MagicAirConnectionError(
                "Unable to connect to the MagicAir authentication service"
            ) from err

        if response.status in {400, 401, 403}:
            response.release()
            raise MagicAirAuthenticationError(
                "The MagicAir username or password is invalid"
            )

        payload = await self._async_decode_response(response)
        if not isinstance(payload, dict) or not payload.get("access_token"):
            raise MagicAirAuthenticationError(
                "MagicAir returned an invalid authentication response"
            )

        self._access_token = str(payload["access_token"])
        refresh_token = payload.get("refresh_token")
        if refresh_token:
            self._refresh_token = str(refresh_token)

    @staticmethod
    async def _async_decode_response(response: ClientResponse) -> Any:
        if response.status >= 500:
            response.release()
            raise MagicAirConnectionError(
                f"MagicAir cloud returned HTTP {response.status}"
            )
        if response.status >= 400:
            response.release()
            raise MagicAirError(f"MagicAir cloud returned HTTP {response.status}")
        if response.status == 204:
            return None

        try:
            return await response.json(content_type=None)
        except (ValueError, ClientError) as err:
            raise MagicAirError("MagicAir returned invalid JSON") from err
