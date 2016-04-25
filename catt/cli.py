# -*- coding: utf-8 -*-
import click

from .controllers import get_stream_url, CastController


@click.group()
def cli():
    pass


@cli.command()
@click.argument("video_url")
def cast(video_url):
    stream_url = get_stream_url(video_url)
    cast = CastController()
    cc_name = cast.cast.device.friendly_name
    click.echo(u"Playing %s on %s..." % (video_url, cc_name))
    cast.play_media(stream_url)


@cli.command()
def play():
    CastController().play()


@cli.command()
def pause():
    CastController().pause()


@cli.command()
def stop():
    CastController().kill()


@cli.command()
def rewind():
    CastController().rewind()


@cli.command()
@click.argument("seconds")
def seek(seconds):
    CastController().seek(seconds)


@cli.command()
def status():
    CastController().status()
