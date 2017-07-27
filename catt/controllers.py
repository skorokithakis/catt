import json
import os
import shutil
import tempfile
import threading
import time

import pychromecast

from click import ClickException, echo

from .youtube import YouTubeController


def get_chromecasts():
    devices = pychromecast.get_chromecasts()

    if not devices:
        raise CattCastError("No devices found.")

    devices.sort(key=lambda cc: cc.name)
    return devices


def get_chromecast(device_name):
    devices = get_chromecasts()

    if device_name:
        try:
            return next(cc for cc in devices if cc.name == device_name)
        except StopIteration:
            raise CattCastError("Specified device \"%s\" not found." % device_name)
    else:
        return devices[0]


def human_time(seconds):
    return time.strftime("%H:%M:%S", time.gmtime(seconds))


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


class StatusListener:
    def __init__(self, running_app, state):
        self._dmc_app_id = "CC1AD845"
        self._yt_app_id = "233637DE"
        self.dmc_ready = threading.Event()
        self.yt_ready = threading.Event()
        self.queue_ready = threading.Event()

        if running_app == self._dmc_app_id:
            self.dmc_ready.set()
        elif running_app == self._yt_app_id:
            self.yt_ready.set()

        if state != "BUFFERING" and self.yt_ready.is_set():
            self.queue_ready.set()

    def new_cast_status(self, status):
        if status.app_id == self._dmc_app_id:
            self.dmc_ready.set()
            self.yt_ready.clear()
        elif status.app_id == self._yt_app_id:
            self.yt_ready.set()
            self.dmc_ready.clear()
        else:
            self.dmc_ready.clear()
            self.yt_ready.clear()

    def new_media_status(self, status):
        if status.player_state == "BUFFERING":
            self.queue_ready.clear()
        elif self.yt_ready.is_set():
            self.queue_ready.set()


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

        self._listener = StatusListener(self.cast.app_id,
                                        self.cast.media_controller.status.player_state)
        self.cast.register_status_listener(self._listener)
        self.cast.media_controller.register_status_listener(self._listener)

        # We need to create the ytc object in the constructor
        # as the cli is calling add_to_yt_queue multiple times
        # when the user is casting a youtube playlist.
        self._ytc = YouTubeController()
        self.cast.register_handler(self._ytc)

        if state_check:
            self._check_state()

    def _check_state(self):
        if self.cast.app_id == "E8C28D3C" or not self.cast.app_id:
            raise CattCastError("Chromecast is inactive.")

        self.cast.media_controller.block_until_active(1.0)

        if self.cast.media_controller.status.player_state in ["UNKNOWN", "IDLE"]:
            raise CattCastError("Nothing is currently playing.")

    # The controller's start_new_session method
    # needs a video id for some reason unknown to me.
    def _prep_yt(self, video_id):
        if self.cast.app_id != "233637DE":
            self.cast.start_app("233637DE")
            self._listener.yt_ready.wait()

        if not self._ytc.in_session:
            self._ytc.start_new_session(video_id)

    def play_media(self, url, content_type="video/mp4"):
        self.cast.play_media(url, content_type)
        self._listener.dmc_ready.wait()
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
    
    def skip(self):
        status = self.cast.media_controller.status.__dict__
        
        if status["duration"]:
            self.seek(int(status["duration"]) + 1)
        else:
            raise CattCastError("Cannot skip live stream.")

    def volume(self, level):
        self.cast.set_volume(level)

    def volumeup(self, delta):
        self.cast.volume_up(delta)

    def volumedown(self, delta):
        self.cast.volume_down(delta)

    def status(self):
        status = self.cast.media_controller.status.__dict__

        if status["duration"]:
            dur, cur = int(status["duration"]), int(status["current_time"])
            duration = human_time(dur)
            current = human_time(cur)
            remaining = human_time(dur - cur)
            progress = int((1.0 * cur / dur) * 100)

            echo("Time: %s / %s (%s%%)" % (current, duration, progress))
            echo("Remaining time: %s" % remaining)

        echo("State: %s" % status["player_state"])

    def info(self):
        status = self.cast.media_controller.status.__dict__
        for (key, value) in status.items():
            echo("%s: %s" % (key, value))

    def kill(self):
        self.cast.quit_app()

    def play_yt_video(self, video_id):
        self._prep_yt(video_id)
        self._ytc.play_video(video_id)

    def add_to_yt_queue(self, video_id):
        self._prep_yt(video_id)
        # You can't add videos to the queue while the app is buffering.
        self._listener.queue_ready.wait()
        self._ytc.add_to_queue(video_id)
