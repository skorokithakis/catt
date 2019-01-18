# -*- coding: utf-8 -*-

import configparser
import json
import random
import time
from pathlib import Path
from threading import Thread

import click
import requests

from .controllers import Cache, CastState, StateFileError, StateMode, get_chromecast, get_chromecasts, setup_cast
from .http_server import serve_file
from .util import convert_srt_to_webvtt, convert_srt_to_webvtt_helper, human_time, hunt_subtitle, warning

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
            self.fail("%s is not a valid time description." % value, param, ctx)

        tdesc.reverse()
        return sum(tdesc[p] * 60 ** p for p in range(tlen))


CATT_TIME = CattTimeParamType()


class YtdlOptParamType(click.ParamType):
    def convert(self, value, param, ctx):
        if "=" not in value:
            self.fail("%s is not a valid key/value pair." % value, param, ctx)

        ykey, yval = value.split("=", 1)
        yval = {"true": True, "false": False}.get(yval.lower().strip(), yval)
        return (ykey, yval)


YTDL_OPT = YtdlOptParamType()


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
        if not Path(value).is_file():
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
@click.option("--delete-cache", is_flag=True, help="Empty the Chromecast discovery cache.")
@click.option("-d", "--device", metavar="NAME", callback=get_device, help="Select Chromecast device.")
@click.pass_context
def cli(ctx, delete_cache, device):
    if delete_cache:
        Cache().clear()
    ctx.obj["device"] = device


@cli.command("write_config", short_help="Write the name of default Chromecast device to config file.")
@click.pass_obj
def write_config(settings):
    if settings.get("device"):
        # This is so we fail if the specified Chromecast cannot be found.
        get_chromecast(settings["device"])
        writeconfig(settings)
    else:
        raise CattCliError("No device specified.")


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

    thr = Thread(target=serve_file, args=(subtitle, local_ip, port, "text/vtt;charset=utf-8"))
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
        raise CattCliError("Subtitle file [{}] does not exist.".format(value))
    return value


@cli.command(short_help="Send a video to a Chromecast for playing.")
@click.argument("video_url", callback=process_url)
@click.option("-s", "--subtitle", callback=process_subtitle, metavar="SUB", help="Specify a subtitle.")
@click.option(
    "-f",
    "--force-default",
    is_flag=True,
    help="Force use of the default Chromecast app (use if a custom app doesn't work).",
)
@click.option("-r", "--random-play", is_flag=True, help="Play random item from playlist, if applicable.")
@click.option(
    "--no-subs", is_flag=True, default=False, help="Don't try to load subtitles automatically from the local folder."
)
@click.option("-n", "--no-playlist", is_flag=True, help="Play only video, if url contains both video and playlist ids.")
@click.option(
    "-y",
    "--ytdl-option",
    type=YTDL_OPT,
    multiple=True,
    metavar="OPT",
    help="YouTube-DL option. "
    "Should be passed as `-y option=value`, and can be specified multiple times (implies --force-default).",
)
@click.pass_obj
def cast(settings, video_url, subtitle, force_default, random_play, no_subs, no_playlist, ytdl_option):
    controller = "default" if force_default or ytdl_option else None
    subtitle_url = None
    playlist_playback = False
    cst, stream = setup_cast(
        settings["device"], video_url=video_url, prep="app", controller=controller, ytdl_options=ytdl_option
    )

    if stream.is_local_file:
        if subtitle or not no_subs:
            subtitle_url = load_subtitle_if_exists(subtitle, video_url, stream.local_ip, stream.port + 1)
        thr = Thread(target=serve_file, args=(video_url, stream.local_ip, stream.port, stream.guessed_content_type))
        thr.setDaemon(True)
        thr.start()
    elif stream.is_playlist and not (no_playlist and stream.video_id):
        if stream.playlist_length == 0:
            cst.kill(idle_only=True)
            raise CattCliError("Playlist is empty.")
        if not random_play and cst.playlist_capability and stream.playlist_all_ids:
            playlist_playback = True
        else:
            if random_play:
                entry = random.randrange(0, stream.playlist_length)
            else:
                warning("Playlist playback not possible, playing first video.")
                entry = 0
            stream.set_playlist_entry(entry)

    if playlist_playback:
        click.echo("Casting remote playlist %s..." % video_url)
        video_id = stream.video_id or stream.playlist_all_ids[0]
        cst.play_playlist(stream.playlist_id, video_id=video_id)
    else:
        click.echo("Casting %s file %s..." % ("local" if stream.is_local_file else "remote", video_url))
        click.echo('Playing "%s" on "%s"...' % (stream.video_title, cst.cc_name))
        if cst.info_type == "url":
            cst.play_media_url(
                stream.video_url,
                title=stream.video_title,
                content_type=stream.guessed_content_type,
                subtitles=subtitle_url,
                thumb=stream.video_thumbnail,
            )
        elif cst.info_type == "id":
            cst.play_media_id(stream.video_id)
        else:
            raise ValueError("invalid or undefined info type")
        if stream.is_local_file:
            click.echo("Serving local file, press Ctrl+C when done.")
            while thr.is_alive():
                time.sleep(1)


