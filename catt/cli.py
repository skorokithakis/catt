# -*- coding: utf-8 -*-

import configparser
import random
import re
import tempfile
import time
from pathlib import Path
from threading import Thread

import click
import requests

from .controllers import (
    Cache,
    CastState,
    get_chromecast,
    get_chromecasts,
    PlaybackError,
    setup_cast,
    StateFileError
)
from .http_server import serve_file
from .util import warning


CONFIG_DIR = Path(click.get_app_dir("catt"))
CONFIG_PATH = Path(CONFIG_DIR, "catt.cfg")
STATE_PATH = Path(CONFIG_DIR, "state.json")


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


def human_time(seconds):
    return time.strftime("%H:%M:%S", time.gmtime(seconds))


def process_url(ctx, param, value):
    if value == "-":
        stdin_text = click.get_text_stream("stdin")
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


def process_path(ctx, param, value):
    path = Path(value) if value else None
    if path and (path.is_dir() or not path.parent.exists()):
        raise CattCliError("The specified path is invalid.")
    return path


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


def hunt_subtitle(video):
    """"Searches for subtitles in the current folder"""
    video_path = Path(video)
    video_path_stem_lower = video_path.stem.lower()
    for entry_path in video_path.parent.iterdir():
        if entry_path.is_dir():
            continue
        if entry_path.stem.lower().startswith(video_path_stem_lower) and \
                entry_path.suffix.lower() in [".vtt", ".srt"]:
            return str(entry_path.resolve())
    return None


def convert_srt_to_webvtt_helper(content):
    content = re.sub(r"^(.*? \-\-\> .*?)$", lambda m: m.group(1).replace(",", "."), content, flags=re.MULTILINE)

    with tempfile.NamedTemporaryFile(mode='w+b',
                                     suffix=".vtt",
                                     delete=False) as vttfile:
        target_filename = vttfile.name
        vttfile.write("WEBVTT\n\n".encode())
        vttfile.write(content.encode())
        return target_filename


def convert_srt_to_webvtt(filename):
    for possible_encoding in ['utf-8', 'iso-8859-15']:
        try:
            with open(filename, 'r', encoding=possible_encoding) as srtfile:
                content = srtfile.read()
                return convert_srt_to_webvtt_helper(content)
        except UnicodeDecodeError:
            pass
    raise CattCliError("Could not find the proper encoding of {}. Please convert it to utf-8".format(filename))


def load_subtitle_if_exists(subtitle, video, local_ip, port):
    subtitle = subtitle if subtitle else hunt_subtitle(video)
    if subtitle is None:
        return None
    click.echo("Using subtitle {}".format(subtitle))

    if "://" in subtitle:
        # it's an URL
        if subtitle.lower().endswith(".srt"):
            content = requests.get(subtitle).text
            subtitle = convert_srt_to_webvtt_helper(content)
        else:
            return subtitle

    if subtitle.lower().endswith(".srt"):
        subtitle = convert_srt_to_webvtt(subtitle)

    thr = Thread(target=serve_file,
                 args=(subtitle, local_ip, port, "text/vtt;charset=utf-8"))
    thr.setDaemon(True)
    thr.start()
    subtitle_url = "http://{}:{}/{}".format(local_ip, port, subtitle)
    return subtitle_url


def process_subtitle(ctx, param, value):
    if value is None:
        return None
    if "://" in value:
        return value
    if not Path(value).is_file():
        raise CattCliError("Subtitle file [{}] does not exist".format(value))
    return value


@cli.command(short_help="Send a video to a Chromecast for playing.")
@click.argument("video_url", callback=process_url)
@click.option("-s", "--subtitle",
              callback=process_subtitle, help="Specify a Subtitle")
@click.option("-f", "--force-default", is_flag=True,
              help="Force use of the default Chromecast app (use if a custom app doesn't work).")
@click.option("-r", "--random-play", is_flag=True,
              help="Play random item from playlist, if applicable.")
@click.option("--no-subs", is_flag=True, default=False,
              help="Don't try to load subtitles automatically from the local folder.")
