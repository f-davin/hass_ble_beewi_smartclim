"""Test the BeeWi SmartClim config flow."""
from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.components.beewi_smartclim.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import NOT_SMART_CLIM_DEVICE, SMART_CLIM_VALID

from tests.common import MockConfigEntry


async def test_async_step_bluetooth_valid_device(hass: HomeAssistant) -> None:
    """Test discovery via bluetooth with a valid device."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=SMART_CLIM_VALID,
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"
    with patch(
        "homeassistant.components.beewi_smartclim.async_setup_entry", return_value=True
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == "089352809434933736"
    assert result2["data"] == {}
    assert result2["result"].unique_id == "aa:bb:cc:dd:ee:ff"


async def test_async_step_bluetooth_not_smartclim(hass: HomeAssistant) -> None:
    """Test that we reject discovery via Bluetooth for an unrelated device."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=NOT_SMART_CLIM_DEVICE,
    )
    assert result["type"] == FlowResultType.ABORT


async def test_async_step_bluetooth_devices_already_setup(hass: HomeAssistant) -> None:
    """Test we can't start a flow if there is already a config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=SMART_CLIM_VALID,
    )
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_async_step_bluetooth_already_in_progress(hass: HomeAssistant) -> None:
    """Test we can't start a flow for the same device twice."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=SMART_CLIM_VALID,
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=SMART_CLIM_VALID,
    )
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_in_progress"


async def test_async_step_user_takes_precedence_over_discovery(
    hass: HomeAssistant,
) -> None:
    """Test manual setup takes precedence over discovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=SMART_CLIM_VALID,
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"

    with patch(
        "homeassistant.components.beewi_smartclim.config_flow.async_discovered_service_info",
        return_value=[SMART_CLIM_VALID],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
        assert result["type"] == FlowResultType.FORM

    with patch(
        "homeassistant.components.beewi_smartclim.async_setup_entry", return_value=True
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"address": "aa:bb:cc:dd:ee:ff"},
        )
    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == "N"
    assert result2["data"] == {}
    assert result2["result"].unique_id == "aa:bb:cc:dd:ee:ff"

    # Verify the original one was aborted
    assert not hass.config_entries.flow.async_progress(DOMAIN)


async def test_async_step_user_no_devices_found(hass: HomeAssistant) -> None:
    """Test setup from service info cache with no devices found."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "no_devices_found"


async def test_async_step_user_only_other_devices_found(hass: HomeAssistant) -> None:
    """Test setup from service info cache with only other devices found."""
    with patch(
        "homeassistant.components.beewi_smartclim.config_flow.async_discovered_service_info",
        return_value=[NOT_SMART_CLIM_DEVICE],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "no_devices_found"


async def test_async_step_user_with_found_devices(hass: HomeAssistant) -> None:
    """Test setup from service info cache with devices found."""
    with patch(
        "homeassistant.components.beewi_smartclim.config_flow.async_discovered_service_info",
        return_value=[SMART_CLIM_VALID],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    with patch(
        "homeassistant.components.beewi_smartclim.async_setup_entry", return_value=True
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"address": "aa:bb:cc:dd:ee:ff"},
        )
    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == "N"
    assert result2["data"] == {}
    assert result2["result"].unique_id == "aa:bb:cc:dd:ee:ff"


async def test_async_step_user_device_added_between_steps(hass: HomeAssistant) -> None:
    """Test the device gets added via another flow between steps."""
    with patch(
        "homeassistant.components.beewi_smartclim.config_flow.async_discovered_service_info",
        return_value=[SMART_CLIM_VALID],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"

    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.beewi_smartclim.async_setup_entry", return_value=True
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"address": "aa:bb:cc:dd:ee:ff"},
        )
    assert result2["type"] == FlowResultType.ABORT
    assert result2["reason"] == "already_configured"


async def test_async_step_user_with_found_devices_already_setup(
    hass: HomeAssistant,
) -> None:
    """Test setup from service info cache with devices found."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.beewi_smartclim.config_flow.async_discovered_service_info",
        return_value=[SMART_CLIM_VALID],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "no_devices_found"