@cli.command("cast_site", short_help="Cast any website to a Chromecast.")
@click.argument("url", callback=process_url)
@click.pass_obj
def cast_site(settings, url):
    cst = setup_cast(settings["device"], controller="dashcast", action="load_url", prep="app")
    click.echo('Casting %s on "%s"...' % (url, cst.cc_name))
    cst.load_url(url)


@cli.command(short_help="Add a video to the queue.")
@click.argument("video_url", callback=process_url)
@click.option("-n", "--play-next", is_flag=True, help="Add video immediately after currently playing video.")
@click.pass_obj
def add(settings, video_url, play_next):
    cst, stream = setup_cast(settings["device"], video_url=video_url, action="add", prep="control")
    if cst.name != stream.extractor or not (stream.is_remote_file or stream.is_playlist_with_active_entry):
        raise CattCliError("This url cannot be added to the queue.")
    click.echo('Adding video id "%s" to the queue.' % stream.video_id)
    if play_next:
        cst.add_next(stream.video_id)
    else:
        cst.add(stream.video_id)


@cli.command(short_help="Remove a video from the queue.")
@click.argument("video_url", callback=process_url)
@click.pass_obj
def remove(settings, video_url):
    cst, stream = setup_cast(settings["device"], video_url=video_url, prep="control")
    if cst.name != stream.extractor or not stream.is_remote_file:
        raise CattCliError("This url cannot be removed from the queue.")
    click.echo('Removing video id "%s" from the queue.' % stream.video_id)
    cst.remove(stream.video_id)


@cli.command(short_help="Clear the queue.")
@click.pass_obj
def clear(settings):
    cst = setup_cast(settings["device"])
    cst.clear()


@cli.command(short_help="Pause a video.")
@click.pass_obj
def pause(settings):
    cst = setup_cast(settings["device"], action="pause", prep="control")
    cst.pause()


@cli.command(short_help="Resume a video after it has been paused.")
@click.pass_obj
def play(settings):
    cst = setup_cast(settings["device"], action="play", prep="control")
    cst.play()


@cli.command(short_help="Stop playing.")
@click.pass_obj
def stop(settings):
    cst = setup_cast(settings["device"])
    cst.kill()


@cli.command(short_help="Rewind a video by TIME duration.")
@click.argument("timedesc", type=CATT_TIME, required=False, default="30", metavar="TIME")
@click.pass_obj
def rewind(settings, timedesc):
    cst = setup_cast(settings["device"], action="rewind", prep="control")
    cst.rewind(timedesc)


@cli.command(short_help="Fastforward a video by TIME duration.")
@click.argument("timedesc", type=CATT_TIME, required=False, default="30", metavar="TIME")
@click.pass_obj
def ffwd(settings, timedesc):
    cst = setup_cast(settings["device"], action="ffwd", prep="control")
    cst.ffwd(timedesc)