@click.pass_obj
def cast(settings, video_url, subtitle, force_default, random_play, no_subs):
    controller = "default" if force_default else None
    cst, stream = setup_cast(settings["device"], video_url=video_url,
                             prep="app", controller=controller)

    if stream.is_local_file:
        click.echo("Casting local file %s..." % video_url)
        click.echo("Playing %s on \"%s\"..." % (stream.video_title, cst.cc_name))
        if subtitle is None and no_subs:
            subtitle_url = None
        else:
            subtitle_url = load_subtitle_if_exists(subtitle, video_url, stream.local_ip, stream.port + 1)

        thr = Thread(target=serve_file,
                     args=(video_url, stream.local_ip, stream.port, stream.guessed_content_type))

        thr.setDaemon(True)
        thr.start()
        cst.play_media_url(stream.video_url, content_type=stream.guessed_content_type,
                           title=stream.video_title, subtitles=subtitle_url)
        click.echo("Serving local file, press Ctrl+C when done.")
        while thr.is_alive():
            time.sleep(1)

    elif stream.is_playlist:
        if stream.playlist_length == 0:
            cst.kill(idle_only=True)
            raise CattCliError("Playlist is empty.")
        click.echo("Casting remote playlist %s..." % video_url)
        if random_play:
            stream.set_playlist_entry(random.randrange(0, stream.playlist_length))
        else:
            try:
                if not stream.playlist_all_ids:
                    raise ValueError
                cst.play_playlist(stream.playlist_all_ids)
                return
            except (PlaybackError, ValueError):
                warning("Playlist playback not possible, playing first video.")
                stream.set_playlist_entry(0)
        click.echo("Playing %s on \"%s\"..." % (stream.playlist_entry_title, cst.cc_name))
        if cst.info_type == "url":
            cst.play_media_url(stream.playlist_entry_url,
                               title=stream.playlist_entry_title,
                               thumb=stream.playlist_entry_thumbnail,
                               content_type=stream.guessed_content_type)
        elif cst.info_type == "id":
            cst.play_media_id(stream.playlist_entry_id)

    else:
        click.echo("Casting remote file %s..." % video_url)
        click.echo("Playing %s on \"%s\"..." % (stream.video_title, cst.cc_name))
        if cst.info_type == "url":
            cst.play_media_url(stream.video_url, title=stream.video_title,
                               thumb=stream.video_thumbnail,
                               content_type=stream.guessed_content_type)
        elif cst.info_type == "id":
            cst.play_media_id(stream.video_id)


@cli.command(short_help="Cast any webpage to a Chromecast.")
@click.argument("url")
@click.pass_obj
def cast_site(settings, url):
    cst = setup_cast(settings["device"], prep="app", controller="dashcast")
    click.echo("Casting %s on \"%s\"..." % (url, cst.cc_name))
    cst.load_url(url)


@cli.command(short_help="Add a video to the queue.")
@click.argument("video_url", callback=process_url)
@click.pass_obj
def add(settings, video_url):
    cst, stream = setup_cast(settings["device"], video_url=video_url, prep="control")
    if (cst.name != "default" and cst.name != stream.extractor) or not stream.is_remote_file:
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
    print_status(cst.cast_info)


@cli.command(short_help="Show complete information about the currently-playing video.")
@click.pass_obj
def info(settings):
    cst = setup_cast(settings["device"], prep="control")
    for (key, value) in cst.info.items():
        click.echo("%s: %s" % (key, value))


@cli.command(short_help="Scan the local network and show all Chromecasts and their IPs.")
def scan():
    click.echo("Scanning Chromecasts...")
    for device in get_chromecasts():
        click.echo("{0.host} - {0.device.friendly_name} - {0.device.manufacturer} {0.device.model_name}".format(device))


@cli.command(short_help="Save the current state of the Chromecast for later use.")
@click.argument("path",
                type=click.Path(writable=True), callback=process_path, required=False)
@click.pass_obj
def save(settings, path):
    cst = setup_cast(settings["device"], prep="control")
    if not cst.save_capability or cst.is_streaming_local_file:
        raise CattCliError("Saving state of this kind of content is not supported.")
    elif cst.save_capability == "partial":
        warning("Please be advised that playlist data will not be saved.")

    print_status(cst.media_info)
    if path and path.exists():
        click.confirm("File already exists. Overwrite?", abort=True)
    click.echo("Saving...")
    state = CastState(path or STATE_PATH, create_dir=True if not path else False)
    state.set_data(cst.cc_name, {"controller": cst.name, "data": cst.media_info})


@cli.command(short_help="Return Chromecast to saved state.")
@click.argument("path",
                type=click.Path(exists=True), callback=process_path, required=False)
@click.pass_obj
def restore(settings, path):
    cst = setup_cast(settings["device"])
    state = CastState(path or STATE_PATH)
    try:
        data = state.get_data(cst.cc_name)
    except StateFileError:
        raise CattCliError("The chosen file is not a valid save file.")
    if not data:
        raise CattCliError("No save data found for this device.")

    print_status(data["data"])
    click.echo("Restoring...")
    cst = setup_cast(settings["device"], prep="app", controller=data["controller"])
    cst.restore(data["data"])


def print_status(status):
    if status.get("title"):
        click.echo("Title: %s" % status["title"])

    if status.get("current_time"):
        current = human_time(status["current_time"])
        if status.get("duration"):
            duration = human_time(status["duration"])
            remaining = human_time(status["remaining"])
            click.echo("Time: %s / %s (%s%%)" % (current, duration, status["progress"]))
            click.echo("Remaining time: %s" % remaining)
        else:
            click.echo("Time: %s" % current)

    if status.get("player_state"):
        click.echo("State: %s" % status["player_state"])

    if status.get("volume_level"):
        click.echo("Volume: %s" % status["volume_level"])


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

    with CONFIG_PATH.open("w") as configfile:
        config.write(configfile)


def readconfig():
    """
    Read the configuration from the config file.

    Returns a dictionary of the form:
        {"option": "value",
         "aliases": {"device1": "device_name"}}
    """
    config = configparser.ConfigParser()
    # ConfigParser.read does not take path-like objects <3.6.
    config.read(str(CONFIG_PATH))
    conf_dict = {section: dict(config.items(section)) for section in config.sections()}

    conf = conf_dict.get("options", {})
    conf["aliases"] = conf_dict.get("aliases", {})

    return conf


def main():
    return cli(obj={}, default_map=readconfig())


if __name__ == "__main__":
    main()
