import re
import tempfile
from pathlib import Path

import click


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

    video_dir_path = Path(video).parent
    for ext in ["vtt", "VTT", "srt", "SRT"]:
        try:
            sub = next(video_dir_path.glob("*." + ext))
        except StopIteration:
            continue
        return str(sub.resolve())
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
