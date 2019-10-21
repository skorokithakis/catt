# -*- coding: utf-8 -*-

import configparser
import random
import sys
import time
from pathlib import Path
from threading import Thread
from urllib.parse import urlparse

import click

from . import __version__
from .controllers import Cache, CastState, StateFileError, StateMode, get_chromecast, get_chromecasts, setup_cast
from .error import CastError, CattUserError, CliError
from .http_server import serve_file
from .subs_info import SubsInfo
from .util import echo_json, human_time, hunt_subtitles, is_ipaddress, warning

CONFIG_DIR = Path(click.get_app_dir("catt"))
CONFIG_PATH = Path(CONFIG_DIR, "catt.cfg")
STATE_PATH = Path(CONFIG_DIR, "state.json")


class CattTimeParamType(click.ParamType):
    def convert(self, value, param, ctx):
        try:
            tdesc = [int(x) for x in value.split(":")]
            tlen = len(tdesc)
            if (tlen > 1 and any(t > 59 for t in tdesc)) or tlen > 3:
                raise ValueError
        except ValueError:
            self.fail("{} is not a valid time description.".format(value))

        tdesc.reverse()
        return sum(tdesc[p] * 60 ** p for p in range(tlen))


CATT_TIME = CattTimeParamType()


class YtdlOptParamType(click.ParamType):
    def convert(self, value, param, ctx):
        if "=" not in value:
            self.fail("{} is not a valid key/value pair.".format(value))

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
            raise CliError("No input received from stdin")
    if "://" not in value:
        if ctx.info_name != "cast":
            raise CliError("Local file not allowed as argument to this command")
        if not Path(value).is_file():
            raise CliError("The chosen file does not exist")
    return value


def process_path(ctx, param, value):
    path = Path(value) if value else None
    if path and (path.is_dir() or not path.parent.exists()):
        raise CliError("The specified path is invalid")
    return path


def process_subtitles(ctx, param, value):
    if not value:
        return None
    pval = urlparse(value).path if "://" in value else value
    if not pval.lower().endswith((".srt", ".vtt")):
        raise CliError("Invalid subtitles format, only srt and vtt are supported")
    if "://" not in value and not Path(value).is_file():
        raise CliError("Subtitles file [{}] does not exist".format(value))
    return value


def process_device(ctx, param, value):
    """
    Resolve real device name when value is an alias.

    :param value: Can be an ip-address or a name (alias or real name).
    :type value: str
    """

    if is_ipaddress(value):
        return value
    else:
        return ctx.default_map["aliases"].get(value, value)


def fail_if_no_ip(ipaddr):
    if not ipaddr:
        raise CliError("Local IP-address could not be determined")


def create_server_thread(filename, address, port, content_type, single_req=False):
    thr = Thread(target=serve_file, args=(filename, address, port, content_type, single_req))
    thr.setDaemon(True)
    thr.start()
    return thr


CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group(context_settings=CONTEXT_SETTINGS)
@click.option("--delete-cache", is_flag=True, help="Empty the Chromecast discovery cache.")
@click.option("-d", "--device", metavar="NAME_OR_IP", callback=process_device, help="Select Chromecast device.")
@click.version_option(version=__version__, prog_name="catt", message="%(prog)s v%(version)s, Xylophone Xtravaganza.")
@click.pass_context
def cli(ctx, delete_cache, device):
    if delete_cache:
        Cache().clear()
    ctx.obj["device"] = device


@cli.command("write_config", short_help="Write the name of default Chromecast device to config file.")
@click.pass_obj
def write_config(settings):
    if settings.get("device"):
        if not get_chromecast(settings["device"]):
            raise CliError("Specified device not found")
        writeconfig(settings)
    else:
        raise CliError("No device specified")


@cli.command(short_help="Send a video to a Chromecast for playing.")
@click.argument("video_url", callback=process_url)
@click.option("-s", "--subtitles", callback=process_subtitles, metavar="SUB", help="Specify a subtitles file.")
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
def cast(settings, video_url, subtitles, force_default, random_play, no_subs, no_playlist, ytdl_option):
    controller = "default" if force_default or ytdl_option else None
    playlist_playback = False
    st_thr = su_thr = subs = None
    cst, stream = setup_cast(
        settings["device"], video_url=video_url, prep="app", controller=controller, ytdl_options=ytdl_option
    )
    media_is_image = stream.guessed_content_category == "image"

    if stream.is_local_file:
        fail_if_no_ip(stream.local_ip)
        st_thr = create_server_thread(
            video_url, stream.local_ip, stream.port, stream.guessed_content_type, single_req=media_is_image
        )
    elif stream.is_playlist and not (no_playlist and stream.video_id):
        if stream.playlist_length == 0:
            cst.kill(idle_only=True)
            raise CliError("Playlist is empty")
        if not random_play and cst.playlist_capability and stream.playlist_all_ids:
            playlist_playback = True
        else:
            if random_play:
                entry = random.randrange(0, stream.playlist_length)
            else:
                warning("Playlist playback not possible, playing first video")
                entry = 0
            stream.set_playlist_entry(entry)

    if playlist_playback:
        click.echo("Casting remote playlist {}...".format(video_url))
        video_id = stream.video_id or stream.playlist_all_ids[0]
        cst.play_playlist(stream.playlist_id, video_id=video_id)
    else:
        if not subtitles and not no_subs and stream.is_local_file:
            subtitles = hunt_subtitles(video_url)
        if subtitles:
            fail_if_no_ip(stream.local_ip)
            subs = SubsInfo(subtitles, stream.local_ip, stream.port + 1)
            su_thr = create_server_thread(
                subs.file, subs.local_ip, subs.port, "text/vtt;charset=utf-8", single_req=True
            )

        click.echo("Casting {} file {}...".format("local" if stream.is_local_file else "remote", video_url))
        click.echo(
            '{} "{}" on "{}"...'.format("Showing" if media_is_image else "Playing", stream.video_title, cst.cc_name)
        )
        if cst.info_type == "url":
            cst.play_media_url(
                stream.video_url,
                title=stream.video_title,
                content_type=stream.guessed_content_type,
                subtitles=subs.url if subs else None,
                thumb=stream.video_thumbnail,
            )
        elif cst.info_type == "id":
            cst.play_media_id(stream.video_id)
        else:
            raise ValueError("Invalid or undefined info type")

        if stream.is_local_file or subs:
            add_msg = ", press Ctrl+C when done" if stream.is_local_file and not media_is_image else ""
            click.echo("Serving local file(s){}.".format(add_msg))
            while (st_thr and st_thr.is_alive()) or (su_thr and su_thr.is_alive()):
                time.sleep(1)


