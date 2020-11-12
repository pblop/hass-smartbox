# hass-smartbox
Home Assistant integration for heating smartboxes.

Uses the [smartbox](https://github.com/graham33/smartbox) Python module.

**Note: this is very much a work in progress**, a lot of functionality is
missing or not fully working!

See [CHANGELOG.md](./CHANGELOG.md) for release notes.

## TODO
* Packaging (requirements.txt etc.)
* Tests
* CI
* Docs
* Handle presets (e.g. away and eco)
* config_flow (only configured via yaml atm)
* Handle adding and removing entities properly
* Ensure token refresh is working
* Graceful cleanup/shutdown of update task
* Handle node types other than heater
