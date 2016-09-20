# -*- coding: utf-8 -*-
import click
import random
import os
import socket
import time
from threading import Thread

from .controllers import get_stream_info, CastController, Cache
from .http_server import serve_file


def get_local_ip(cc_host):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((cc_host, 0))
    return s.getsockname()[0]


@click.group()
@click.option("--delete-cache", is_flag=True, help="Empty the Chromecast "
              "discovery cache. Specify this if you're having errors connecting to "
              "the Chromecast.")
def cli(delete_cache):
    if delete_cache:
        Cache().clear()


@cli.command(short_help="Send a video to a Chromecast for playing.")
@click.argument("video_url")
def cast(video_url):
    cast = CastController()
    cc_name = cast.cast.device.friendly_name

    if "://" not in video_url:
        click.echo("Casting local file %s..." % video_url)
        if not os.path.isfile(video_url):
            click.echo("The chosen file does not exist.")
            return
        local_ip = get_local_ip(cast.cast.host)
        port = random.randrange(45000, 47000)
        stream_info = {"url": "http://%s:%s/" % (local_ip, port), "title": os.path.basename(video_url)}

        t = Thread(target=serve_file, args=(video_url, local_ip, port))
        t.setDaemon(True)
        t.start()
    else:
        t = None
        click.echo("Casting remote file %s..." % video_url)
        stream_info = get_stream_info(video_url)

    click.echo(u"Playing %s on %s..." % (stream_info["title"], cc_name))
    cast.play_media(stream_info["url"])

    if t:
        click.echo("Serving local file, press Ctrl+C when done.")
        while t.is_alive():
            time.sleep(1)


@cli.command(short_help="Pause a video.")
def pause():
    CastController().pause()


@cli.command(short_help="Resume a video after it has been paused.")
def play():
    CastController().play()


@cli.command(short_help="Stop playing.")
def stop():
    CastController().kill()


@cli.command(short_help="Rewind a video by SECS seconds.")
@click.argument("seconds", type=click.INT, required=False, default=30, metavar="SECS")
def rewind(seconds):
    CastController().rewind(seconds)


@cli.command(short_help="Fastforward a video by SECS seconds.")
@click.argument("seconds", type=click.INT, required=False, default=30, metavar="SECS")
def ffwd(seconds):
    CastController().ffwd(seconds)


@cli.command(short_help="Seek the video to SECS seconds.")
@click.argument("seconds", type=click.INT, metavar="SECS")
def seek(seconds):
    CastController().seek(seconds)


@cli.command(short_help="Set the volume to LVL [0-1].")
@click.argument("level", type=click.FLOAT, required=False, default=0.5, metavar="LVL")
def volume(level):
    CastController().volume(level)


@cli.command(short_help="Show some information about the currently-playing video.")
def status():
    CastController().status()


if __name__ == "__main__":
    cli()
