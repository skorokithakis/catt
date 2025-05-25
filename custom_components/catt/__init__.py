# This file makes Home Assistant recognize this directory as an integration.
# For CATT, which is primarily a CLI tool, this allows HACS to manage it.

DOMAIN = "catt"

async def async_setup(hass, config):
    # Mark domain as loaded. CATT itself doesn't integrate deeply with Home Assistant's event loop
    # or entity system in a typical way, so setup is minimal.
    hass.data[DOMAIN] = {}
    return True

async def async_setup_entry(hass, entry):
    # CATT does not use config entries.
    return True

async def async_unload_entry(hass, entry):
    # CATT does not use config entries.
    return True
