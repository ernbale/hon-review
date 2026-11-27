import logging
from dataclasses import dataclass
from typing import Any


from .const import DOMAIN, APPLIANCE_TYPE, DW_OPTIONS, DW_SETTINGS_SWITCHES
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import EntityCategory
from .device import HonDevice
from .parameter import HonParameter, HonParameterFixed, HonParameterEnum, HonParameterRange, HonParameterProgram
from .base import HonBaseCoordinator, HonBaseSwitchEntity


from homeassistant.core import callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.switch import SwitchEntityDescription, SwitchEntity

_LOGGER = logging.getLogger(__name__)

@dataclass(frozen=True)
class HonControlSwitchEntityDescription(SwitchEntityDescription):
    turn_on_key: str = ""
    turn_off_key: str = ""


@dataclass(frozen=True)
class HonSwitchEntityDescription(SwitchEntityDescription):
    pass



async def async_setup_entry(hass, entry: ConfigEntry, async_add_entities) -> None:

    hon = hass.data[DOMAIN][entry.unique_id]

    appliances = []
    for appliance in hon.appliances:
        coordinator = await hon.async_get_coordinator(appliance)
        device = coordinator.device

        # Lavastoviglie: opzioni del lavaggio (per "Avvia") e impostazioni
        if appliance.get("applianceTypeId") == APPLIANCE_TYPE.DISH_WASHER:
            if "startProgram" in device.commands:
                for key in DW_OPTIONS:
                    appliances.append(HonDishWasherOptionSwitch(coordinator, key))
            if "settings" in device.commands:
                for key in DW_SETTINGS_SWITCHES:
                    if device.get(key, "N/A") != "N/A":
                        appliances.append(HonDishWasherSettingSwitch(coordinator, key))

        if (("settings" in device.commands) 
            and (device.get("silentSleepStatus", "N/A") != "N/A")):

            description = HonSwitchEntityDescription(
                key="silentSleepStatus",
                name="Sleep Mode",
                icon="mdi:bed",
                translation_key="sleep_mode",
            )
            appliances.extend([HonSwitchEntity(hass, coordinator, entry, appliance, description)])
            await coordinator.async_request_refresh()

        if (("settings" in device.commands) 
            and (device.get("screenDisplayStatus", "N/A") != "N/A")):

            description = HonSwitchEntityDescription(
                key="screenDisplayStatus",
                name="Screen Display",
                icon="mdi:monitor-small",
                translation_key="screen_display_status",
            )
            appliances.extend([HonSwitchEntity(hass, coordinator, entry, appliance, description)])
            await coordinator.async_request_refresh()


        if (("settings" in device.commands) 
            and (device.get("muteStatus", "N/A") != "N/A")):

            description = HonSwitchEntityDescription(
                key="muteStatus",
                name="Silent Mode",
                icon="mdi:volume-off",
                translation_key="silent_mode",
            )
            appliances.extend([HonSwitchEntity(hass, coordinator, entry, appliance, description)])
            await coordinator.async_request_refresh()


        if (("settings" in device.commands) 
            and (device.get("echoStatus", "N/A") != "N/A")):

            description = HonSwitchEntityDescription(
                key="echoStatus",
                name="Echo",
                icon="mdi:account-voice",
                translation_key="echo_status"
            )
            appliances.extend([HonSwitchEntity(hass, coordinator, entry, appliance, description, True)])
            await coordinator.async_request_refresh()


        if (("settings" in device.commands) 
            and (device.get("rapidMode", "N/A") != "N/A")):

            description = HonSwitchEntityDescription(
                key="rapidMode",
                name="Rapid Mode",
                icon="mdi:car-turbocharger",
                translation_key="rapid_mode",
            )
            appliances.extend([HonSwitchEntity(hass, coordinator, entry, appliance, description)])
            await coordinator.async_request_refresh()


        if (("settings" in device.commands) 
            and (device.get("10degreeHeatingStatus", "N/A") != "N/A")):

            description = HonSwitchEntityDescription(
                key="10degreeHeatingStatus",
                name="10° Heating",
                icon="mdi:heat-wave",
                translation_key="10_degree_heating",
            )
            appliances.extend([HonSwitchEntity(hass, coordinator, entry, appliance, description)])
            await coordinator.async_request_refresh()


        if (("settings" in device.commands) 
            and (device.get("ecoMode", "N/A") != "N/A")):

            description = HonSwitchEntityDescription(
                key="ecoMode",
                name="Eco Mode",
                icon="mdi:sprout",
                translation_key="eco_mode",
            )
            appliances.extend([HonSwitchEntity(hass, coordinator, entry, appliance, description)])
            await coordinator.async_request_refresh()


        if (("settings" in device.commands) 
            and (device.get("healthMode", "N/A") != "N/A")):

            description = HonSwitchEntityDescription(
                key="healthMode",
                name="Health Mode",
                icon="mdi:heart",
                translation_key="health_mode",
            )
            appliances.extend([HonSwitchEntity(hass, coordinator, entry, appliance, description)])
            await coordinator.async_request_refresh()


    async_add_entities(appliances)




