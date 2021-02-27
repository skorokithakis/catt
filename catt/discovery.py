from typing import Dict
from typing import List
from typing import Optional
from typing import Union

import pychromecast

from .error import CastError
from .util import is_ipaddress

DEFAULT_PORT = 8009


class CastDevice:
    def __init__(self, cast: pychromecast.Chromecast, ip: str, port: int) -> None:
        self.cast = cast
        self.ip = ip
        self.port = port

    @property
    def info(self):
        return {
            "ip": self.ip,
            "port": self.port,
            "manufacturer": self.cast.device.manufacturer,
            "model_name": self.cast.model_name,
            "uuid": self.cast.uuid,
            "cast_type": self.cast.cast_type,
            "name": self.cast.name,
        }


def get_cast_devices(names: Optional[List[str]] = None) -> List[CastDevice]:
    """
    Discover all available devices, optionally filtering them with list of specific device names
    (which will speedup discovery, as pychromecast does this in a non-blocking manner).

    :param names: Optional list of device names.
    :type names: List[str]
    :returns: List of CastDevice wrapper objects containing cast object and additional ip/port info.
    :rtype: List[CastDevice]
    """

    if names:
        cast_infos, browser = pychromecast.discovery.discover_listed_chromecasts(friendly_names=names)
    else:
        cast_infos, browser = pychromecast.discovery.discover_chromecasts()
    browser.stop_discovery()

    devices = [
        CastDevice(pychromecast.get_chromecast_from_cast_info(c, browser.zc), c.host, c.port) for c in cast_infos
    ]
    devices.sort(key=lambda d: d.cast.name)
    return devices


def get_cast_devices_info() -> Dict[str, Dict[str, Union[str, int]]]:
    """
    Discover all available devices, and collect info from them.

    :returns: Various device info, packed in dict w. device names as keys.
    :rtype: Dict
    """

    devices = get_cast_devices()
    return {d.cast.name: d.info for d in devices}


def get_cast_device_with_name(device_name: Union[str, None]) -> Optional[CastDevice]:
    """
    Get specific device if supplied name is not None,
    otherwise the device with the name that has the lowest alphabetical value.

    :param device_name: Name of device.
    :type device_name: str
    :returns: CastDevice wrapper object containing cast object and additional ip/port info.
    :rtype: CastDevice
    """

    devices = get_cast_devices([device_name]) if device_name else get_cast_devices()
    return devices[0] if devices else None


def get_cast_device_with_ip(device_ip: str, port: int = DEFAULT_PORT) -> Optional[CastDevice]:
    """
    Get specific device using its ip-address (and optionally port).

    :param device_ip: Ip-address of device.
    :type device_name: str
    :param port: Optional port number of device.
    :returns: CastDevice wrapper object containing cast object and additional ip/port info.
    :rtype: CastDevice
    """

    try:
        # tries = 1 is necessary in order to stop pychromecast engaging
        # in a retry behaviour when ip is correct, but port is wrong.
        cast = pychromecast.Chromecast(device_ip, port=port, tries=1)
        return CastDevice(cast, device_ip, port)
    except pychromecast.error.ChromecastConnectionError:
        return None


def cast_device_ip_exists(device_ip: str) -> bool:
    """
    Get availability of specific device using its ip-address.

    :param device_ip: Ip-address of device.
    :type device_name: str
    :returns: Availability of device.
    :rtype: bool
    """

    return bool(get_cast_device_with_ip(device_ip))


def get_cast_device(device_desc: Optional[str] = None) -> CastDevice:
    """
    Attempt to connect with requested device (or any device if none has been specified).

    :param device_desc: Can be an ip-address or a name.
    :type device_desc: str
    :returns: Chromecast object for use in a CastController.
    :rtype: pychromecast.Chromecast
    """

    cast_device = None

    if device_desc and is_ipaddress(device_desc):
        cast_device = get_cast_device_with_ip(device_desc, DEFAULT_PORT)
        if not cast_device:
            msg = "No device found at {}".format(device_desc)
            raise CastError(msg)
    else:
        cast_device = get_cast_device_with_name(device_desc)
        if not cast_device:
            msg = 'Specified device "{}" not found'.format(device_desc) if device_desc else "No devices found"
            raise CastError(msg)

    cast_device.cast.wait()
    return cast_device
