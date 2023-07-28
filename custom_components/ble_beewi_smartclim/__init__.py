"""The BeeWi SmartClim custom component."""

from __future__ import annotations

import logging

from homeassistant import config_entries
from homeassistant.components.bluetooth import BluetoothScanningMode
from homeassistant.components.bluetooth.models import BluetoothServiceInfoBleak
from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothProcessorCoordinator,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceRegistry, async_get
from smartclim_ble import BeeWiSmartClimBluetoothDeviceData, SensorUpdate

from .const import DOMAIN

PLATFORMS: list[Platform] = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


def process_service_info(
    hass: HomeAssistant,
    entry: config_entries.ConfigEntry,
    data: BeeWiSmartClimBluetoothDeviceData,
    service_info: BluetoothServiceInfoBleak,
    device_registry: DeviceRegistry,
) -> SensorUpdate:
    """Process a BluetoothServiceInfoBleak, running side effects and returning
    sensor data."""
    update = data.update(service_info)
    coordinator: PassiveBluetoothProcessorCoordinator = hass.data[DOMAIN][
        entry.entry_id
    ]
    #discovered_device_classes = coordinator.discovered_device_classes
    if update.events:
        address = service_info.device.address
        for device_key, event in update.events.items():
            sensor_device_info = update.devices[device_key.device_id]
            device = device_registry.async_get_or_create(
                config_entry_id=entry.entry_id,
                identifiers={(DOMAIN, address)},
                manufacturer=sensor_device_info.manufacturer,
                model=sensor_device_info.model,
                name=sensor_device_info.name,
                sw_version=sensor_device_info.sw_version,
                hw_version=sensor_device_info.hw_version,
            )
            event_class = event.device_key.key
            event_type = event.event_type

            # if event_class not in discovered_device_classes:
            #     discovered_device_classes.add(event_class)
            #     hass.config_entries.async_update_entry(
            #         entry,
            #         data=entry.data
            #         | {"known_events": list(discovered_device_classes)},
            #     )
    return update


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Xiaomi BLE device from a config entry."""
    address = entry.unique_id
    assert address is not None

    kwargs = {}
    if bindkey := entry.data.get("bindkey"):
        kwargs["bindkey"] = bytes.fromhex(bindkey)
    data = BeeWiSmartClimBluetoothDeviceData(**kwargs)

    device_registry = async_get(hass)
    coordinator = hass.data.setdefault(DOMAIN, {})[
        entry.entry_id
    ] = PassiveBluetoothProcessorCoordinator(
        hass,
        _LOGGER,
        address=address,
        mode=BluetoothScanningMode.PASSIVE,
        update_method=lambda service_info: process_service_info(
            hass, entry, data, service_info, device_registry
        ),
        # We will take advertisements from non-connectable devices
        # since we will trade the BLEDevice for a connectable one
        # if we need to poll it
        connectable=False,
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(
        coordinator.async_start()
    )  # only start after all platforms have had a chance to subscribe
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
