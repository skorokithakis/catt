import os
import time
import youtube_dl
import pychromecast
import shutil
import tempfile
import json
from click import echo, ClickException


def get_stream_info(video_url):
    ydl = youtube_dl.YoutubeDL({})
    info = ydl.extract_info(video_url, download=False)
    format_selector = ydl.build_format_selector("best")
    try:
        best_format = list(format_selector(info))[0]
    except KeyError:
        best_format = info
    stream_info = {
        "url": best_format["url"],
        "title": info.get("title", video_url),
    }
    return stream_info


class ChromecastDeviceError(ClickException):
    pass


class Cache:
    def __init__(self, duration=3 * 24 * 3600,
                 cache_dir=os.path.join(tempfile.gettempdir(), "catt_cache")):
        self.cache_dir = cache_dir
        try:
            os.mkdir(cache_dir)
        except:
            pass

        cache_filename = os.path.join(cache_dir, "chromecast_hosts")
        self.cache_filename = cache_filename

        if os.path.exists(cache_filename):
            if os.path.getctime(cache_filename) + duration < time.time():
                self._initialize_cache()
        else:
            self._initialize_cache()

    def _initialize_cache(self):
        data = {}
        devices = pychromecast.get_chromecasts()
        for device in devices:
            data[device.name] = device.host
        self._write_cache(data)

    def _read_cache(self):
        with open(self.cache_filename, "r") as cache:
            return json.load(cache)

    def _write_cache(self, data):
        with open(self.cache_filename, "w") as cache:
            json.dump(data, cache)

    def get(self, name):
        data = self._read_cache()
        if not data:
            return None
        if not name:
            devices = list(data.keys())
            devices.sort()
            return data[devices[0]]
        try:
            return data[name]
        except KeyError:
            return None

    def set(self, name, value):
        data = self._read_cache()
        data[name] = value
        self._write_cache(data)

    def clear(self):
        try:
            shutil.rmtree(self.cache_dir)
        except:
            pass


class CastController:
    def __init__(self, device_name):
        cache = Cache()
        cached_ip = cache.get(device_name)

        try:
            if not cached_ip:
                raise ValueError
            self.cast = pychromecast.Chromecast(cached_ip)
        except (pychromecast.error.ChromecastConnectionError, ValueError):
            if device_name:
                self.cast = pychromecast.get_chromecast(friendly_name=device_name)
            else:
                self.cast = pychromecast.get_chromecast()
            if not self.cast:
                raise ChromecastDeviceError("Device not found.")
            cache.set(self.cast.name, self.cast.host)

        time.sleep(0.2)

    def play_media(self, url, content_type="video/mp4"):
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
        pos = self.cast.media_controller.status.current_time
        self.seek(pos - seconds)

    def ffwd(self, seconds):
        pos = self.cast.media_controller.status.current_time
        self.seek(pos + seconds)

    def volume(self, level):
        self.cast.set_volume(level)

    def volumeup(self):
        self.cast.volume_up()

    def volumedown(self):
        self.cast.volume_down()

    def status(self):
        status = self.cast.media_controller.status.__dict__
        if not status["duration"]:
            echo("Nothing currently playing.")
            return

        status["current_time"] = int(status["current_time"])
        status["duration"] = int(status["duration"])
        status["progress"] = int(((1.0 * status["current_time"]) / status["duration"]) * 100)
        status["remaining_minutes"] = (status["duration"] - status["current_time"]) / 60

        echo(
            "Time: {current_time}/{duration} ({progress}%)\n"
            "Remaining minutes: {remaining_minutes:0.1f}\n"
            "State: {player_state}\n".format(**status)
        )

    def info(self):
        status = self.cast.media_controller.status.__dict__
        for (key, value) in status.items():
            echo("%s : %s" % (key, value))

    def kill(self):
        self.cast.quit_app()
