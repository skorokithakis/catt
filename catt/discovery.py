from typing import Dict
from typing import List
from typing import Optional
from typing import Union

import pychromecast

from .error import CastError
from .util import is_ipaddress

DEFAULT_PORT = 8009


def get_casts(names: Optional[List[str]] = None) -> List[pychromecast.Chromecast]:
    """
    Discover all available devices, optionally filtering them with list of specific device names
    (which will speedup discovery, as pychromecast does this in a non-blocking manner).

    :param names: Optional list of device names.
    :type names: List[str]
    :returns: List of Chromecast objects.
    :rtype: List[pychromecast.Chromecast]
    """

    if names:
        cast_infos, browser = pychromecast.discovery.discover_listed_chromecasts(friendly_names=names)
    else:
        cast_infos, browser = pychromecast.discovery.discover_chromecasts()

    casts = [pychromecast.get_chromecast_from_cast_info(c, browser.zc) for c in cast_infos]

    for cast in casts:
        cast.wait()

    browser.stop_discovery()
    casts.sort(key=lambda c: c.cast_info.friendly_name)
    return casts


def get_cast_infos() -> List[pychromecast.CastInfo]:
    """
    Discover all available devices, and collect info from them.

    :returns: Various device info, packed in CastInfo namedtuple.
    :rtype: pychromecast.CastInfo
    """

    return [c.cast_info for c in get_casts()]


def get_cast_with_name(cast_name: Union[str, None]) -> Optional[pychromecast.Chromecast]:
    """
    Get specific device if supplied name is not None,
    otherwise the device with the name that has the lowest alphabetical value.

    :param device_name: Name of device.
    :type device_name: str
    :returns: Chromecast object.
    :rtype: pychromecast.Chromecast
    """

    casts = get_casts([cast_name]) if cast_name else get_casts()
    return casts[0] if casts else None


def get_cast_with_ip(cast_ip: str, port: int = DEFAULT_PORT) -> Optional[pychromecast.Chromecast]:
    """
    Get specific device using its ip-address (and optionally port).

    :param device_ip: Ip-address of device.
    :type device_name: str
    :param port: Optional port number of device.
    :returns: Chromecast object.
    :rtype: pychromecast.Chromecast
    """

    try:
        # tries = 1 is necessary in order to stop pychromecast engaging
        # in a retry behaviour when ip is correct, but port is wrong.
        cast = pychromecast.Chromecast(cast_ip, port=port, tries=1)
        return cast
    except pychromecast.error.ChromecastConnectionError:
        return None


def cast_ip_exists(cast_ip: str) -> bool:
    """
    Get availability of specific device using its ip-address.

    :param device_ip: Ip-address of device.
    :type device_name: str
    :returns: Availability of device.
    :rtype: bool
    """

    return bool(get_cast_with_ip(cast_ip))


def get_cast(cast_desc: Optional[str] = None) -> pychromecast.Chromecast:
    """
    Attempt to connect with requested device (or any device if none has been specified).

    :param device_desc: Can be an ip-address or a name.
    :type device_desc: str
    :returns: Chromecast object for use in a CastController.
    :rtype: pychromecast.Chromecast
    """

    cast = None

    if cast_desc and is_ipaddress(cast_desc):
        cast = get_cast_with_ip(cast_desc, DEFAULT_PORT)
        if not cast:
            msg = "No device found at {}".format(cast_desc)
            raise CastError(msg)
    else:
        cast = get_cast_with_name(cast_desc)
        if not cast:
            msg = 'Specified device "{}" not found'.format(cast_desc) if cast_desc else "No devices found"
            raise CastError(msg)

    return cast
