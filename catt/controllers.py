import json
import os
import shutil
import tempfile
import threading
import time

import pychromecast

from click import ClickException, echo

from .stream_info import StreamInfo
from .youtube import YouTubeController


APP_INFO = [{"app_name": "youtube", "app_id": "233637DE", "supported_devices": ["cast"]}]
DEFAULT_APP = {"app_name": "default", "app_id": "CC1AD845"}
BACKDROP_APP_ID = "E8C28D3C"


def get_chromecasts():
    devices = pychromecast.get_chromecasts()

    if not devices:
        raise CattCastError("No devices found.")

    devices.sort(key=lambda cc: cc.name)
    # We need to ensure that all Chromecast objects contain DIAL info.
    return [pychromecast.Chromecast(cc.host) for cc in devices]


def get_chromecast(device_name):
    devices = get_chromecasts()

    if device_name:
        try:
            return next(cc for cc in devices if cc.name == device_name)
        except StopIteration:
            raise CattCastError("Specified device \"%s\" not found." % device_name)
    else:
        return devices[0]


def setup_cast(device_name, video_url=None, prep=None):
    cache = Cache()
    cached_ip = cache.get(device_name)

    try:
        if not cached_ip:
            raise ValueError
        cast = pychromecast.Chromecast(cached_ip)
    except (pychromecast.error.ChromecastConnectionError, ValueError):
        cast = get_chromecast(device_name)
        cache.set(cast.name, cast.host)
    cast.wait()

    if video_url:
        cc_info = (cast.device.manufacturer, cast.model_name)
        stream = StreamInfo(video_url, model=cc_info, host=cast.host)
        if stream.is_local_file:
            app = DEFAULT_APP
        else:
            try:
                app = next(a for a in APP_INFO if a["app_name"] == stream.extractor)
            except StopIteration:
                app = DEFAULT_APP
    else:
        stream = None
        try:
            app = next(a for a in APP_INFO if a["app_id"] == cast.app_id)
        except StopIteration:
            app = DEFAULT_APP

    if app["app_name"] != "default":
        if cast.cast_type not in app["supported_devices"]:
            if stream:
                echo("The %s app is not available for this device." % app["app_name"].capitalize(),
                     err=True)
            app = DEFAULT_APP

    if app["app_name"] == "youtube":
        controller = YoutubeCastController(cast, app["app_name"], app["app_id"], prep=prep)
    else:
        controller = DefaultCastController(cast, app["app_name"], app["app_id"], prep=prep)
    return (controller, stream) if stream else controller


class CattCastError(ClickException):
    pass


class PlaybackError(Exception):
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
    def __init__(self, app_id, active_app_id, state):
        self.app_id = app_id
        self.app_ready = threading.Event()
        self.not_buffering = threading.Event()

        if app_id == active_app_id:
            self.app_ready.set()
            if state != "BUFFERING":
                self.not_buffering.set()

    def new_cast_status(self, status):
        if status.app_id == self.app_id:
            self.app_ready.set()
        else:
            self.app_ready.clear()

    def new_media_status(self, status):
        if status.player_state == "BUFFERING":
            self.not_buffering.clear()
        elif self.app_ready.is_set():
            self.not_buffering.set()


class CastController:
    def __init__(self, cast, name, app_id, prep=None):
        self.cast = cast
        self._name = name
        self.info_type = None
        self._listener = StatusListener(app_id, self.cast.app_id,
                                        self.cast.media_controller.status.player_state)
        self.cast.register_status_listener(self._listener)
        self.cast.media_controller.register_status_listener(self._listener)

        try:
            self.cast.register_handler(self._controller)
        except AttributeError:
            self._controller = self.cast.media_controller

        if prep == "app":
            self._prep_app()
        elif prep == "control":
            self._prep_control()

    def _prep_app(self):
        if not self._listener.app_ready.is_set():
            self.cast.start_app(self._listener.app_id)
            self._listener.app_ready.wait()

    def _prep_control(self):
        if self.cast.app_id == BACKDROP_APP_ID or not self.cast.app_id:
            raise CattCastError("Chromecast is inactive.")
        self.cast.media_controller.block_until_active(1.0)
        if self.cast.media_controller.status.player_state in ["UNKNOWN", "IDLE"]:
            raise CattCastError("Nothing is currently playing.")

    def _human_time(self, seconds):
        return time.strftime("%H:%M:%S", time.gmtime(seconds))

    def play_media_url(self, video_url):
        raise PlaybackError

    def play_media_id(self, video_id):
        raise PlaybackError

    def play_playlist(self, playlist_id):
        raise PlaybackError

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
            duration, current = self._human_time(dur), self._human_time(cur)
            remaining = self._human_time(dur - cur)
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

    def _not_supported(self):
        if self.cast.media_controller.status.player_state in ["UNKNOWN", "IDLE"]:
            self.kill()
        raise CattCastError("This action is not supported by the %s controller." % self._name.capitalize())

    def add(self, video_id):
        self._not_supported()


class DefaultCastController(CastController):
    def __init__(self, cast, name, app_id, prep=None):
        super(DefaultCastController, self).__init__(cast, name, app_id, prep=prep)
        self.info_type = "url"

    def play_media_url(self, video_url):
        self._controller.play_media(video_url, "video/mp4")
        self._controller.block_until_active()


class YoutubeCastController(CastController):
    def __init__(self, cast, name, app_id, prep=None):
        self._controller = YouTubeController()
        super(YoutubeCastController, self).__init__(cast, name, app_id, prep=prep)
        self.info_type = "id"

    # The controller's start_new_session method needs a video id.
    def _prep_yt(self, video_id):
        if not self._controller.in_session:
            self._controller.start_new_session(video_id)

    def play_media_id(self, video_id):
        self._prep_yt(video_id)
        self._controller.play_video(video_id)

    def play_playlist(self, playlist):
        if not playlist:
            raise CattCastError("Playlist is empty.")
        self.play_media_id(playlist[0])
        if len(playlist) > 1:
            for video_id in playlist[1:]:
                self.add(video_id)

    def add(self, video_id):
        echo("Adding video id \"%s\" to the queue." % video_id)
        self._prep_yt(video_id)
        # You can't add videos to the queue while the app is buffering.
        self._listener.not_buffering.wait()
        self._controller.add_to_queue(video_id)
