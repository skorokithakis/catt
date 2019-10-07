import ipaddress
import json
import sys
import tempfile
import time
from pathlib import Path

import click

try:
    import netifaces
except ImportError:
    import ifaddr


def warning(msg):
    click.secho("Warning: ", fg="red", nl=False, err=True)
    click.echo("{}.".format(msg), err=True)


def echo_json(data_dict):
    click.echo(json.dumps(data_dict, indent=4, default=str))


def guess_mime(path):
    # source: https://developers.google.com/cast/docs/media
    extension = Path(path).suffix.lower()
    extensions = {
        ".mp4": "video/mp4",
        ".m4a": "audio/mp4",
        ".mp3": "audio/mp3",
        ".mpa": "audio/mpeg",
        ".webm": "video/webm",
        ".mkv": "video/x-matroska",
        ".bmp": "image/bmp",
        ".jpg": "image/jpeg",
        ".gif": "image/gif",
        ".png": "image/png",
        ".webp": "image/web",
    }
    return extensions.get(extension, "video/mp4")


def hunt_subtitles(video):
    """Searches for subtitles in the current folder"""

    video_path = Path(video)
    video_path_stem_lower = video_path.stem.lower()
    for entry_path in video_path.parent.iterdir():
        if entry_path.is_dir():
            continue
        if entry_path.stem.lower().startswith(video_path_stem_lower) and entry_path.suffix.lower() in [".vtt", ".srt"]:
            return str(entry_path.resolve())
    return None


def create_temp_file(content):
    with tempfile.NamedTemporaryFile(mode="w+b", suffix=".vtt", delete=False) as tfile:
        tfile.write(content.encode())
        return tfile.name


def human_time(seconds: int):
    return time.strftime("%H:%M:%S", time.gmtime(seconds))


def get_local_ip(host):
    if "netifaces" in sys.modules:
        interface = netifaces.gateways()["default"][netifaces.AF_INET][1]
        return netifaces.ifaddresses(interface)[netifaces.AF_INET][0]["addr"]
    else:
        for adapter in ifaddr.get_adapters():
            for adapter_ip in adapter.ips:
                aip = adapter_ip.ip[0] if isinstance(adapter_ip.ip, tuple) else adapter_ip.ip
                try:
                    if not isinstance(ipaddress.ip_address(host), type(ipaddress.ip_address(aip))):
                        continue
                except ValueError:
                    continue
                ipt = [(ip, adapter_ip.network_prefix) for ip in (aip, host)]
                catt_net, cc_net = [ipaddress.ip_network("{0}/{1}".format(*ip), strict=False) for ip in ipt]
                if catt_net == cc_net:
                    return aip
                else:
                    continue
        raise ValueError("No adapters found")


def is_ipaddress(device):
    try:
        ipaddress.ip_address(device)
    except ValueError:
        return False
    else:
        return True
