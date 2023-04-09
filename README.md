# hass-smartbox ![hassfest](https://github.com/graham33/hass-smartbox/workflows/Validate%20with%20hassfest/badge.svg) [![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration) [![codecov](https://codecov.io/gh/graham33/hass-smartbox/branch/main/graph/badge.svg?token=F3VFCU9WPA)](https://codecov.io/gh/graham33/hass-smartbox)
Home Assistant integration for heating smartboxes.

## Supported Heaters

The integration supports heaters of different types from different manufacturers
that use a common cloud protocol. Most models use a WiFi 'smartbox' device
which the heater nodes communicate with, but some have WiFi capabilities in each
heater. Note there is no option for local control without the cloud service
dependency.

Each heater node is modelled as a Home Assistant climate entity. Some other
entities are provided to expose other data, depending on the type of heater. An
Away mode switch is provided for each smartbox device, as well as a Power Limit
number entity which can be used to set the overall power limit.

### `htr` Heater Nodes
For example Climastar, some Haverland models, HJM, Wibo
* Climate:
  * Modes: 'manual' and 'auto'
  * Presets: 'home and 'away'
* Sensor: Temperature, Energy, Power, Duty Cycle
* Switch: Window Mode (if supported), True Radiant Mode (if supported)

### `acm` Accumulator Nodes
For example Elnur Gabarron
* Climate:
  * Modes: 'manual' and 'auto'
  * Presets: 'home and 'away'
* Sensor: Temperature, Power, Charge Level
* Switch: Window Mode (if supported), True Radiant Mode (if supported)

### `htr_mod` Heater Nodes
For example Haverland Smartwave and Ultrad
* Climate:
  * Modes: 'manual', 'auto', 'self_learn' and 'presence'
  * Presets: 'away', 'comfort', 'eco', 'ice' and 'away'
* Sensor: Temperature
* Switch: Window Mode (if supported), True Radiant Mode (if supported)

The modes and presets for htr_mod heaters are mapped as follows:

| htr\_mod mode | htr\_mod selected_temp | HA HVAC mode | HA preset   |
|---------------|------------------------|--------------|-------------|
| manual        | comfort                | HEAT         | COMFORT     |
|               | eco                    | HEAT         | ECO         |
|               | ice                    | HEAT         | ICE         |
| auto          | *                      | AUTO         | SCHEDULE    |
| self\_learn   | *                      | AUTO         | SELF\_LEARN |
| presence      | *                      | AUTO         | ACTIVITY    |

## Installation
This integration uses the [smartbox] Python module, so make sure to install that
into your Home Assistant python environment first. If you are using hass.io, the
module should be automatically installed from github via the reference in the
`manifest.json` file.

Then, install the `custom_components/smartbox` directory in this repo to your
Home Assistant `custom_components` directory. See the [Home Assistant
integration docs] for details.

### HACS
Initial support is available for installation via HACS, as a [custom
repository]. If you want to install beta releases make sure you have enabled
pre-release support as described in the [HACS FAQ] .

## Configuration
**Note: currently only YAML-based configuration is supported, the UI-based
config flow is not yet implemented.**

Add a section like the following to your Home Assistant config.yaml:

```
smartbox:
  accounts:
  - api_name: <api name>
    username: <api username>
    password: <api password>
    device_ids:
    - <device id>
  basic_auth_creds: <basic auth credentials>
```

You will need the following items of information:
* The API name for your heater vendor. This is visible in the 'API Host' entry
  in the 'Version' menu item in the mobile app/web app. If the host name is of
  the form `api-foo.xxxx` or `api.xxxx` use the values `api-foo` or `api`
  respectively.
* Your username and password used for the mobile app/web app.
* Your smartbox device ID, which is shows as the 'Device ID Code' under My
  Devices in the Home section of the mobile app/web app.
* Basic auth credentials: this is an HTTP Basic Auth credential used to do
  initial authentication with the server. Use the base64 encoded string
  directly. See 'Basic Auth Credential' section below for more details.

It's recommended that you store credentials using the built-in [Home Assistant
secrets management].

### Basic Auth Credential
Initial authentication to the smartbox REST API is protected by HTTP Basic Auth,
in addition to the user's username and password which are then used to obtain an
access token. In order not to undermine the security layer it provides, and also
because it might change over time or vary between implementations, **the token
is not provided here and system owners need to find it themselves**.

### Additional Options
You can also specify the following options (although they have reasonable defaults):

```
smartbox:
  accounts:
  - ...
    session_retry_attempts: 8 # how many times to retry session REST operations
    session_backoff_factor: 0.1 # how much to backoff between REST retries
    socket_reconnect_attempts: 3 # how many times to try reconnecting the socket.io socket
    socket_backoff_factor: 0.1 # how much to backoff between initial socket connect attempts
```

### Use in Energy Dashboard

If you have `htr` type heaters (see Supported Heaters above), then you should
see an Energy entity for each node. These sensors compute the power used over
time by multiplying the reported power usage of the heater by the reported duty
cycle and the time between updates, which appears to be reasonably accurate (at
least compared to the usage reported in the manufacturer's web app).

If you have `acm` heaters, there is a power sensor available but unfortunately
the heaters don't report their duty cycle (i.e. how much of the period since the
last update that the heater was actually active for). One option to use the
values in the Energy dashboard is to aggregate the power sensors into energy
sensors via an integration
(https://www.home-assistant.io/integrations/integration/#energy), as shown
below. However it should be noted that _this is likely to be quite inaccurate_,
since the heater won't be active the whole period between each update.

```
sensor:
  - platform: integration
    source: sensor.living_room
    name: energy_living_room
    unit_prefix: k
    round: 2
    method: left
```

The resulting sensor 'sensor.energy_living_room' can then be added to the Energy
dashboard as soon as it has values.

Unfortunately `htr_mod` heaters don't appear to report power or duty cycle, so
there's no known option to measure their energy consumption (aside from
installing a separate sensor like a Shelly EM on the power input).

## Debugging

Debug logging can be enabled by increasing the log level for the smartbox custom
component and the underlying [smartbox] python module in the Home Assistant
`configuration.yaml`:

```
 logger:
   ...
   logs:
     custom_components.smartbox: debug
     smartbox: debug
   ...
```

**Warning: currently logs might include credentials, so please be careful when
sharing excerpts from logs**

See the [Home Assistant logger docs] for how to view the actual logs. Please
file a [Github issue] with any problems.

## TODO
* config_flow (only configured via yaml atm)
* Handle adding and removing entities properly
* Graceful cleanup/shutdown of update task

[custom repository]: https://hacs.xyz/docs/faq/custom_repositories
[Github issue]: https://github.com/graham33/hass-smartbox/issues
[HACS FAQ]: https://hacs.xyz/docs/faq/beta/
[Home Assistant integration docs]: https://developers.home-assistant.io/docs/creating_integration_file_structure/#where-home-assistant-looks-for-integrations
[Home Assistant logger docs]: https://www.home-assistant.io/integrations/logger/#viewing-logs
[Home Assistant secrets management]: https://www.home-assistant.io/docs/configuration/secrets/
[smartbox]: https://github.com/graham33/smartbox
