"""Sensors: what is still due today, what is late, what comes next -- and what needs
attention beyond the medicine cabinet.

2026-09-04 (Begyo): the daily routine sensor is gone. A routine is a list a person reads in
the app; it never changed on its own, so a dashboard tile for it only repeated what was
already written down. What belongs on a wall panel is the time-bound and the alarming:
appointments, a hazard reported nearby, someone's lost pet in the neighbourhood, and a
supply about to run out. Those change without anyone opening the app.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BogancsCoordinator


@dataclass(frozen=True, kw_only=True)
class BogancsSensorDescription(SensorEntityDescription):
    """A sensor plus how to read it out of the state payload."""

    value: Callable[[dict[str, Any]], Any]
    extra: Callable[[dict[str, Any]], dict[str, Any]] | None = None


def _next_value(data: dict[str, Any]) -> Any:
    nxt = data.get("next")
    return nxt.get("scheduled") if isinstance(nxt, dict) else None


def _next_extra(data: dict[str, Any]) -> dict[str, Any]:
    nxt = data.get("next")
    if not isinstance(nxt, dict):
        return {}
    return {"pet": nxt.get("pet", ""), "medication": nxt.get("med", "")}


def _lista(data: dict[str, Any], kulcs: str) -> list[Any]:
    """One list out of the payload, defensively.

    An older server does not send the new keys at all, and a missing key must read as
    "nothing to show", not as a crash in the coordinator.
    """
    ertek = data.get(kulcs)
    return ertek if isinstance(ertek, list) else []


SENSORS: tuple[BogancsSensorDescription, ...] = (
    BogancsSensorDescription(
        key="pending",
        translation_key="pending",
        icon="mdi:pill",
        native_unit_of_measurement="adag",
        value=lambda d: d.get("pending", 0),
        # The whole day's list travels as an attribute so a dashboard card can
        # render it without a second request.
        extra=lambda d: {
            "date": d.get("date", ""),
            "total": d.get("total", 0),
            "given": d.get("given", 0),
            "overdue": d.get("overdue", 0),
            "doses": d.get("doses", []),
            "interval": d.get("interval", []),
            "missed": d.get("missed", 0),
        },
    ),
    # KIMARADT (Begyo kerese 2026-09-17): sajat szenzor, mert ez az egyetlen allapot, amirol
    # egy vezerlopult magatol sosem szolna. A hatralevo adag magatol elfogy (beadjak), a
    # kimaradas viszont ott marad a napon, es pont ezt kell eszrevenni.
    BogancsSensorDescription(
        key="missed",
        translation_key="missed",
        icon="mdi:pill-off",
        native_unit_of_measurement="adag",
        value=lambda d: d.get("missed", 0),
        extra=lambda d: {
            "doses": [r for r in _lista(d, "doses") if r.get("missed")],
        },
    ),
    BogancsSensorDescription(
        key="overdue",
        translation_key="overdue",
        icon="mdi:clock-alert-outline",
        native_unit_of_measurement="adag",
        value=lambda d: d.get("overdue", 0),
    ),
    BogancsSensorDescription(
        key="next",
        translation_key="next",
        icon="mdi:clock-outline",
        value=_next_value,
        extra=_next_extra,
    ),
    # A time-bound list: vet and grooming appointments in the next seven days. The state is
    # the count so an automation can gate on it; the whole list travels as an attribute so a
    # card renders without a second request. `next` is broken out because that is what a
    # single-line tile wants to show.
    BogancsSensorDescription(
        key="appointments",
        translation_key="appointments",
        icon="mdi:calendar-clock",
        native_unit_of_measurement="időpont",
        value=lambda d: len(_lista(d, "appointments")),
        extra=lambda d: {
            "items": _lista(d, "appointments"),
            "next": d.get("appointment_next"),
        },
    ),
    # Hazards reported nearby. The server already applied the family's radius and dropped
    # anything expired or held back by moderation; the distance is rounded, and no address
    # or coordinate ever reaches the integration.
    BogancsSensorDescription(
        key="hazards",
        translation_key="hazards",
        icon="mdi:alert-outline",
        native_unit_of_measurement="jelzés",
        value=lambda d: len(_lista(d, "hazards")),
        extra=lambda d: {"items": _lista(d, "hazards")},
    ),
    # Somebody else's lost pet in the neighbourhood. Never your own: the server filters the
    # family out, otherwise the panel would report your own animal back to you.
    BogancsSensorDescription(
        key="lost_nearby",
        translation_key="lost_nearby",
        icon="mdi:map-marker-alert-outline",
        native_unit_of_measurement="állat",
        value=lambda d: len(_lista(d, "lost_nearby")),
        extra=lambda d: {"items": _lista(d, "lost_nearby")},
    ),
    # Food and medicine running low, with the same arithmetic the app and the morning
    # summary use -- a panel that disagreed with the phone would be worse than no panel.
    BogancsSensorDescription(
        key="stock",
        translation_key="stock",
        icon="mdi:package-variant",
        native_unit_of_measurement="tétel",
        value=lambda d: len(_lista(d, "stock")),
        extra=lambda d: {"items": _lista(d, "stock")},
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: BogancsCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(BogancsSensor(coordinator, entry, d) for d in SENSORS)


class BogancsSensor(CoordinatorEntity[BogancsCoordinator], SensorEntity):
    """One number out of the daily state."""

    _attr_has_entity_name = True
    entity_description: BogancsSensorDescription

    def __init__(
        self,
        coordinator: BogancsCoordinator,
        entry: ConfigEntry,
        description: BogancsSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Bogáncs kisállatkönyv",
            configuration_url=coordinator.base_url,
        )

    @property
    def native_value(self) -> Any:
        return self.entity_description.value(self.coordinator.data or {})

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.extra is None:
            return None
        return self.entity_description.extra(self.coordinator.data or {})