class HonSwitchEntity(HonBaseSwitchEntity):
    entity_description: HonSwitchEntityDescription

    def __init__(self, hass, coordinator, entry, appliance, entity_description, invert = False) -> None:
        super().__init__(coordinator, appliance, entity_description)
        self.invert = invert

    def _setting_key(self) -> str:
        return f"settings.{self.entity_description.key}"

    def _setting(self):
        return self._device.settings.get(self._setting_key())

    def _target_value(self, turn_on: bool) -> str:
        if self.invert:
            return "0" if turn_on else "1"
        return "1" if turn_on else "0"

    @property
    def is_on(self) -> bool | None:
        """Return True if entity is on."""
        if( self.invert == True ):
            return self._device.get(self.entity_description.key, "1") == "0"
        return self._device.get(self.entity_description.key, "0") == "1"

    async def async_turn_on(self, **kwargs: Any) -> None:
        setting = self._setting()
        if setting is not None:
            if type(setting) == HonParameter:
                return
            if self.invert:
                setting.value = setting.min if isinstance(setting, HonParameterRange) else 0
            else:
                setting.value = setting.max if isinstance(setting, HonParameterRange) else 1
            await self._device.commands["settings"].send()
            value = str(setting.value)
        else:
            value = self._target_value(True)
            await self.coordinator.async_set({self.entity_description.key: value})

        self._device.set(self.entity_description.key, value)
        self.async_write_ha_state()
        self.coordinator.async_set_updated_data({})

    async def async_turn_off(self, **kwargs: Any) -> None:
        setting = self._setting()
        if setting is not None:
            if type(setting) == HonParameter:
                return
            if self.invert:
                setting.value = setting.max if isinstance(setting, HonParameterRange) else 1
            else:
                setting.value = setting.min if isinstance(setting, HonParameterRange) else 0
            await self._device.commands["settings"].send()
            value = str(setting.value)
        else:
            value = self._target_value(False)
            await self.coordinator.async_set({self.entity_description.key: value})

        self._device.set(self.entity_description.key, value)
        self.async_write_ha_state()
        self.coordinator.async_set_updated_data({})

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not super().available:
            _LOGGER.warning("HonSwitchEntity not available: super() is not")
            return False
        if not self._device.get("remoteCtrValid", "1") == "1":
            _LOGGER.warning("HonSwitchEntity not available: remoteCtrValid==1")
            return False
        if self._device.get("attributes.lastConnEvent.category") == "DISCONNECTED":
            _LOGGER.warning("HonSwitchEntity not available: DISCONNECTED")
            return False

        setting = self._setting()
        if setting is None:
            return self._device.get(self.entity_description.key, None) is not None

        #_LOGGER.warning(setting)
        #if isinstance(setting, HonParameterRange) and len(setting.values) < 2:
        #    return False
        return True

    @callback
    def _handle_coordinator_update(self, update: bool = True) -> None:
        self._attr_is_on = self.is_on
        if update:
            self.async_write_ha_state()




class HonDishWasherOptionSwitch(CoordinatorEntity, SwitchEntity, RestoreEntity):
    """Opzione del prossimo lavaggio: non manda niente alla macchina, la usa il pulsante "Avvia"."""

    def __init__(self, coordinator, key) -> None:
        super().__init__(coordinator)
        self._device = coordinator.device
        self._key = key
        name, icon = DW_OPTIONS[key]
        self._attr_unique_id = f"{self._device.mac_address}_dw_option_{key}"
        self._attr_name = f"{self._device.name} {name}"
        self._attr_icon = icon
        if not hasattr(self._device, "dw_options"):
            self._device.dw_options = {}
        self._device.dw_options.setdefault(key, False)

    @property
    def device_info(self):
        return self._device.device_info

    @property
    def is_on(self):
        return bool(self._device.dw_options.get(self._key))

    async def async_turn_on(self, **kwargs) -> None:
        self._device.dw_options[self._key] = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        self._device.dw_options[self._key] = False
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is not None and last.state in ("on", "off"):
            self._device.dw_options[self._key] = last.state == "on"


class HonDishWasherSettingSwitch(CoordinatorEntity, SwitchEntity):
    """Impostazione della lavastoviglie: cambia subito sulla macchina (comando "settings")."""

    def __init__(self, coordinator, key) -> None:
        super().__init__(coordinator)
        self._device = coordinator.device
        self._key = key
        name, icon, self._invert = DW_SETTINGS_SWITCHES[key]
        self._attr_unique_id = f"{self._device.mac_address}_dw_setting_{key}"
        self._attr_name = f"{self._device.name} {name}"
        self._attr_icon = icon
        self._attr_entity_category = EntityCategory.CONFIG

    @property
    def device_info(self):
        return self._device.device_info

    @property
    def is_on(self):
        on = str(self._device.get(self._key)) == "1"
        return (not on) if self._invert else on

    async def _set(self, on: bool) -> None:
        value = (0 if on else 1) if self._invert else (1 if on else 0)
        await self._device.settings_command({self._key: value}).send()
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self, **kwargs) -> None:
        await self._set(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self._set(False)
