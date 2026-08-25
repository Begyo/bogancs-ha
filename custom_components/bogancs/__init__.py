"""Bogáncs kisállatkönyv integration for Home Assistant."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryAuthFailed
import homeassistant.helpers.config_validation as cv

from .const import (
    ATTR_BY,
    ATTR_GIVEN,
    ATTR_MEDICATION,
    ATTR_SCHEDULED,
    CONF_KEY,
    CONF_URL,
    DEFAULT_URL,
    DOMAIN,
    SERVICE_DOSE,
)
from .coordinator import BogancsAuthError, BogancsCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SWITCH]

DOSE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_MEDICATION): cv.string,
        vol.Optional(ATTR_SCHEDULED, default=""): cv.string,
        vol.Optional(ATTR_GIVEN, default=True): cv.boolean,
        vol.Optional(ATTR_BY, default="Home Assistant"): cv.string,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up one family from a config entry."""
    coordinator = BogancsCoordinator(
        hass, entry.data.get(CONF_URL, DEFAULT_URL), entry.data[CONF_KEY]
    )
    try:
        await coordinator.async_config_entry_first_refresh()
    except BogancsAuthError as err:
        # The key was revoked or regenerated in the app -> ask for a new one
        # instead of retrying forever with a key that will never work again.
        raise ConfigEntryAuthFailed from err

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def _dose(call: ServiceCall) -> None:
        """Mark a dose from an automation. Applies to every configured family."""
        for coord in hass.data.get(DOMAIN, {}).values():
            await coord.async_set_dose(
                call.data[ATTR_MEDICATION],
                call.data.get(ATTR_SCHEDULED, ""),
                call.data.get(ATTR_GIVEN, True),
                call.data.get(ATTR_BY, "Home Assistant"),
            )

    if not hass.services.has_service(DOMAIN, SERVICE_DOSE):
        hass.services.async_register(DOMAIN, SERVICE_DOSE, _dose, schema=DOSE_SCHEMA)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_DOSE)
    return unloaded
