"""Data coordinator: one poll of /api/ha/state, shared by every entity."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_DOSE, API_STATE, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class BogancsAuthError(Exception):
    """The key was rejected. Re-authentication is needed, not a retry."""


class BogancsCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetches today's doses and the daily routine for one family."""

    def __init__(self, hass: HomeAssistant, url: str, key: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Bogáncs",
            update_interval=UPDATE_INTERVAL,
        )
        self._url = url.rstrip("/")
        self._key = key
        self._session = async_get_clientsession(hass)

    @property
    def base_url(self) -> str:
        return self._url

    async def _async_update_data(self) -> dict[str, Any]:
        return await self.fetch_state()

    async def fetch_state(self) -> dict[str, Any]:
        """One GET. Raises BogancsAuthError on a bad key so the flow can ask again."""
        try:
            async with self._session.get(
                f"{self._url}{API_STATE}",
                headers={"X-Api-Key": self._key},
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                if resp.status in (401, 403):
                    raise BogancsAuthError
                if resp.status != 200:
                    raise UpdateFailed(f"HTTP {resp.status}")
                data = await resp.json()
        except BogancsAuthError:
            raise
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"connection failed: {err}") from err
        if not isinstance(data, dict):
            raise UpdateFailed("unexpected response")
        return data

    async def async_set_dose(
        self, medication: str, scheduled: str, given: bool, by: str
    ) -> None:
        """Mark one dose as given (or undo it), then refresh so the UI follows."""
        body = {
            "medication": medication,
            "scheduled": scheduled,
            "given": given,
            "by": by,
        }
        try:
            async with self._session.post(
                f"{self._url}{API_DOSE}",
                headers={"X-Api-Key": self._key},
                json=body,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                if resp.status in (401, 403):
                    raise BogancsAuthError
                if resp.status != 200:
                    text = await resp.text()
                    raise UpdateFailed(f"HTTP {resp.status}: {text[:120]}")
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"connection failed: {err}") from err
        await self.async_request_refresh()
