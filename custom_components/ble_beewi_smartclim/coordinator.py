"""The Xiaomi BLE integration."""
from collections.abc import Callable, Coroutine
from logging import Logger
from typing import Any

from homeassistant.components.bluetooth import (
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
)
from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothDataProcessor,
    PassiveBluetoothProcessorCoordinator,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.debounce import Debouncer
from smartclim_ble import XiaomiBluetoothDeviceData


class BeeWiSmartClimPassiveBluetoothProcessorCoordinator(PassiveBluetoothProcessorCoordinator):
    """Define a BeeWiSmartClim Bluetooth Passive Update Processor Coordinator."""

    def __init__(
        self,
        hass: HomeAssistant,
        logger: Logger,
        *,
        address: str,
        mode: BluetoothScanningMode,
        update_method: Callable[[BluetoothServiceInfoBleak], Any],
        device_data: XiaomiBluetoothDeviceData,
        discovered_device_classes: set[str],
        connectable: bool = False,
    ) -> None:
        """Initialize the Xiaomi Bluetooth Active Update Processor Coordinator."""
        super().__init__(
            hass=hass,
            logger=logger,
            address=address,
            mode=mode,
            update_method=update_method,
            connectable=connectable,
        )
        self.discovered_device_classes = discovered_device_classes
        self.device_data = device_data


class BeeWiSmartClimPassiveBluetoothDataProcessor(PassiveBluetoothDataProcessor):
    """Define a BeeWiSmartClim Bluetooth Passive Update Data Processor."""

    coordinator: BeeWiSmartClimPassiveBluetoothProcessorCoordinator
