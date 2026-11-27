"""hOn component constants."""

from enum import Enum, IntEnum
from homeassistant.components.climate.const import (
    FAN_OFF,
    FAN_AUTO,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_HIGH,
    SWING_OFF,
    SWING_BOTH,
    SWING_VERTICAL,
    SWING_HORIZONTAL,
    HVACMode,
)

DOMAIN = "hon"


CONF_ID_TOKEN = "token"
CONF_COGNITO_TOKEN = "cognito_token"
CONF_REFRESH_TOKEN = "refresh_token"
CONF_FRAMEWORK = "framework"

PLATFORMS = [
    "climate", 
    "sensor",
    "binary_sensor",
    "button",
    "switch",
    "select"
]

'''
    "select",
    "number" '''

AUTH_API        = "https://account2.hon-smarthome.com/SmartHome"
API_URL         = "https://api-iot.he.services"
APP_VERSION     = "2.27.9"
OS_VERSION      = 31
OS              = "android"
DEVICE_MODEL    = "exynos9820"



class APPLIANCE_TYPE(IntEnum):
    WASHING_MACHINE = 1,
    WASH_DRYER      = 2,
    OVEN            = 4,
    WINE_COOLER     = 6,
    PURIFIER        = 7,
    TUMBLE_DRYER    = 8,
    DISH_WASHER     = 9,
    CLIMATE         = 11,
    FRIDGE          = 14

APPLIANCE_DEFAULT_NAME = {
    "1": "Washing Machine",
    "2": "Wash Dryer",
    "4": "Oven",
    "6": "Wine Cooler",
    "7": "Purifier",
    "8": "Tumble Dryer",
    "9": "Dish Washer",
    "11": "Climate",
    "14": "Fridge",
}

CLIMATE_FAN_MODE = {
    FAN_OFF: "0",
    FAN_LOW: "3",
    FAN_MEDIUM: "2",
    FAN_HIGH: "1",
    FAN_AUTO: "5",
}

CLIMATE_HVAC_MODE = {
    HVACMode.AUTO: "0",
    HVACMode.COOL: "1",
    HVACMode.HEAT: "4",
    HVACMode.DRY: "2",
    HVACMode.FAN_ONLY: "6",
}

class ClimateSwingVertical:
    AUTO = "8"
    VERY_LOW = "7"
    LOW = "6"
    MIDDLE = "5"
    HIGH = "4"
    HEALTH_LOW = "3"
    VERY_HIGH = "2"
    HEALTH_HIGH = "1"

class ClimateSwingHorizontal:
    AUTO = "7"
    MIDDLE = "0"
    FAR_LEFT = "3"
    LEFT = "4"
    RIGHT = "5"
    FAR_RIGHT = "6"

class ClimateEcoPilotMode:
    OFF = "0"
    AVOID = "1"
    FOLLOW = "2"


#WASHING_MACHINE_DOOR_LOCK_STATUS = {
#    "1": "Locked",
#    "0": "Unlocked"
#}

#WASHING_MACHINE_PROGRAM = {
#    "0": { 
#        "name": "fragile",
#        "spinSpeed": "400",
#        "temp": "30",
#        "rinseIterations": "1",
#        "mainWashTime": "10",
#        "autoSoftenerStatus": "1"
#                },
#    "1": { 
#        "name": "quotidien sale",
#        "spinSpeed": "1400",
#        "temp": "40",
#        "rinseIterations": "2",
#        "mainWashTime": "15",
#        "autoSoftenerStatus": "1"
#                },
#}

#PURIFIER_LIGHT_VALUE  = {
#    "0": "Off",
#    "1": "50%",
#    "2": "100%"
#}


# Lavastoviglie: nomi italiani dei programmi come nell'app hOn (Candy CS 6C2S3PSA, 27 nov 2026).
# Ordine = ordine del menu "Programma". I programmi che l'app non mostra (iot_voice_*, iot_checkup) restano fuori.
DW_PROGRAM_NAMES = {
    "eco": "Eco 45°C",
    "universal": "Universale 60°C",
    "intensive": "Intensivo",
    "auto_wash_soil": "Auto Wash",
    "auto_care_soil": "Auto Care",
    "auto_plus_soil": "Auto Plus Sporco",
    "prewash": "Prelavaggio",
    "rapid_20": "Rapido 20'",
    "rapid_35": "Wash&Dry 35'",
    "rapid_49": "Rapido 49'",
    "rapid_59": "Rapido 59'",
    "glass": "Calici",
    "silent": "Notte",
    "hygiene": "Igiene",
    "iot_turbopower": "Turbo Power",
    "iot_baby_care": "Baby Care",
    "iot_extra_hygiene": "Extra Hygiene",
    "iot_super_wash": "Super Wash",
    "iot_wok_grids_maxi_pans_soil": "Maxi Stoviglie e Griglie",
    "iot_daily_care_soil": "Daily Care",
    "iot_power_mix_wash_soil": "Power Mix Wash",
    "iot_pot_&_pans": "Pentole & Padelle",
    "iot_pyrex_and_glassware": "Pyrex & Glassware",
    "iot_plastic_tupperware": "Plastiche & Tupperware",
    "iot_cocktail_glasses_soil": "Cocktail Glasses",
    "iot_pizza_menu_soil": "Pizza Menu",
    "iot_porcelain": "Porcellane",
    "iot_china_crystals": "Cristalli",
    "iot_party": "Party",
    "iot_happy_hour": "Happy Hour",
    "iot_dinner_for_two": "Cena di coppia",
    "iot_breakfast": "Colazione",
    "iot_super_flash": "Super Flash",
    "dishwasher_care": "Pulizia lavastoviglie",
}

# Opzioni del lavaggio (interruttori usati dal pulsante "Avvia"): chiave hOn -> (nome, icona)
DW_OPTIONS = {
    "halfLoad":   ("Mezzo carico", "mdi:circle-half-full"),
    "extraDry":   ("Extra asciutto", "mdi:weather-sunny"),
    "openDoor":   ("Apri porta a fine ciclo", "mdi:door-open"),
    "hygiene":    ("Igiene", "mdi:shield-check-outline"),
    "ecoExpress": ("Eco express", "mdi:leaf"),
    "intensive":  ("Intensivo", "mdi:water-plus"),
    "tabStatus":  ("Pastiglie tutto in uno", "mdi:pill"),
}

# Impostazioni della lavastoviglie (comando "settings"): chiave -> (nome, icona, invertito)
DW_SETTINGS_SWITCHES = {
    "buzzerDisabled":        ("Segnale acustico", "mdi:volume-high", True),
    "lightStatus":           ("Luce interna", "mdi:lightbulb", False),
    "lastCycleSavingStatus": ("Ricorda ultimo programma", "mdi:history", False),
}
