"""Config flow for BeeWi SmartClim integration."""


import logging
from typing import Any

from homeassistant import config_entries, data_entry_flow
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.const import CONF_MAC, CONF_NAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv
from smartclim_ble import BeeWiSmartClimAdvertisement, SmartClimSensorData
import voluptuous as vol

from .const import DEFAULT_DEVICE_MAC, DEFAULT_DEVICE_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)

DEVICE_SCHEMA = vol.Schema ({
    vol.Optional(CONF_MAC, default=DEFAULT_DEVICE_MAC): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_DEVICE_NAME): cv.string,
})

class SmartClimConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BeeWi SmartClim."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    def __init__(self) -> None:
        """Set up a new config flow for BeeWi SmartClim."""
        self._discovery_info: BluetoothServiceInfoBleak | None = None
        self._discovered_device: BeeWiSmartClimAdvertisement | None = None
        self._discovered_devices: dict[str, str] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the user step to pick discovered device."""
        _LOGGER.debug("async_step_user: %s", user_input)

        if self._async_current_entries():
            return self.async_abort(reason="Single instance allowed.")
        if self.hass.data.get(DOMAIN):
            return self.async_abort(reason="Single instance allowed.")
        if user_input is not None:
            address = user_input[CONF_MAC]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=self._discovered_devices[address][0], data={}
            )

        current_addresses = self._async_current_ids()
        for discovery_info in async_discovered_service_info(self.hass, False):
            address = discovery_info.address
            if address in current_addresses or address in self._discovered_devices:
                continue

            device = SmartClimSensorData()
            if device.supported_data(discovery_info.advertisement):
                self._discovered_devices[
                    address
                ] = f"Name: {discovery_info.name}  Mac: {discovery_info.address}"

        if not self._discovered_devices:
            return self.async_abort(reason="no_devices_found")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_MAC): vol.In(self._discovered_devices)}
            ),
        )

    async def async_step_import(self, import_info=None):
        """Handle import from config file."""
        return await self.async_step_user(import_info)
