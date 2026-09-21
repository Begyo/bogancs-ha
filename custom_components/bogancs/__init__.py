"""Bogáncs kisállatkönyv integration for Home Assistant."""

from __future__ import annotations

from pathlib import Path

import voluptuous as vol
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.frontend import add_extra_js_url
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.loader import async_get_integration
import homeassistant.helpers.config_validation as cv

from .const import (
    ATTR_ALKALOM,
    ATTR_BY,
    ATTR_FED,
    ATTR_FEEDING,
    ATTR_FEED_MISSED,
    ATTR_GIVEN,
    ATTR_MEDICATION,
    ATTR_SCHEDULED,
    CONF_KEY,
    CONF_URL,
    DEFAULT_URL,
    DOMAIN,
    ATTR_MISSED,
    ATTR_REASON,
    SERVICE_DOSE,
    SERVICE_FEED,
)
from .coordinator import BogancsAuthError, BogancsCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SWITCH]

CARD_URL = "/bogancs_static/bogancs-card.js"
CARD_FILE = "bogancs-card.js"
# SAJAT KULCS, NEM a hass.data[DOMAIN]-ban: oda kizarolag koordinatorok valok, mert a
# `bogancs.dose` szolgaltatas vegigmegy az ertekein. 2026-09-16-an egy ide tett boolean
# miatt a szolgaltatas `'bool' object has no attribute 'async_set_dose'` hibaval elszallt,
# es a kioszkrol nem lehetett adagot jelolni.
CARD_FLAG = f"{DOMAIN}_card_registered"

DOSE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_MEDICATION): cv.string,
        vol.Optional(ATTR_SCHEDULED, default=""): cv.string,
        vol.Optional(ATTR_GIVEN, default=True): cv.boolean,
        vol.Optional(ATTR_BY, default="Home Assistant"): cv.string,
        # Kimaradt adag (2026-09-17). Kulon mezo es nem masik szolgaltatas: ugyanarrol az
        # adagrol van szo, csak a harmadik allapotaban.
        vol.Optional(ATTR_MISSED, default=False): cv.boolean,
        vol.Optional(ATTR_REASON, default=""): cv.string,
    }
)

# ETETES (Begyo kerese 2026-09-21, jegy #40). Kulon szolgaltatas es nem a `dose` bovitese:
# mas az azonositoja (tap + napi alkalom, nem gyogyszer + idopont), es nincs harmadik allapota.
FEED_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_FEEDING): cv.string,
        vol.Optional(ATTR_ALKALOM, default=1): vol.All(vol.Coerce(int), vol.Range(min=1)),
        vol.Optional(ATTR_FED, default=True): cv.boolean,
        vol.Optional(ATTR_FEED_MISSED, default=False): cv.boolean,
        vol.Optional(ATTR_BY, default="Home Assistant"): cv.string,
    }
)


async def _async_register_card(hass: HomeAssistant) -> None:
    """Serve our own Lovelace card, so the integration is complete on its own.

    Begyo, 2026-09-16: "Az integracio telepitesevel mindenkinek komplett, jol mukodo megoldast
    kell nyujtani. Nem irhatjuk oda, hogy ahhoz hogy mukodjon, telepitsd meg ezt meg azt."
    Until now the dose list on a dashboard needed three separate HACS front-end add-ons
    (mushroom, card-mod, config-template-card), and the template card rebuilt the whole list on
    every state change -- the screen flashed and the scroll position jumped back to the top.
    The card shipped here has no external dependency and updates one row at a time.
    """
    if hass.data.get(CARD_FLAG):
        return
    path = Path(__file__).parent / "www" / CARD_FILE
    if not path.is_file():
        return
    # A jelzot az ELSO `await` ELOTT kell beallitani. Ket felvett csalad eseten a ket bejegyzes
    # egyszerre indul, mindketto atjutna a fenti ellenorzesen, es a masodik regisztracio
    # "Added route will never be executed, method GET is already registered" hibaval megolne a
    # MASODIK csalad egesz bejegyzeset (2026-09-21-en merve, ket bejegyzessel).
    hass.data[CARD_FLAG] = True
    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig(CARD_URL, str(path), True)]
        )
    except (RuntimeError, ValueError):
        # Mar regisztralva van (pl. a HA belso ujratoltese utan): a kartya kiszolgalasa el,
        # nincs teendo. A bejegyzes emiatt SOHA ne dolje el.
        return
    # A cache-buster the browser can see: without it a returning user keeps the old card
    # after an update, and the fix looks like it never shipped. The version comes from the
    # manifest, so it can never drift from what HACS reports.
    integration = await async_get_integration(hass, DOMAIN)
    add_extra_js_url(hass, f"{CARD_URL}?v={integration.version}")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up one family from a config entry."""
    await _async_register_card(hass)
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
                missed=call.data.get(ATTR_MISSED, False),
            )

    async def _feed(call: ServiceCall) -> None:
        """Etetes megjelolese automatizalasbol vagy a sajat kartyarol.

        A `dose`-zal ellentetben ez CSAK ahhoz a csaladhoz megy, amelyiknel a sor tenylegesen
        letezik. Ket felvett csalad eseten a masiknak kuldott keres 404-gyel szallna el, es a
        hibat a hivo latna -- pedig az etetes rogzult.
        """
        feeding = call.data[ATTR_FEEDING]
        alkalom = call.data.get(ATTR_ALKALOM, 1)
        for coord in hass.data.get(DOMAIN, {}).values():
            blokk = (coord.data or {}).get("feeding") or {}
            for row in blokk.get("rows", []):
                if str(row.get("feeding")) == feeding and int(row.get("alkalom") or 0) == alkalom:
                    await coord.async_set_feed(
                        feeding,
                        alkalom,
                        call.data.get(ATTR_FED, True),
                        call.data.get(ATTR_BY, "Home Assistant"),
                        missed=call.data.get(ATTR_FEED_MISSED, False),
                    )
                    return

    if not hass.services.has_service(DOMAIN, SERVICE_DOSE):
        hass.services.async_register(DOMAIN, SERVICE_DOSE, _dose, schema=DOSE_SCHEMA)
    if not hass.services.has_service(DOMAIN, SERVICE_FEED):
        hass.services.async_register(DOMAIN, SERVICE_FEED, _feed, schema=FEED_SCHEMA)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_DOSE)
            hass.services.async_remove(DOMAIN, SERVICE_FEED)
    return unloaded
