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


class Device(object):
    def __init__(self, name):
        self.name = name


pass_device = click.make_pass_decorator(Device)


@click.group()
@click.option("--delete-cache", is_flag=True, help="Empty the Chromecast discovery cache.")
@click.option("-d", "--device", metavar="NAME", help="Select Chromecast device.")
@click.pass_context
def cli(ctx, delete_cache, device):
    if delete_cache:
        Cache().clear()
    ctx.obj = Device(device)


@cli.command(short_help="Send a video to a Chromecast for playing.")
@click.argument("video_url")
@pass_device
def cast(device, video_url):
    cast = CastController(device.name)
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
@pass_device
def pause(device):
    cast = CastController(device.name)
    cast.pause()


@cli.command(short_help="Resume a video after it has been paused.")
@pass_device
def play(device):
    cast = CastController(device.name)
    cast.play()


@cli.command(short_help="Stop playing.")
@pass_device
def stop(device):
    cast = CastController(device.name)
    cast.kill()


@cli.command(short_help="Rewind a video by SECS seconds.")
@click.argument("seconds", type=click.INT, required=False, default=30, metavar="SECS")
@pass_device
def rewind(device, seconds):
    cast = CastController(device.name)
    cast.rewind(seconds)


@cli.command(short_help="Fastforward a video by SECS seconds.")
@click.argument("seconds", type=click.INT, required=False, default=30, metavar="SECS")
@pass_device
def ffwd(device, seconds):
    cast = CastController(device.name)
    cast.ffwd(seconds)


@cli.command(short_help="Seek the video to SECS seconds.")
@click.argument("seconds", type=click.INT, metavar="SECS")
@pass_device
def seek(device, seconds):
    cast = CastController(device.name)
    cast.seek(seconds)


@cli.command(short_help="Set the volume to LVL [0-1].")
@click.argument("level", type=click.FLOAT, required=False, default=0.5, metavar="LVL")
@pass_device
def volume(device, level):
    cast = CastController(device.name)
    cast.volume(level)


@cli.command(short_help="Turn up volume by an 0.1 increment.")
@pass_device
def volumeup(device):
    cast = CastController(device.name)
    cast.volumeup()


@cli.command(short_help="Turn down volume by an 0.1 increment.")
@pass_device
def volumedown(device):
    cast = CastController(device.name)
    cast.volumedown()


@cli.command(short_help="Show some information about the currently-playing video.")
@pass_device
def status(device):
    cast = CastController(device.name)
    cast.status()


@cli.command(short_help="Show complete information about the currently-playing video.")
@pass_device
def info(device):
    cast = CastController(device.name)
    cast.info()


if __name__ == "__main__":
    cli()
