# -*- coding: utf-8 -*-
import os
import time

from threading import Thread
try:
    import ConfigParser as configparser
except:
    import configparser

import click

from .controllers import (
    Cache,
    CastController,
    get_chromecast,
    get_chromecasts
)
from .http_server import serve_file
from .stream_info import StreamInfo


CONFIG_DIR = click.get_app_dir("catt")
CONFIG_FILENAME = os.path.join(CONFIG_DIR, "catt.cfg")


class CattCliError(click.ClickException):
    pass


class CattTimeParamType(click.ParamType):
    def convert(self, value, param, ctx):
        try:
            tdesc = [int(x) for x in value.split(":")]
            tlen = len(tdesc)
            if (tlen > 1 and any(t > 59 for t in tdesc)) or tlen > 3:
                raise ValueError
        except ValueError:
            self.fail("%s is not a valid time description" % value, param, ctx)

        tdesc.reverse()
        return sum(tdesc[p] * 60 ** p for p in range(tlen))


CATT_TIME = CattTimeParamType()


def get_device(ctx, param, value):
    try:
        return ctx.default_map["aliases"][value]
    except KeyError:
        return value


@click.group()
@click.option("--delete-cache", is_flag=True,
              help="Empty the Chromecast discovery cache.")
@click.option("-d", "--device", metavar="NAME",
              callback=get_device, help="Select Chromecast device.")
@click.pass_context
def cli(ctx, delete_cache, device):
    if delete_cache:
        Cache().clear()
    ctx.obj["device"] = device


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
    cst = CastController(settings["device"], state_check=False)
    cc_name = cst.cast.device.friendly_name
    cc_type = cst.cast.cast_type
    cc_info = (cst.cast.device.manufacturer, cst.cast.model_name)
    stream = StreamInfo(video_url, model=cc_info, host=cst.cast.host)

    if stream.is_local_file:
        click.echo("Casting local file %s..." % video_url)
        click.echo("Playing %s on \"%s\"..." % (stream.video_title, cc_name))

        thr = Thread(target=serve_file,
                     args=(video_url, stream.local_ip, stream.port))

        thr.setDaemon(True)
        thr.start()
        cst.play_media(stream.video_url)
        click.echo("Serving local file, press Ctrl+C when done.")
        while thr.is_alive():
            time.sleep(1)
    # Google blocks Chromecast Audio devices from running the YouTube app.
    elif stream.is_youtube_video and cc_type != "audio":
        click.echo("Casting YouTube video %s..." % stream.video_id)
        click.echo("Playing %s on \"%s\"..." % (stream.video_title, cc_name))
        cst.play_yt_video(stream.video_id)

    elif stream.is_youtube_playlist and cc_type != "audio":
        click.echo("Casting YouTube playlist %s..." % stream.playlist_id)
        click.echo("Playing %s on \"%s\"..." % (stream.playlist_title, cc_name))
        cst.play_yt_video(stream.playlist[0])
        # When casting a playlist, we need to start playback of the first
        # video immediately, as the controller's play_video method clears
        # the queue for some reason.
        if len(stream.playlist) > 1:
            for video_id in stream.playlist[1:]:
                click.echo("Adding YouTube video %s to queue..." % video_id)
                cst.add_to_yt_queue(video_id)

    elif stream.is_playlist and (cc_type == "audio" or not stream.is_youtube_playlist):
        click.echo("Casting remote file %s..." % video_url)
        if cc_type == "audio":
            click.echo("Warning: Playlists not supported on audio devices, playing first video.",
                       err=True)
        else:
            click.echo("Warning: Only YouTube playlists are supported, playing first video.",
                       err=True)
        click.echo("Playing %s on \"%s\"..." % (stream.first_entry_title, cc_name))
        cst.play_media(stream.first_entry_url)

    else:
        click.echo("Casting remote file %s..." % video_url)
        click.echo("Playing %s on \"%s\"..." % (stream.video_title, cc_name))
        cst.play_media(stream.video_url)


@cli.command(short_help="Send a video to the YouTube Queue.")
@click.argument("video_url")
@click.pass_obj
def add(settings, video_url):
    cst = CastController(settings["device"], state_check=False)
    cc_name = cst.cast.device.friendly_name
    cc_type = cst.cast.cast_type
    stream = StreamInfo(video_url)

    if not stream.is_youtube_video:
        raise CattCliError("Not a valid YouTube video url.")
    if cc_type == "audio":
        raise CattCliError("YouTube Queue not supported on audio devices.")

    click.echo("Adding YouTube video %s to queue..." % stream.video_id)

    if (cst.cast.app_id == "233637DE" and
            cst.cast.media_controller.status.player_state != "IDLE"):
        cst.add_to_yt_queue(stream.video_id)
    else:
        click.echo("Playing %s on \"%s\"..." % (stream.video_title, cc_name))
        cst.play_yt_video(stream.video_id)


