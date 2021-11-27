"""Constants for Daikin Residential Controller."""

from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_TOKEN,
    CONF_ICON,
    CONF_NAME,
    CONF_TYPE,
    CONF_UNIT_OF_MEASUREMENT,
    DEVICE_CLASS_TEMPERATURE,
    ENERGY_KILO_WATT_HOUR,
    TEMP_CELSIUS,
)

DOMAIN = "daikin_residential"

CONF_TOKENSET = CONF_TOKEN + "set"

DAIKIN_DATA = "daikin_data"
DAIKIN_API = "daikin_api"
DAIKIN_DEVICES = "daikin_devices"
DAIKIN_DISCOVERY_NEW = "daikin_discovery_new_{}"

ATTR_ON_OFF = "on_off"
ATTR_PRESET_MODE = "preset_mode"
ATTR_OPERATION_MODE = "operation_mode"
ATTR_TEMPERATURE = "temperature"
ATTR_TARGET_TEMPERATURE = "target_temperature"
ATTR_INSIDE_TEMPERATURE = "inside_temperature"
ATTR_OUTSIDE_TEMPERATURE = "outside_temperature"
ATTR_ENERGY_CONSUMPTION = "energy_consumption"
ATTR_HUMIDITY = "humidity"
ATTR_TARGET_HUMIDITY = "target_humidity"
ATTR_FAN_MODE = "fan_mode"
ATTR_FAN_SPEED = "fan_speed"
ATTR_HSWING_MODE = "hswing_mode"
ATTR_VSWING_MODE = "vswing_mode"
ATTR_SWING_AUTO = "auto"
ATTR_SWING_SWING = "swing"
ATTR_SWING_STOP = "stop"
ATTR_COOL_ENERGY = "cool_energy"
ATTR_HEAT_ENERGY = "heat_energy"

MP_CLIMATE = "climateControl"
DP_ON_OFF = "onOffMode"
DP_OPERATION_MODE = "operationMode"
DP_SENSORS = "sensoryData"
DP_TEMPERATURE = "temperatureControl"
DP_FAN = "fanControl"
DP_CONSUMPTION = "consumptionData"

DAIKIN_CMD_SETS = {
    ATTR_ON_OFF: [MP_CLIMATE, DP_ON_OFF, ""],
    ATTR_PRESET_MODE: [MP_CLIMATE, "", ""],
    ATTR_OPERATION_MODE: [MP_CLIMATE, DP_OPERATION_MODE, ""],
    ATTR_OUTSIDE_TEMPERATURE: [MP_CLIMATE, DP_SENSORS, "/outdoorTemperature"],
    ATTR_INSIDE_TEMPERATURE: [MP_CLIMATE, DP_SENSORS, "/roomTemperature"],
    ATTR_TARGET_TEMPERATURE: [
        MP_CLIMATE,
        DP_TEMPERATURE,
        "/operationModes/%operationMode%/setpoints/roomTemperature",
    ],
    ATTR_FAN_MODE: [
        MP_CLIMATE,
        DP_FAN,
        "/operationModes/%operationMode%/fanSpeed/currentMode",
    ],
    ATTR_FAN_SPEED: [
        MP_CLIMATE,
        DP_FAN,
        "/operationModes/%operationMode%/fanSpeed/modes/fixed",
    ],
    ATTR_HSWING_MODE: [
        MP_CLIMATE,
        DP_FAN,
        "/operationModes/%operationMode%/fanDirection/horizontal/currentMode",
    ],
    ATTR_VSWING_MODE: [
        MP_CLIMATE,
        DP_FAN,
        "/operationModes/%operationMode%/fanDirection/vertical/currentMode",
    ],
    ATTR_ENERGY_CONSUMPTION: [MP_CLIMATE, DP_CONSUMPTION, "/electrical"],
}

ATTR_STATE_ON = "on"
ATTR_STATE_OFF = "off"

FAN_FIXED = "fixed"
FAN_QUIET = "Silence"

SWING_OFF = "Off"
SWING_BOTH = "3D"
SWING_VERTICAL = "Vertical"
SWING_HORIZONTAL = "Horizontal"

PRESET_STREAMER = "streamer"

SENSOR_TYPE_TEMPERATURE = "temperature"
SENSOR_TYPE_HUMIDITY = "humidity"
SENSOR_TYPE_POWER = "power"
SENSOR_TYPE_ENERGY = "energy"
SENSOR_PERIOD_DAILY = "d"
SENSOR_PERIOD_WEEKLY = "w"
SENSOR_PERIOD_YEARLY = "m"
SENSOR_PERIODS = {
    SENSOR_PERIOD_DAILY: "Daily",
    SENSOR_PERIOD_WEEKLY: "Weekly",
    SENSOR_PERIOD_YEARLY: "Yearly",
}

SENSOR_TYPES = {
    ATTR_INSIDE_TEMPERATURE: {
        CONF_NAME: "Inside Temperature",
        CONF_TYPE: SENSOR_TYPE_TEMPERATURE,
        CONF_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
        CONF_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
    },
    ATTR_OUTSIDE_TEMPERATURE: {
        CONF_NAME: "Outside Temperature",
        CONF_TYPE: SENSOR_TYPE_TEMPERATURE,
        CONF_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
        CONF_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
    },
    ATTR_COOL_ENERGY: {
        CONF_NAME: "Cool Energy Consumption",
        CONF_TYPE: SENSOR_TYPE_ENERGY,
        CONF_ICON: "mdi:snowflake",
        CONF_UNIT_OF_MEASUREMENT: ENERGY_KILO_WATT_HOUR,
    },
    ATTR_HEAT_ENERGY: {
        CONF_NAME: "Heat Energy Consumption",
        CONF_TYPE: SENSOR_TYPE_ENERGY,
        CONF_ICON: "mdi:fire",
        CONF_UNIT_OF_MEASUREMENT: ENERGY_KILO_WATT_HOUR,
    },
}

CONF_UUID = "uuid"

KEY_MAC = "mac"
KEY_IP = "ip"

TIMEOUT = 60