@cli.command(short_help="Seek the video to TIME position.")
@click.argument("timedesc", type=CATT_TIME, metavar="TIME")
@click.pass_obj
def seek(settings, timedesc):
    cst = setup_cast(settings["device"], action="seek", prep="control")
    cst.seek(timedesc)


@cli.command(short_help="Skip to end of content.")
@click.pass_obj
def skip(settings):
    cst = setup_cast(settings["device"], action="skip", prep="control")
    cst.skip()


@cli.command(short_help="Set the volume to LVL [0-100].")
@click.argument("level", type=click.IntRange(0, 100), metavar="LVL")
@click.pass_obj
def volume(settings, level):
    cst = setup_cast(settings["device"])
    cst.volume(level / 100.0)


@cli.command(short_help="Turn up volume by a DELTA increment.")
@click.argument("delta", type=click.IntRange(1, 100), required=False, default=10, metavar="DELTA")
@click.pass_obj
def volumeup(settings, delta):
    cst = setup_cast(settings["device"])
    cst.volumeup(delta / 100.0)


@cli.command(short_help="Turn down volume by a DELTA increment.")
@click.argument("delta", type=click.IntRange(1, 100), required=False, default=10, metavar="DELTA")
@click.pass_obj
def volumedown(settings, delta):
    cst = setup_cast(settings["device"])
    cst.volumedown(delta / 100.0)


@cli.command(short_help="Show some information about the currently-playing video.")
@click.pass_obj
def status(settings):
    cst = setup_cast(settings["device"], prep="info")
    print_status(cst.cast_info)


@cli.command(short_help="Show complete information about the currently-playing video.")
@click.option("-j", "--json-output", is_flag=True, help="Output info as json.")
@click.pass_obj
def info(settings, json_output):
    cst = setup_cast(settings["device"], prep="info")
    if json_output:
        click.echo(json.dumps(cst.info, indent=4, default=str))
    else:
        for (key, value) in cst.info.items():
            click.echo("%s: %s" % (key, value))


@cli.command(short_help="Scan the local network and show all Chromecasts and their IPs.")
def scan():
    click.echo("Scanning Chromecasts...")
    devices = get_chromecasts()
    if not devices:
        raise CattCliError("No devices found.")
    for device in devices:
        click.echo("{0.host} - {0.device.friendly_name} - {0.device.manufacturer} {0.device.model_name}".format(device))


@cli.command(short_help="Save the current state of the Chromecast for later use.")
@click.argument("path", type=click.Path(writable=True), callback=process_path, required=False)
@click.pass_obj
def save(settings, path):
    cst = setup_cast(settings["device"], prep="control")
    if not cst.save_capability or cst.is_streaming_local_file:
        raise CattCliError("Saving state of this kind of content is not supported.")
    elif cst.save_capability == "partial":
        warning("Please be advised that playlist data will not be saved.")

    print_status(cst.media_info)
    if path and path.is_file():
        click.confirm("File already exists. Overwrite?", abort=True)
    click.echo("Saving...")
    if path:
        state = CastState(path, StateMode.ARBI)
        cc_name = "*"
    else:
        state = CastState(STATE_PATH, StateMode.CONF)
        cc_name = cst.cc_name
    state.set_data(cc_name, {"controller": cst.name, "data": cst.media_info})


@cli.command(short_help="Return Chromecast to saved state.")
@click.argument("path", type=click.Path(exists=True), callback=process_path, required=False)
@click.pass_obj
def restore(settings, path):
    if not path and not STATE_PATH.is_file():
        raise CattCliError("Save file in config dir has not been created.")
    cst = setup_cast(settings["device"])
    state = CastState(path or STATE_PATH, StateMode.READ)
    try:
        data = state.get_data(cst.cc_name if not path else None)
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
