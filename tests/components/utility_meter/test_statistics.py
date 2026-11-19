"""The tests for the statistics of utility_meter sensors."""

from functools import partial

from freezegun.api import FrozenDateTimeFactory
from pytest_homeassistant.components.recorder.common import (
    async_wait_recording_done,
    do_adhoc_statistics,
)

from homeassistant.components.recorder import Recorder
from homeassistant.components.recorder.statistics import get_metadata
from homeassistant.components.recorder.util import get_instance
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.utility_meter.const import DOMAIN
from homeassistant.components.utility_meter.services import UtilityMeterService
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_UNIT_OF_MEASUREMENT,
    TargetKey,
    UnitOfEnergy,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

SOURCE_ENTITY_ID = "sensor.energy"
METER_ENTITY_ID = "sensor.energy_bill"


async def test_reset_before_first_source_change_statistics_unit(
    recorder_mock: Recorder, hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Test a meter reset before the source changes compiles statistics in kWh."""
    freezer.move_to("2026-01-01 10:01:00+00:00")
    hass.states.async_set(
        SOURCE_ENTITY_ID,
        "10",
        {
            ATTR_UNIT_OF_MEASUREMENT: UnitOfEnergy.KILO_WATT_HOUR,
            ATTR_DEVICE_CLASS: SensorDeviceClass.ENERGY,
        },
    )
    assert await async_setup_component(
        hass, DOMAIN, {DOMAIN: {"energy_bill": {"source": SOURCE_ENTITY_ID}}}
    )
    await hass.async_block_till_done()

    await hass.services.async_call(
        DOMAIN,
        UtilityMeterService.RESET,
        target={TargetKey.ENTITY_ID: METER_ENTITY_ID},
        blocking=True,
    )
    await async_wait_recording_done(hass)

    do_adhoc_statistics(hass, start=dt_util.parse_datetime("2026-01-01T10:00:00Z"))
    await async_wait_recording_done(hass)

    metadata = await get_instance(hass).async_add_executor_job(
        partial(get_metadata, hass, statistic_ids={METER_ENTITY_ID})
    )
    assert metadata[METER_ENTITY_ID][1]["unit_of_measurement"] == (
        UnitOfEnergy.KILO_WATT_HOUR
    )
