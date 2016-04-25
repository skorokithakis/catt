# -*- coding: utf-8 -*-
import sys
import os
import time
from click import echo
import click
import youtube_dl
import pychromecast


def get_stream_url(video_url):
    ydl = youtube_dl.YoutubeDL({})
    info = ydl.extract_info(video_url, download=False)
    format_selector = ydl.build_format_selector("best")
    best_format = list(format_selector(info["formats"]))[0]
    return best_format["url"]


class Cache:
    def __init__(self, cache_dir):
        self.cache_dir = cache_dir
        try:
            os.mkdir(cache_dir)
        except:
            pass

    def _get_cache_filename(self, key):
        return os.path.join(self.cache_dir, key)

    def get(self, key, duration):
        cache_filename = self._get_cache_filename(key)
        if os.path.exists(cache_filename):
            if os.path.getctime(cache_filename) + duration > time.time():
                return open(cache_filename).read()
            else:
                os.remove(cache_filename)
        else:
            return None

    def set(self, key, value):
        open(self._get_cache_filename(key), "w").write(value)


class CastController:
    def __init__(self):
        cache = Cache("/tmp/catt_cache/")

        cached_chromecast = cache.get("chromecast_host", 3 * 24 * 3600)
        if cached_chromecast:
            self.cast = pychromecast.Chromecast(cached_chromecast)
        else:
            self.cast = pychromecast.get_chromecast()
            cache.set("chromecast_host", self.cast.host)
        time.sleep(0.2)

    def play_media(self, url, content_type="video/mp4"):
        self.kill()
        time.sleep(5)
        self.cast.play_media(url, content_type)

    def play(self):
        self.cast.media_controller.play()

    def pause(self):
        self.cast.media_controller.pause()

    def stop(self):
        self.cast.media_controller.stop()

    def seek(self, seconds):
        self.cast.media_controller.seek(int(seconds))

    def rewind(self, seconds):
        try:
            seconds = int(seconds)
        except:
            seconds = 30
        pos = self.cast.media_controller.status.current_time
        self.seek(pos - seconds)

    def status(self):
        status = self.cast.media_controller.status.__dict__
        status["progress"] = int((status["current_time"] / status["duration"]) * 100)
        status["remaining_minutes"] = (status["duration"] - status["current_time"]) / 60
        echo(
            "Time: {current_time}/{duration} ({progress}%)\n"
            "Remaining minutes: {remaining_minutes:0.1f}\n"
            "State: {player_state}\n".format(**status)
        )

    def kill(self):
        self.cast.quit_app()


@click.group()
def cli():
    pass


@cli.command()
@click.argument("video_url")
def cast(video_url):
    stream_url = get_stream_url(video_url)
    cast = CastController()
    cc_name = cast.cast.device.friendly_name
    echo(u"Playing %s on %s..." % (video_url, cc_name))
    cast.play_media(stream_url)


@cli.command()
def play():
    CastController().play()


@cli.command()
def pause():
    CastController().pause()


@cli.command()
def stop():
    CastController().stop()


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