@cli.command("cast_site", short_help="Cast any website to a Chromecast.")
@click.argument("url", callback=process_url)
@click.pass_obj
def cast_site(settings, url):
    cst = setup_cast(settings["device"], controller="dashcast", action="load_url", prep="app")
    click.echo('Casting {} on "{}"...'.format(url, cst.cc_name))
    cst.load_url(url)


@cli.command(short_help="Add a video to the queue (YouTube only).")
@click.argument("video_url", callback=process_url)
@click.option("-n", "--play-next", is_flag=True, help="Add video immediately after currently playing video.")
@click.pass_obj
def add(settings, video_url, play_next):
    cst, stream = setup_cast(settings["device"], video_url=video_url, action="add", prep="control")
    if cst.name != stream.extractor or not (stream.is_remote_file or stream.is_playlist_with_active_entry):
        raise CliError("This url cannot be added to the queue")
    click.echo('Adding video id "{}" to the queue.'.format(stream.video_id))
    if play_next:
        cst.add_next(stream.video_id)
    else:
        cst.add(stream.video_id)


@cli.command(short_help="Remove a video from the queue (YouTube only).")
@click.argument("video_url", callback=process_url)
@click.pass_obj
def remove(settings, video_url):
    cst, stream = setup_cast(settings["device"], video_url=video_url, action="remove", prep="control")
    if cst.name != stream.extractor or not stream.is_remote_file:
        raise CliError("This url cannot be removed from the queue")
    click.echo('Removing video id "{}" from the queue.'.format(stream.video_id))
    cst.remove(stream.video_id)


@cli.command(short_help="Clear the queue (YouTube only).")
@click.pass_obj
def clear(settings):
    cst = setup_cast(settings["device"], action="clear", prep="control")
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
    try:
        cst = setup_cast(settings["device"], prep="info")
    except CastError:
        if json_output:
            info = {}
        else:
            raise
    else:
        info = cst.info

    if json_output:
        echo_json(info)
    else:
        for (key, value) in info.items():
            click.echo("{}: {}".format(key, value))


@cli.command(short_help="Scan the local network and show all Chromecasts and their IPs.")
@click.option("-j", "--json-output", is_flag=True, help="Output scan result as json.")
def scan(json_output):
    if not json_output:
        click.echo("Scanning Chromecasts...")
    devices_dict = {
        d.name: {
            "host": d.host,
            "port": d.port,
            "manufacturer": d.device.manufacturer,
            "model_name": d.model_name,
            "uuid": d.uuid,
            "cast_type": d.cast_type,
        }
        for d in get_chromecasts()
    }

    if json_output:
        echo_json(devices_dict)
    else:
        if not devices_dict:
            raise CastError("No devices found")
        for device in devices_dict.keys():
            click.echo("{host} - {device} - {manufacturer} {model_name}".format(device=device, **devices_dict[device]))


@cli.command(short_help="Save the current state of the Chromecast for later use.")
@click.argument("path", type=click.Path(writable=True), callback=process_path, required=False)
@click.pass_obj
def save(settings, path):
    cst = setup_cast(settings["device"], prep="control")
    if not cst.save_capability or cst.is_streaming_local_file:
        raise CliError("Saving state of this kind of content is not supported")
    elif cst.save_capability == "partial":
        warning("Please be advised that playlist data will not be saved")

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
        raise CliError("Save file in config dir has not been created")
    cst = setup_cast(settings["device"])
    state = CastState(path or STATE_PATH, StateMode.READ)
    try:
        data = state.get_data(cst.cc_name if not path else None)
    except StateFileError:
        raise CliError("The chosen file is not a valid save file")
    if not data:
        raise CliError("No save data found for this device")

    print_status(data["data"])
    click.echo("Restoring...")
    cst = setup_cast(settings["device"], prep="app", controller=data["controller"])
    cst.restore(data["data"])


def print_status(status):
    if status.get("title"):
        click.echo("Title: {}".format(status["title"]))

    if status.get("current_time"):
        current = human_time(status["current_time"])
        if status.get("duration"):
            duration = human_time(status["duration"])
            remaining = human_time(status["remaining"])
            click.echo("Time: {} / {} ({}%)".format(current, duration, status["progress"]))
            click.echo("Remaining time: {}".format(remaining))
        else:
            click.echo("Time: {}".format(current))

    if status.get("player_state"):
        click.echo("State: {}".format(status["player_state"]))

    if status.get("volume_level"):
        click.echo("Volume: {}".format(status["volume_level"]))


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
    try:
        return cli(obj={}, default_map=readconfig())
    except CattUserError as err:
        sys.exit("Error: {}.".format(str(err)))


if __name__ == "__main__":
    main()