@cli.command(short_help="Pause a video.")
@click.pass_obj
def pause(settings):
    cst = CastController(settings["device"])
    cst.pause()


@cli.command(short_help="Resume a video after it has been paused.")
@click.pass_obj
def play(settings):
    cst = CastController(settings["device"])
    cst.play()


@cli.command(short_help="Stop playing.")
@click.pass_obj
def stop(settings):
    cst = CastController(settings["device"], state_check=False)
    cst.kill()


@cli.command(short_help="Rewind a video by TIME duration.")
@click.argument("timedesc", type=CATT_TIME,
                required=False, default="30", metavar="TIME")
@click.pass_obj
def rewind(settings, timedesc):
    cst = CastController(settings["device"])
    cst.rewind(timedesc)


@cli.command(short_help="Fastforward a video by TIME duration.")
@click.argument("timedesc", type=CATT_TIME,
                required=False, default="30", metavar="TIME")
@click.pass_obj
def ffwd(settings, timedesc):
    cst = CastController(settings["device"])
    cst.ffwd(timedesc)


@cli.command(short_help="Seek the video to TIME position.")
@click.argument("timedesc", type=CATT_TIME, metavar="TIME")
@click.pass_obj
def seek(settings, timedesc):
    cst = CastController(settings["device"])
    cst.seek(timedesc)


@cli.command(short_help="Skip to next video in YouTube Queue.")
@click.pass_obj
def skip(settings):
    cst = CastController(settings["device"])
    if cst.cast.app_id != "233637DE":
        raise CattCliError("YouTube Queue is currently not active.")
    cst.skip()


@cli.command(short_help="Set the volume to LVL [0-100].")
@click.argument("level", type=click.IntRange(0, 100), metavar="LVL")
@click.pass_obj
def volume(settings, level):
    cst = CastController(settings["device"], state_check=False)
    cst.volume(level / 100.0)


@cli.command(short_help="Turn up volume by a DELTA increment.")
@click.argument("delta", type=click.IntRange(1, 100),
                required=False, default=10, metavar="DELTA")
@click.pass_obj
def volumeup(settings, delta):
    cst = CastController(settings["device"], state_check=False)
    cst.volumeup(delta / 100.0)


@cli.command(short_help="Turn down volume by a DELTA increment.")
@click.argument("delta", type=click.IntRange(1, 100),
                required=False, default=10, metavar="DELTA")
@click.pass_obj
def volumedown(settings, delta):
    cst = CastController(settings["device"], state_check=False)
    cst.volumedown(delta / 100.0)


@cli.command(short_help="Show some information about the currently-playing video.")
@click.pass_obj
def status(settings):
    cst = CastController(settings["device"])
    cst.status()


@cli.command(short_help="Show complete information about the currently-playing video.")
@click.pass_obj
def info(settings):
    cst = CastController(settings["device"])
    cst.info()


@cli.command(short_help="Scan the local network and show all Chromecasts and their IPs.")
def scan():
    click.echo("Scanning Chromecasts...")
    for device in get_chromecasts():
        click.echo("{0.host} - {0.device.friendly_name} - {0.device.manufacturer} {0.device.model_name}".format(device))


def writeconfig(settings):
    try:
        os.mkdir(CONFIG_DIR)
    except:
        pass

    # Put all the standalone options from the settings into an "options" key.
    old_conf = readconfig()
    conf = {"options": settings}
    conf["aliases"] = old_conf["aliases"]

    # Convert the conf dict into a ConfigParser instance.
    config = configparser.ConfigParser()

    for section, options in conf.items():
        config.add_section(section)
        for option, value in options.items():
            config.set(section, option, value)

    with open(CONFIG_FILENAME, "w") as configfile:
        config.write(configfile)


def readconfig():
    """
    Read the configuration from the config file.

    Returns a dictionary of the form:
        {"option": "value",
         "aliases": {"device1": "device_name"}}
    """
    config = configparser.ConfigParser()
    config.read(CONFIG_FILENAME)
    conf_dict = {section: dict(config.items(section)) for section in config.sections()}

    conf = conf_dict.get("options", {})
    conf["aliases"] = conf_dict.get("aliases", {})

    return conf


def main():
    return cli(obj={}, default_map=readconfig())


if __name__ == "__main__":
    main()
