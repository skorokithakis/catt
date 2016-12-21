# -*- coding: utf-8 -*-
import click
import random
import os
import socket
import time
try:
    import ConfigParser as configparser
except:
    import configparser
from threading import Thread

from .controllers import get_stream_info, get_chromecast, CastController, Cache
from .http_server import serve_file


def get_local_ip(cc_host):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((cc_host, 0))
    return s.getsockname()[0]


class CattCliError(click.ClickException):
    pass


class CattTimeParamType(click.ParamType):
    def convert(self, value, param, ctx):
        try:
            time = [int(x) for x in value.split(':')]
            tlen = len(time)
            if (tlen > 1 and any(t > 59 for t in time)) or tlen > 3:
                raise ValueError
        except ValueError:
            self.fail('%s is not a valid time description' % value, param, ctx)
        else:
            time.reverse()
            return sum(time[p] * 60 ** p for p in range(tlen))


CATT_TIME = CattTimeParamType()


@click.group()
@click.option("--delete-cache", is_flag=True,
              help="Empty the Chromecast discovery cache.")
@click.option("-d", "--device", metavar="NAME",
              help="Select Chromecast device.")
@click.pass_context
def cli(ctx, delete_cache, device):
    if delete_cache:
        Cache().clear()
    ctx.obj["device"] = device
    if device:
        click.echo("Trying to connect to %s" % device)


@cli.command(short_help="Write the name of default Chromecast "
                        "device to config file.")
@click.pass_obj
def write_config(settings):
    if settings.get("device"):
        # This is so we fail if the specified Chromecast cannot be found.
        get_chromecast(settings["device"])
        writeconfig(settings)
    else:
        raise CattCliError("No device specified.")


@cli.command(short_help="Send a video to a Chromecast for playing.")
@click.argument("video_url")
@click.pass_obj
def cast(settings, video_url):
    cast = CastController(settings["device"])
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
@click.pass_obj
def pause(settings):
    cast = CastController(settings["device"])
    cast.pause()


@cli.command(short_help="Resume a video after it has been paused.")
@click.pass_obj
def play(settings):
    cast = CastController(settings["device"])
    cast.play()


@cli.command(short_help="Stop playing.")
@click.pass_obj
def stop(settings):
    cast = CastController(settings["device"])
    cast.kill()


@cli.command(short_help="Rewind a video by TIME duration.")
@click.argument("time", type=CATT_TIME,
                required=False, default="30", metavar="TIME")
@click.pass_obj
def rewind(settings, time):
    cast = CastController(settings["device"])
    cast.rewind(time)


@cli.command(short_help="Fastforward a video by TIME duration.")
@click.argument("time", type=CATT_TIME,
                required=False, default="30", metavar="TIME")
@click.pass_obj
def ffwd(settings, time):
    cast = CastController(settings["device"])
    cast.ffwd(time)


@cli.command(short_help="Seek the video to TIME position.")
@click.argument("time", type=CATT_TIME, metavar="TIME")
@click.pass_obj
def seek(settings, time):
    cast = CastController(settings["device"])
    cast.seek(time)


@cli.command(short_help="Set the volume to LVL [0-100].")
@click.argument("level", type=click.IntRange(0, 100), metavar="LVL")
@click.pass_obj
def volume(settings, level):
    cast = CastController(settings["device"])
    cast.volume(level / 100.0)


@cli.command(short_help="Turn up volume by an 0.1 increment.")
@click.pass_obj
def volumeup(settings):
    cast = CastController(settings["device"])
    cast.volumeup()


@cli.command(short_help="Turn down volume by an 0.1 increment.")
@click.pass_obj
def volumedown(settings):
    cast = CastController(settings["device"])
    cast.volumedown()


@cli.command(short_help="Show some information about the currently-playing video.")
@click.pass_obj
def status(settings):
    cast = CastController(settings["device"])
    cast.status()


@cli.command(short_help="Show complete information about the currently-playing video.")
@click.pass_obj
def info(settings):
    cast = CastController(settings["device"])
    cast.info()


def writeconfig(settings):
    config_dir = click.get_app_dir("catt")
    try:
        os.mkdir(config_dir)
    except:
        pass

    config_filename = os.path.join(config_dir, "catt.cfg")
    config = configparser.ConfigParser()

    for key, value in settings.items():
        config.set("DEFAULT", key, value)

    with open(config_filename, 'w') as configfile:
        config.write(configfile)


def readconfig():
    config_filename = os.path.join(click.get_app_dir("catt"), "catt.cfg")

    config = configparser.RawConfigParser()
    config.read(config_filename)
    return dict(config.defaults())


def main():
    return cli(obj={}, default_map=readconfig())


if __name__ == "__main__":
    main()
