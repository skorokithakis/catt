import ipaddress
import re
import tempfile
import time
from pathlib import Path

import click
import ifaddr


class CattUtilError(click.ClickException):
    pass


def warning(msg):
    click.secho("Warning: ", fg="red", nl=False, err=True)
    click.echo(msg, err=True)


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


def hunt_subtitle(video):
    """Searches for subtitles in the current folder"""

    video_path = Path(video)
    video_path_stem_lower = video_path.stem.lower()
    for entry_path in video_path.parent.iterdir():
        if entry_path.is_dir():
            continue
        if entry_path.stem.lower().startswith(video_path_stem_lower) and entry_path.suffix.lower() in [".vtt", ".srt"]:
            return str(entry_path.resolve())
    return None


def convert_srt_to_webvtt_helper(content):
    content = re.sub(r"^(.*? \-\-\> .*?)$", lambda m: m.group(1).replace(",", "."), content, flags=re.MULTILINE)

    with tempfile.NamedTemporaryFile(mode="w+b", suffix=".vtt", delete=False) as vttfile:
        target_filename = vttfile.name
        vttfile.write("WEBVTT\n\n".encode())
        vttfile.write(content.encode())
        return target_filename


def convert_srt_to_webvtt(filename):
    for possible_encoding in ["utf-8", "iso-8859-15"]:
        try:
            with open(filename, "r", encoding=possible_encoding) as srtfile:
                content = srtfile.read()
                return convert_srt_to_webvtt_helper(content)
        except UnicodeDecodeError:
            pass
    raise CattUtilError("Could not find the proper encoding of {}. Please convert it to utf-8.".format(filename))


def human_time(seconds: int):
    return time.strftime("%H:%M:%S", time.gmtime(seconds))


def get_local_ip(host):
    for adapter in ifaddr.get_adapters():
        for adapter_ip in adapter.ips:
            aip = adapter_ip.ip[0] if isinstance(adapter_ip.ip, tuple) else adapter_ip.ip
            try:
                if not isinstance(ipaddress.ip_address(host), type(ipaddress.ip_address(aip))):
                    raise ValueError
            except ValueError:
                continue
            ipt = [(ip, adapter_ip.network_prefix) for ip in (aip, host)]
            catt_net, cc_net = [ipaddress.ip_network("%s/%s" % ip, strict=False) for ip in ipt]
            if catt_net == cc_net:
                return aip
            else:
                continue
