"""One switch per scheduled dose: on = given, off = not given.

A switch and not a button, because the app itself works this way: tapping a dose
marks it given, tapping again takes it back. A button could only ever say "done"
and never show whether it already happened.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BogancsCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: BogancsCoordinator = hass.data[DOMAIN][entry.entry_id]
    known: set[str] = set()

    @callback
    def _sync() -> None:
        """Add switches for doses we have not seen yet.

        The schedule can change any day (a new medication, a new time), and the
        integration must not need a restart for that. Entities are never removed
        automatically: a medication that ends should not silently drop the history
        of the switch from the recorder.
        """
        new = []
        for row in (coordinator.data or {}).get("doses", []):
            key = f"{row.get('medication')}_{row.get('scheduled')}"
            if key in known:
                continue
            known.add(key)
            new.append(BogancsDoseSwitch(coordinator, entry, row))
        if new:
            async_add_entities(new)

    _sync()
    entry.async_on_unload(coordinator.async_add_listener(_sync))


class BogancsDoseSwitch(CoordinatorEntity[BogancsCoordinator], SwitchEntity):
    """A single dose of one medication at one time of day."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: BogancsCoordinator, entry: ConfigEntry, row: dict[str, Any]
    ) -> None:
        super().__init__(coordinator)
        self._medication = str(row.get("medication") or "")
        self._scheduled = str(row.get("scheduled") or "")
        self._attr_unique_id = f"{entry.entry_id}_{self._medication}_{self._scheduled}"
        self._attr_name = (
            f"{row.get('pet', '')} – {row.get('med', '')} {self._scheduled}".strip()
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Bogáncs kisállatkönyv",
            configuration_url=coordinator.base_url,
        )

    @property
    def _row(self) -> dict[str, Any]:
        for row in (self.coordinator.data or {}).get("doses", []):
            if (
                str(row.get("medication")) == self._medication
                and str(row.get("scheduled")) == self._scheduled
            ):
                return row
        return {}

    @property
    def available(self) -> bool:
        # A medication that ran out of its active window disappears from the day's
        # list. Showing "off" then would look like a missed dose, so: unavailable.
        return super().available and bool(self._row)

    @property
    def is_on(self) -> bool:
        return bool(self._row.get("given"))

    @property
    def icon(self) -> str:
        # A kimaradt adag ranezesre is masik allapot, ne csak az attributumban legyen ott.
        return "mdi:pill-off" if self._row.get("missed") else "mdi:pill"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        row = self._row
        return {
            "pet": row.get("pet", ""),
            "medication": row.get("med", ""),
            "dose": row.get("dose", ""),
            "scheduled": self._scheduled,
            "given_by": row.get("given_by", ""),
            "given_at": row.get("given_at", ""),
            # Harmadik allapot: se beadva, se hatravan. Enelkul egy automatizalas nem tudna
            # kulonbseget tenni "meg nem adtuk be" es "nem kapta meg" kozott.
            "missed": bool(row.get("missed")),
        }

    async def async_mark_missed(self, reason: str = "") -> None:
        """Kimaradtnak jelolni ezt az adagot (a szolgaltatason at hivhato)."""
        await self.coordinator.async_set_dose(
            self._medication, self._scheduled, False, "Home Assistant", missed=True
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_dose(
            self._medication, self._scheduled, True, "Home Assistant"
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_dose(
            self._medication, self._scheduled, False, "Home Assistant"
        )
