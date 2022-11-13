from homeassistant.const import TEMP_CELSIUS, TEMP_FAHRENHEIT
from homeassistant.util.unit_conversion import TemperatureConverter


def simple_celsius_to_fahrenheit(temp: float) -> float:
    return temp * 9 / 5 + 32


def convert_temp(hass, node_units, temp):
    # Temperatures are converted to the units of the HA
    # instance, so do the same for comparison
    unit = TEMP_CELSIUS if node_units == "C" else TEMP_FAHRENHEIT
    return TemperatureConverter.convert(temp, unit, hass.config.units.temperature_unit)


def round_temp(hass, temp):
    print(f"TEMP {temp} {type(temp)}")
    # HA uses different precisions for Fahrenheit (whole
    # integers) vs Celsius (tenths)
    if hass.config.units.temperature_unit == TEMP_CELSIUS:
        return round(temp, 1)
    else:
        return round(temp)
