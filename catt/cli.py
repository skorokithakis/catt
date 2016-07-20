# -*- coding: utf-8 -*-
import click


from .controllers import get_stream_info, CastController, Cache


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
    stream_info = get_stream_info(video_url)
    cast = CastController()
    cc_name = cast.cast.device.friendly_name
    click.echo(u"Playing %s on %s..." % (stream_info["title"], cc_name))
    cast.play_media(stream_info["url"])


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
