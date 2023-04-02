"""Select platform for BMW."""
from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any

from bimmer_connected.vehicle import MyBMWVehicle
from bimmer_connected.vehicle.charging_profile import ChargingMode

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfElectricCurrent
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import BMWBaseEntity
from .const import DOMAIN
from .coordinator import BMWDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass
class BMWRequiredKeysMixin:
    """Mixin for required keys."""

    current_option: Callable[[MyBMWVehicle], Any]
    remote_service: Callable[[MyBMWVehicle, Any], Any]


@dataclass
class BMWSelectEntityDescription(SelectEntityDescription, BMWRequiredKeysMixin):
    """Describes BMW sensor entity."""

    is_available: Callable = lambda x: False
    dynamic_options: Callable | None = None


NUMBER_TYPES: dict[str, BMWSelectEntityDescription] = {
    # --- Generic ---
    "target_soc": BMWSelectEntityDescription(
        key="target_soc",
        name="Target SoC",
        is_available=lambda x: x.is_remote_set_target_soc_enabled,
        options=[str(i * 5 + 20) for i in range(17)],
        current_option=lambda x: str(x.fuel_and_battery.charging_target),
        remote_service=lambda v, x: v.remote_services.trigger_charging_settings_update(
            target_soc=int(x)
        ),
        icon="mdi:battery-charging-medium",
        unit_of_measurement=PERCENTAGE,
    ),
    "ac_limit": BMWSelectEntityDescription(
        key="ac_limit",
        name="AC Charging Limit",
        is_available=lambda x: x.is_remote_set_ac_limit_enabled,
        dynamic_options=lambda x: [
            str(lim) for lim in x.charging_profile.ac_available_limits
        ],
        current_option=lambda x: str(x.charging_profile.ac_current_limit),  # type: ignore[union-attr]
        remote_service=lambda v, x: v.remote_services.trigger_charging_settings_update(
            ac_limit=int(x)
        ),
        icon="mdi:current-ac",
        unit_of_measurement=UnitOfElectricCurrent.AMPERE,
    ),
    "charging_mode": BMWSelectEntityDescription(
        key="charging_mode",
        name="Charging Mode",
        is_available=lambda x: x.is_charging_plan_supported,
        options=[c.value for c in ChargingMode if c != ChargingMode.UNKNOWN],
        current_option=lambda x: x.charging_profile.charging_mode.value,  # type: ignore[union-attr]
        remote_service=lambda v, x: v.remote_services.trigger_charging_profile_update(
            charging_mode=ChargingMode(x)
        ),
        icon="mdi:vector-point-select",
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the MyBMW lock from config entry."""
    coordinator: BMWDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[BMWSelect] = []

    for vehicle in coordinator.account.vehicles:
        if not coordinator.read_only:
            entities.extend(
                [
                    BMWSelect(coordinator, vehicle, description)
                    for description in NUMBER_TYPES.values()
                    if description.is_available(vehicle)
                ]
            )
    async_add_entities(entities)


class BMWSelect(BMWBaseEntity, SelectEntity):
    """Representation of BMW select entity."""

    entity_description: BMWSelectEntityDescription

    def __init__(
        self,
        coordinator: BMWDataUpdateCoordinator,
        vehicle: MyBMWVehicle,
        description: BMWSelectEntityDescription,
    ) -> None:
        """Initialize an BMW select."""
        super().__init__(coordinator, vehicle)
        self.entity_description = description
        self._attr_unique_id = f"{vehicle.vin}-{description.key}"
        self._attr_options = description.options or (
            description.dynamic_options(vehicle) if description.dynamic_options else []
        )
        self._attr_current_option = description.current_option(vehicle)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.debug(
            "Updating select '%s' of %s", self.entity_description.key, self.vehicle.name
        )
        self._attr_current_option = self.entity_description.current_option(self.vehicle)
        super()._handle_coordinator_update()

    async def async_select_option(self, option: str) -> None:
        """Update to the vehicle."""
        _LOGGER.debug(
            "Executing '%s' on vehicle '%s' to value '%s'",
            self.entity_description.key,
            self.vehicle.vin,
            option,
        )
        await self.entity_description.remote_service(self.vehicle, option)
