"""Data coordinator: one poll of /api/ha/state, shared by every entity."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from homeassistant.util import dt as dt_util

from .const import API_DOSE, API_STATE, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


def _hhmm_to_min(ertek: str) -> int:
    """"07:30" -> 450. Anything else is -1, so it never counts as overdue."""
    try:
        ora, perc = ertek.split(":", 1)
        return int(ora) * 60 + int(perc)
    except (ValueError, AttributeError):
        return -1


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
        """Mark one dose as given (or undo it) and reflect it in the UI at once.

        The write itself is quick; what used to feel slow was the refresh. A
        coordinator debounces `async_request_refresh` by ten seconds, so the FIRST
        tap looked instant and every further tap inside that window appeared frozen
        until the debounce expired. On a wall tablet, where the doses are ticked off
        one after another, that reads as a broken screen (measured on video
        2026-09-09: five taps, all five ticks appeared together six seconds later).

        So the cached row is patched locally from the answer the server already
        sends back, and the scheduled poll reconciles it a minute later anyway.
        """
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
                try:
                    valasz = await resp.json()
                except Exception:  # noqa: BLE001 - a valasz nem kotelezo, csak segit
                    valasz = {}
                if not isinstance(valasz, dict):
                    valasz = {}
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"connection failed: {err}") from err
        self._patch_dose(medication, scheduled, given, valasz)
        await self.async_request_refresh()

    def _patch_dose(
        self, medication: str, scheduled: str, given: bool, valasz: dict[str, Any]
    ) -> None:
        """Flip one dose in the cached data, and keep the summary counts honest.

        `given_at` and `given_by` come from the server response: the name is decided
        there (the family can override what the switch sends), so guessing it here
        would show one thing now and another thing after the next poll. An older
        server that does not send them back leaves the labels empty until the poll,
        which is still better than a tick that does not move.
        """
        data = self.data
        if not isinstance(data, dict):
            return
        doses = data.get("doses")
        if not isinstance(doses, list):
            return
        talalt = False
        for row in doses:
            if (
                str(row.get("medication")) == medication
                and str(row.get("scheduled")) == scheduled
            ):
                row["given"] = bool(given)
                row["given_at"] = str(valasz.get("given_at") or "") if given else ""
                row["given_by"] = str(valasz.get("given_by") or "") if given else ""
                talalt = True
                break
        if not talalt:
            return

        # The head card reads these straight off the coordinator, so a stale count
        # would contradict the ticks right next to it.
        most = dt_util.now()
        now_min = most.hour * 60 + most.minute
        pending = overdue = 0
        kovetkezo = None
        for row in doses:
            if row.get("given"):
                continue
            pending += 1
            perc = _hhmm_to_min(str(row.get("scheduled") or ""))
            if 0 <= perc < now_min:
                overdue += 1
            elif kovetkezo is None:
                kovetkezo = {
                    "scheduled": row.get("scheduled"),
                    "pet": row.get("pet"),
                    "med": row.get("med"),
                }
        data["pending"] = pending
        data["given"] = len(doses) - pending
        data["overdue"] = overdue
        data["next"] = kovetkezo
        self.async_set_updated_data(data)
