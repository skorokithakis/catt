# -*- coding: utf-8 -*-
import configparser
import time
from pathlib import Path
from threading import Thread

import click

from .controllers import (
    Cache,
    get_chromecast,
    get_chromecasts,
    PlaybackError,
    setup_cast
)
from .http_server import serve_file


CONFIG_DIR = Path(click.get_app_dir("catt"))
CONFIG_FILE = Path(CONFIG_DIR, "catt.cfg")


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


def process_url(ctx, param, value):
    if value.strip() == "-":
        stdin_text = click.get_text_stream('stdin')
        if not stdin_text.isatty():
            value = stdin_text.read().strip()
        else:
            raise CattCliError("No input received from stdin.")
    if "://" not in value:
        if ctx.info_name != "cast":
            raise CattCliError("Local file not allowed as argument to this command.")
        if not Path(value).exists():
            raise CattCliError("The chosen file does not exist.")
    return value


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
@click.argument("video_url", callback=process_url)
@click.option("-f", "--force-default", is_flag=True,
              help="Force use of the default Chromecast app (use if a custom app doesn't work).")
@click.pass_obj
def cast(settings, video_url, force_default):
    cst, stream = setup_cast(settings["device"], video_url=video_url,
                             prep="app", force_default=force_default)

    if stream.is_local_file:
        click.echo("Casting local file %s..." % video_url)
        click.echo("Playing %s on \"%s\"..." % (stream.video_title, cst.cc_name))

        thr = Thread(target=serve_file,
                     args=(video_url, stream.local_ip, stream.port))

        thr.setDaemon(True)
        thr.start()
        cst.play_media_url(stream.video_url, title=stream.video_title)
        click.echo("Serving local file, press Ctrl+C when done.")
        while thr.is_alive():
            time.sleep(1)

    elif stream.is_playlist:
        if not stream.playlist:
            cst.kill()
            raise CattCliError("Playlist is empty.")
        click.echo("Casting remote file %s..." % video_url)
        click.echo("Playing %s on \"%s\"..." % (stream.playlist_title, cst.cc_name))
        try:
            cst.play_playlist(stream.playlist)
        except PlaybackError:
            click.echo("Warning: Playlist playback not possible, playing first video.", err=True)
            if cst.info_type == "url":
                cst.play_media_url(stream.first_entry_url, title=stream.first_entry_title,
                                   thumb=stream.first_entry_thumbnail)
            elif cst.info_type == "id":
                cst.play_media_id(stream.first_entry_id)

    else:
        click.echo("Casting remote file %s..." % video_url)
        click.echo("Playing %s on \"%s\"..." % (stream.video_title, cst.cc_name))
        if cst.info_type == "url":
            cst.play_media_url(stream.video_url, title=stream.video_title,
                               thumb=stream.video_thumbnail)
        elif cst.info_type == "id":
            cst.play_media_id(stream.video_id)


@cli.command(short_help="Add a video to the queue.")
@click.argument("video_url", callback=process_url)
@click.pass_obj
def add(settings, video_url):
    cst, stream = setup_cast(settings["device"], video_url=video_url, prep="control")
    if (cst.name != "default" and cst.name != stream.extractor) or not stream.is_video:
        raise CattCliError("This url cannot be added to the queue.")
    cst.add(stream.video_id)


@cli.command(short_help="Pause a video.")
@click.pass_obj
def pause(settings):
    cst = setup_cast(settings["device"], prep="control")
    cst.pause()


@cli.command(short_help="Resume a video after it has been paused.")
@click.pass_obj
def play(settings):
    cst = setup_cast(settings["device"], prep="control")
    cst.play()


@cli.command(short_help="Stop playing.")
@click.pass_obj
def stop(settings):
    cst = setup_cast(settings["device"])
    cst.kill()


@cli.command(short_help="Rewind a video by TIME duration.")
@click.argument("timedesc", type=CATT_TIME,
                required=False, default="30", metavar="TIME")
@click.pass_obj
def rewind(settings, timedesc):
    cst = setup_cast(settings["device"], prep="control")
    cst.rewind(timedesc)


@cli.command(short_help="Fastforward a video by TIME duration.")
@click.argument("timedesc", type=CATT_TIME,
                required=False, default="30", metavar="TIME")
@click.pass_obj
def ffwd(settings, timedesc):
    cst = setup_cast(settings["device"], prep="control")
    cst.ffwd(timedesc)


@cli.command(short_help="Seek the video to TIME position.")
@click.argument("timedesc", type=CATT_TIME, metavar="TIME")
@click.pass_obj
def seek(settings, timedesc):
    cst = setup_cast(settings["device"], prep="control")
    cst.seek(timedesc)


@cli.command(short_help="Skip to next video in queue (if any).")
@click.pass_obj
def skip(settings):
    cst = setup_cast(settings["device"], prep="control")
    cst.skip()


@cli.command(short_help="Set the volume to LVL [0-100].")
@click.argument("level", type=click.IntRange(0, 100), metavar="LVL")
@click.pass_obj
def volume(settings, level):
    cst = setup_cast(settings["device"])
    cst.volume(level / 100.0)


@cli.command(short_help="Turn up volume by a DELTA increment.")
@click.argument("delta", type=click.IntRange(1, 100),
                required=False, default=10, metavar="DELTA")
@click.pass_obj
def volumeup(settings, delta):
    cst = setup_cast(settings["device"])
    cst.volumeup(delta / 100.0)


@cli.command(short_help="Turn down volume by a DELTA increment.")
@click.argument("delta", type=click.IntRange(1, 100),
                required=False, default=10, metavar="DELTA")
@click.pass_obj
def volumedown(settings, delta):
    cst = setup_cast(settings["device"])
    cst.volumedown(delta / 100.0)


@cli.command(short_help="Show some information about the currently-playing video.")
@click.pass_obj
def status(settings):
    cst = setup_cast(settings["device"], prep="control")
    cst.status()


@cli.command(short_help="Show complete information about the currently-playing video.")
@click.pass_obj
def info(settings):
    cst = setup_cast(settings["device"], prep="control")
    cst.info()


@cli.command(short_help="Scan the local network and show all Chromecasts and their IPs.")
def scan():
    click.echo("Scanning Chromecasts...")
    for device in get_chromecasts():
        click.echo("{0.host} - {0.device.friendly_name} - {0.device.manufacturer} {0.device.model_name}".format(device))


def writeconfig(settings):
    try:
        CONFIG_DIR.mkdir()
    except FileExistsError:
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

    with CONFIG_FILE.open("w") as configfile:
        config.write(configfile)


def readconfig():
    """
    Read the configuration from the config file.

    Returns a dictionary of the form:
        {"option": "value",
         "aliases": {"device1": "device_name"}}
    """
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    conf_dict = {section: dict(config.items(section)) for section in config.sections()}

    conf = conf_dict.get("options", {})
    conf["aliases"] = conf_dict.get("aliases", {})

    return conf


def main():
    return cli(obj={}, default_map=readconfig())


if __name__ == "__main__":
    main()
