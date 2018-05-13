from pathlib import Path

import click


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
