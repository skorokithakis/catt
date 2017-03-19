import json
import os
import shutil
import tempfile
import time

import pychromecast
import youtube_dl

from click import ClickException, echo


def get_stream_info(video_url):
    ydl = youtube_dl.YoutubeDL({"noplaylist": True, "playlistend": 1})

    try:
        pre = ydl.extract_info(video_url, process=False)
    except youtube_dl.utils.DownloadError:
        raise CattCastError("Remote resource not found.")

    if "entries" in pre:
        preinfo = list(pre["entries"])[0]
        msg = "first"
    elif "url" in pre:
        preinfo = pre
        msg = "current"
    else:
        preinfo = pre
        msg = None

    info = ydl.process_ie_result(preinfo, download=False)

    if msg:
        echo("Warning: Playlists not supported, playing %s video." % msg,
             err=True)

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


def get_chromecasts():
    devices = pychromecast.get_chromecasts()
    devices.sort(key=lambda cc: cc.name)
    return devices


def get_chromecast(device_name):
    devices = pychromecast.get_chromecasts()
    if not devices:
        raise CattCastError("No devices found.")
    if device_name:
        try:
            return next(cc for cc in devices if cc.name == device_name)
        except StopIteration:
            raise CattCastError("Specified device %s not found." % device_name)
    else:
        return min(devices, key=lambda cc: cc.name)


class CattCastError(ClickException):
    pass


class Cache:
    def __init__(self, duration=3 * 24 * 3600,
                 cache_dir=os.path.join(tempfile.gettempdir(), "catt_cache")):
        self.cache_dir = cache_dir
        try:
            os.mkdir(cache_dir)
        except:
            pass

        self.cache_filename = os.path.join(cache_dir, "chromecast_hosts")

        if os.path.exists(self.cache_filename):
            if os.path.getctime(self.cache_filename) + duration < time.time():
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

        # In the case that cache has been initialized with no cc's on the
        # network, we need to ensure auto-discovery.
        if not data:
            return None
        # When the user does not specify a device, we need to make an attempt
        # to consistently return the same IP, thus the alphabetical sorting.
        if not name:
            return data[min(data, key=str)]
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
    def __init__(self, device_name, state_check=True):
        cache = Cache()
        cached_ip = cache.get(device_name)

        try:
            if not cached_ip:
                raise ValueError
            self.cast = pychromecast.Chromecast(cached_ip)
        except (pychromecast.error.ChromecastConnectionError, ValueError):
            self.cast = get_chromecast(device_name)
            cache.set(self.cast.name, self.cast.host)

        self.cast.wait()

        if state_check:
            self._check_state()

    def _check_state(self):
        if self.cast.app_id == "E8C28D3C" or not self.cast.app_id:
            raise CattCastError("Chromecast is inactive.")
        self.cast.media_controller.block_until_active(1.0)
        if self.cast.media_controller.status.player_state in ["UNKNOWN", "IDLE"]:
            raise CattCastError("Nothing is currently playing.")

    def play_media(self, url, content_type="video/mp4"):
        self.cast.play_media(url, content_type)
        self.cast.media_controller.block_until_active()

    def play(self):
        self.cast.media_controller.play()

    def pause(self):
        self.cast.media_controller.pause()

    def seek(self, seconds):
        self.cast.media_controller.seek(seconds)

    def rewind(self, seconds):
        pos = self.cast.media_controller.status.current_time
        self.seek(pos - seconds)

    def ffwd(self, seconds):
        pos = self.cast.media_controller.status.current_time
        self.seek(pos + seconds)

    def volume(self, level):
        self.cast.set_volume(level)

    def volumeup(self, delta):
        self.cast.volume_up(delta)

    def volumedown(self, delta):
        self.cast.volume_down(delta)

    def status(self):
        status = self.cast.media_controller.status.__dict__

        if not status["duration"]:
            echo("State: {player_state}\n".format(**status))
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
