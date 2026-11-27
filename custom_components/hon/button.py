import logging
from .const import DOMAIN, APPLIANCE_TYPE, DW_PROGRAM_NAMES, DW_OPTIONS
from homeassistant.exceptions import HomeAssistantError
from homeassistant.config_entries import ConfigEntry

from homeassistant.helpers import entity_registry as er
from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.persistent_notification import create
#from homeassistant.helpers.template import device_id as get_device_id

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry: ConfigEntry, async_add_entities) -> None:

    hon = hass.data[DOMAIN][entry.unique_id]

    appliances = []
    for appliance in hon.appliances:

        coordinator = await hon.async_get_coordinator(appliance)
        device = coordinator.device
        appliances.extend([HonBaseButtonEntity(coordinator, appliance)])
        if( "settings" in device.commands ):
            appliances.extend([HonBaseSettingsButtonEntity(coordinator, appliance)])
        if appliance.get("applianceTypeId") == APPLIANCE_TYPE.DISH_WASHER:
            if "startProgram" in device.commands:
                appliances.append(HonDishWasherStartButton(coordinator))
            if "stopProgram" in device.commands:
                appliances.append(HonDishWasherStopButton(coordinator))
    async_add_entities(appliances)



class HonBaseButtonEntity(CoordinatorEntity, ButtonEntity):
    def __init__(self, coordinator, appliance) -> None:
        super().__init__(coordinator)
        self._coordinator   = coordinator
        self._device        = coordinator.device

        self._attr_unique_id = self._device.mac_address + "_start_button"
        self._attr_name = self._device.name + " Get programs details"

    @property
    def device_info(self):
        return self._device.device_info

    async def async_press(self) -> None:
        """Handle the button press."""
        command = self._device.commands.get("startProgram")
        programs = command.get_programs()
        #device_id = get_device_id(self._coordinator.hass, self.entity_id)
        device_id = None
        entry = er.async_get(self._coordinator.hass).async_get(self.entity_id)
        if entry:
            device_id = entry.device_id

        for program in programs.keys():
            command.set_program(program)
            command = self._device.commands.get("startProgram")
            alert_text, example = command.dump()

            text = f"""#### Parameters:
{alert_text}
#### Start this program with default parameters:
    service: hon.start_program
    data:
      program: {program}
    target:
      device_id: {device_id}

#### Start this program with customized parameters:
    service: hon.start_program
    data:
      program: {program}
      parameters: >-
        {example}
    target:
      device_id: {device_id}
"""
            create(self._coordinator.hass, text, "Program ["+program+"]")



class HonBaseSettingsButtonEntity(CoordinatorEntity, ButtonEntity):
    def __init__(self, coordinator, appliance) -> None:
        super().__init__(coordinator)
        self._coordinator   = coordinator
        self._device        = coordinator.device

        self._attr_unique_id = self._device.mac_address + "_settings_button"
        self._attr_name = self._device.name + " Get settings details"

    @property
    def device_info(self):
        return self._device.device_info

    async def async_press(self) -> None:
        """Handle the button press."""
        #device_id = get_device_id(self._coordinator.hass, self.entity_id)
        device_id = None
        entry = er.async_get(self._coordinator.hass).async_get(self.entity_id)
        if entry:
            device_id = entry.device_id
        command = self._device.commands.get("settings")
        alert_text, example = command.dump()

        text = f"""#### Parameters:
{alert_text}
#### Update settings:
    service: hon.update_settings
    data:
      parameters: >-
        {example}
    target:
      device_id: {device_id}
"""
        create(self._coordinator.hass, text, "Get all settings")




class HonDishWasherStartButton(CoordinatorEntity, ButtonEntity):
    """Avvia il programma scelto nel menu "Programma" (opzioni di base del programma)."""

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._device = coordinator.device
        self._attr_unique_id = self._device.mac_address + "_dw_start_button"
        self._attr_name = self._device.name + " Avvia"
        self._attr_icon = "mdi:play"

    @property
    def available(self) -> bool:
        # Grigio (non disponibile) se un ciclo e' in corso o il controllo remoto e' spento
        return (super().available
                and str(self._device.get("machMode")) not in ("2", "3")
                and str(self._device.get("remoteCtrValid")) == "1")

    @property
    def device_info(self):
        return self._device.device_info

    async def async_press(self) -> None:
        if str(self._device.get("remoteCtrValid")) != "1":
            raise HomeAssistantError("Controllo remoto spento: chiudi lo sportello, accendi la lavastoviglie e premi il tasto Wi-Fi.")
        if str(self._device.get("machMode")) in ("2", "3"):
            raise HomeAssistantError("Un programma e' gia' in corso: per cambiarlo premi prima Ferma.")
        program = getattr(self._device, "dw_selected_program", None) or "eco"
        _LOGGER.info("Lavastoviglie: avvio %s (%s)", program, DW_PROGRAM_NAMES.get(program, program))
        # Opzioni dagli interruttori: tutte esplicite (0/1), cosi' non restano quelle
        # dell'ultimo ciclo; quelle che il programma non accetta vengono ignorate.
        chosen = getattr(self._device, "dw_options", {})
        parameters = {k: (1 if chosen.get(k) else 0) for k in DW_OPTIONS}
        _LOGGER.info("Lavastoviglie: opzioni %s", parameters)
        await self._device.start_command(program, parameters).send()
        await self.coordinator.async_request_refresh()


class HonDishWasherStopButton(CoordinatorEntity, ButtonEntity):
    """Ferma il programma in corso con lo stopProgram vero dell'apparecchio."""

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._device = coordinator.device
        self._attr_unique_id = self._device.mac_address + "_dw_stop_button"
        self._attr_name = self._device.name + " Ferma"
        self._attr_icon = "mdi:stop"

    @property
    def available(self) -> bool:
        # Disponibile solo con un ciclo in corso o in pausa
        return super().available and str(self._device.get("machMode")) in ("2", "3")

    @property
    def device_info(self):
        return self._device.device_info

    async def async_press(self) -> None:
        _LOGGER.info("Lavastoviglie: stop")
        await self._device.stop_command().send()
        await self.coordinator.async_request_refresh()
