"""Sensors: what is still due today, what is late, and what comes next."""

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
    BogancsSensorDescription(
        key="routine",
        translation_key="routine",
        icon="mdi:white-balance-sunny",
        native_unit_of_measurement="teendő",
        value=lambda d: len(d.get("routine") or []),
        extra=lambda d: {"items": d.get("routine", [])},
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
