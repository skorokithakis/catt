import hashlib
import json
import tempfile
import threading
from enum import Enum
from pathlib import Path

import pychromecast
from click import ClickException, echo
from pychromecast.controllers.dashcast import APP_DASHCAST as DASHCAST_APP_ID
from pychromecast.controllers.dashcast import DashCastController as PyChromecastDashCastController

from .__init__ import __version__ as CATT_VERSION
from .stream_info import StreamInfo
from .util import warning
from .youtube import YouTubeController

APP_INFO = [
    {"app_name": "youtube", "app_id": "233637DE", "supported_device_types": ["cast"]},
    {"app_name": "dashcast", "app_id": DASHCAST_APP_ID, "supported_device_types": ["cast", "audio"]},
]
DEFAULT_APP = {"app_name": "default", "app_id": "CC1AD845"}
BACKDROP_APP_ID = "E8C28D3C"
DEVICES_WITH_TWO_MODEL_NAMES = {"Eureka Dongle": "Chromecast"}
DEFAULT_PORT = 8009


def get_chromecasts(fail=True):
    devices = pychromecast.get_chromecasts()

    if fail and not devices:
        raise CattCastError("No devices found.")

    devices.sort(key=lambda cc: cc.name)
    return devices


def get_chromecast(device_name):
    devices = get_chromecasts()

    if device_name:
        try:
            return next(cc for cc in devices if cc.name == device_name)
        except StopIteration:
            raise CattCastError('Specified device "%s" not found.' % device_name)
    else:
        return devices[0]


def setup_cast(device_name, video_url=None, prep=None, controller=None, ytdl_options=None):
    """
    Prepares selected chromecast and/or media file.

    :param device_name: Friendly name of chromecast device to use.
    :type device_name: str or NoneType
    :param video_url: If supplied, setup_cast will try to exctract a media url
                      from this, for playback or queueing.
    :type video_url: str
    :param prep: If prep = "app", video_url, if supplied, is meant for playback.
                 The relevant chromecast app is started during initialization
                 of the CastController object.
                 If prep = "control", video_url, if supplied, is meant for
                 queueing. The state of the selected chromecast is determined
                 during initialization of the CastController object.
                 If prep = None, no preparation is done. Should only be used
                 if the desired action can be carried out regardless of the
                 state of the chromecast (like volume adjustment).
    :type prep: str
    :param controller: If supplied, the normal logic for determining the appropriate
                       controller is bypassed, and the one specified here is
                       returned instead.
    :type controller: str
    :param ytdl_options: Pairs of options to be passed to YoutubeDL.
                         For the available options please refer to
                         https://github.com/rg3/youtube-dl/blob/master/youtube_dl/YoutubeDL.py#L138-L317
    :type ytdl_options: tuple
    :returns: controllers.DefaultCastController or controllers.YoutubeCastController,
              and stream_info.StreamInfo if video_url is supplied.
    """

    cache = Cache()
    cached_ip, cached_port = cache.get_data(device_name)
    stream = None

    try:
        if not cached_ip:
            raise ValueError
        # tries = 1 is necessary in order to stop pychromecast engaging
        # in a retry behaviour when ip is correct, but port is wrong.
        cast = pychromecast.Chromecast(cached_ip, port=cached_port, tries=1)
    except (pychromecast.error.ChromecastConnectionError, ValueError):
        cast = get_chromecast(device_name)
        cache.set_data(cast.name, cast.host, cast.port)
    cast.wait()

    if video_url:
        model_name = DEVICES_WITH_TWO_MODEL_NAMES.get(cast.model_name, cast.model_name)
        cc_info = (cast.device.manufacturer, model_name)
        stream = StreamInfo(
            video_url, model=cc_info, host=cast.host, device_type=cast.cast_type, ytdl_options=ytdl_options
        )

    if controller:
        if controller == "default":
            app = DEFAULT_APP
        else:
            app = next(a for a in APP_INFO if a["app_name"] == controller)
    elif stream and prep == "app":
        if stream.is_local_file:
            app = DEFAULT_APP
        else:
            try:
                app = next(a for a in APP_INFO if a["app_name"] == stream.extractor)
            except StopIteration:
                app = DEFAULT_APP
    else:
        try:
            app = next(a for a in APP_INFO if a["app_id"] == cast.app_id)
        except StopIteration:
            app = DEFAULT_APP

    if app["app_name"] != "default" and cast.cast_type not in app["supported_device_types"]:
        msg = "The %s app is not available for this device." % app["app_name"].capitalize()
        if controller:
            raise CattCastError(msg)
        elif stream:
            warning(msg)
        app = DEFAULT_APP

    if app["app_name"] == "youtube":
        controller = YoutubeCastController(cast, app["app_name"], app["app_id"], prep=prep)
    # We make these checks in order to avoid problems,
    # in the unlikely event that youtube-dl gets an extractor named "dashcast".
    elif controller == "dashcast" or (app["app_name"] == "dashcast" and not stream):
        controller = DashCastController(cast, app["app_name"], app["app_id"], prep=prep)
    else:
        controller = DefaultCastController(cast, app["app_name"], app["app_id"], prep=prep)
    return (controller, stream) if stream else controller


def catch_namespace_error(func):
    """
    Use this decorator for methods in CastController subclasses where the intended
    action is dependent on the chromecast being in a particular state (such as not
    buffering). If the cc app is then interrupted while catt is waiting for this state,
    we fail in a nice way.
    """

    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except pychromecast.error.UnsupportedNamespace:
            raise CattCastError("Chromecast app operation was interrupted.")

    return wrapper


class CattCastError(ClickException):
    pass


class StateFileError(Exception):
    pass


class CattStore:
    def __init__(self, store_path):
        self.store_path = store_path

    def _create_store_dir(self):
        try:
            self.store_path.parent.mkdir()
        except FileExistsError:
            pass

    def _read_store(self):
        with self.store_path.open() as store:
            return json.load(store)

    def _write_store(self, data):
        with self.store_path.open("w") as store:
            json.dump(data, store)

    def get_data(self, *args):
        raise NotImplementedError

    def set_data(self, *args) -> None:
        raise NotImplementedError

    def clear(self):
        try:
            self.store_path.unlink()
            self.store_path.parent.rmdir()
        except FileNotFoundError:
            pass


class Cache(CattStore):
    def __init__(self):
        vhash = hashlib.sha1(CATT_VERSION.encode()).hexdigest()[:8]
        cache_path = Path(tempfile.gettempdir(), "catt_%s_cache" % vhash, "chromecast_hosts")
        super(Cache, self).__init__(cache_path)
        self._create_store_dir()

        if not self.store_path.is_file():
            devices = get_chromecasts(fail=False)
            cache_data = {d.name: self._create_device_entry(d.host, d.port) for d in devices}
            self._write_store(cache_data)

    def _create_device_entry(self, ip, port):
        device_data = {"ip": ip}
        if port != DEFAULT_PORT:
            device_data["group_port"] = port
        return device_data

    def get_data(self, name: str):  # type: ignore
        data = self._read_store()
        # In the case that cache has been initialized with no cc's on the
        # network, we need to ensure auto-discovery.
        if not data:
            return (None, None)
        if name:
            fetched = data.get(name)
        else:
            # When the user does not specify a device, we need to make an attempt
            # to consistently return the same IP, thus the alphabetical sorting.
            fetched = data[min(data, key=str)]
        return (fetched["ip"], fetched.get("group_port", 0)) if fetched else (None, None)

    def set_data(self, name: str, ip: str, port: int) -> None:  # type: ignore
        data = self._read_store()
        data[name] = self._create_device_entry(ip, port)
        self._write_store(data)


class StateMode(Enum):
    READ = 1
    CONF = 2
    ARBI = 3


class CastState(CattStore):
    def __init__(self, state_path: Path, mode: StateMode) -> None:
        super(CastState, self).__init__(state_path)
        if mode == StateMode.CONF:
            self._create_store_dir()
            if not self.store_path.is_file():
                self._write_store({})
        elif mode == StateMode.ARBI:
            self._write_store({})

    def get_data(self, name: str):  # type: ignore
        try:
            data = self._read_store()
            if set(next(iter(data.values())).keys()) != set(["controller", "data"]):
                raise ValueError
        except (json.decoder.JSONDecodeError, ValueError, StopIteration, AttributeError):
            raise StateFileError
        if name:
            return data.get(name)
        else:
            return next(iter(data.values()))

    def set_data(self, name: str, value: str) -> None:  # type: ignore
        data = self._read_store()
        data[name] = value
        self._write_store(data)


class CastStatusListener:
    def __init__(self, app_id, active_app_id):
        self.app_id = app_id
        self.app_ready = threading.Event()
        if app_id == active_app_id and app_id != DASHCAST_APP_ID:
            self.app_ready.set()

    def new_cast_status(self, status):
        if self._is_app_ready(status):
            self.app_ready.set()
        else:
            self.app_ready.clear()

    def _is_app_ready(self, status):
        if status.app_id == self.app_id == DASHCAST_APP_ID:
            # DashCast is an exception and therefore needs special treatment.
            # Whenever it's loaded, it's initial status is "Application is starting",
            # as shown here: https://github.com/stestagg/dashcast/blob/master/receiver.html#L163
            # While in that status, it's still not ready to start receiving nor loading URLs
            # Therefore we must wait until its status change to "Application ready"
            # https://github.com/stestagg/dashcast/blob/master/receiver.html#L143
            #
            # If one does not wait for the status to become "Application ready",
            # casting the URL will trigger a race condition as the URL may arrive before the
            # "Application ready" status. In this case, casting will not work.
            # One simple way to confirm changes is to uncomment the line below
            # print(status.status_text)
            return status.status_text == "Application ready"
        return status.app_id == self.app_id


class MediaStatusListener:
    def __init__(self, state):
        self.not_buffering = threading.Event()
        self.playing = threading.Event()
        if state != "BUFFERING":
            self.not_buffering.set()
        if state == "PLAYING":
            self.playing.set()

    def new_media_status(self, status):
        if status.player_state == "BUFFERING":
            self.not_buffering.clear()
            self.playing.clear()
        elif status.player_state == "PLAYING":
            self.not_buffering.set()
            self.playing.set()
        else:
            self.not_buffering.set()
            self.playing.clear()


class CastController:
    def __init__(self, cast, name, app_id, prep=None):
        self._cast = cast
        self.name = name
        self.info_type = None
        self.save_capability = None
        self.playlist_capability = None

        self._cast_listener = CastStatusListener(app_id, self._cast.app_id)
        self._cast.register_status_listener(self._cast_listener)
        self._media_listener = MediaStatusListener(self._cast.media_controller.status.player_state)
        self._cast.media_controller.register_status_listener(self._media_listener)

        try:
            self._cast.register_handler(self._controller)
        except AttributeError:
            self._controller = self._cast.media_controller

        if prep == "app":
            self._prep_app()
        elif prep == "control":
            self._prep_control()

    @property
    def cc_name(self):
        return self._cast.device.friendly_name

    @property
    def info(self):
        status = self._cast.media_controller.status.__dict__
        # Values in media_controller.status for the keys "volume_level" and "volume_muted"
        # are always the same, regardless of actual state, so we discard those by
        # overwriting them with the values from system status.
        status.update(self._cast.status._asdict())
        return status

    @property
    def media_info(self):
        status = self._cast.media_controller.status
        return {
            "title": status.title,
            "content_id": status.content_id,
            "current_time": status.current_time if self._is_seekable else None,
            "thumb": status.images[0].url if status.images else None,
        }

    @property
    def cast_info(self):
        status = self._cast.media_controller.status
        cinfo = self.media_info

        if self._is_seekable:
            duration, current = status.duration, status.current_time
            remaining = duration - current
            progress = int((1.0 * current / duration) * 100)
            cinfo.update({"duration": duration, "remaining": remaining, "progress": progress})

        if self._is_audiovideo:
            cinfo.update({"player_state": status.player_state})

        cinfo.update({"volume_level": str(int(round(self._cast.status.volume_level, 2) * 100))})
        return cinfo

    @property
    def is_streaming_local_file(self):
        status = self._cast.media_controller.status
        return status.content_id.endswith("?loaded_from_catt")

    @property
    def _is_seekable(self):
        status = self._cast.media_controller.status
        return status.duration and status.stream_type == "BUFFERED"

    @property
    def _is_audiovideo(self):
        status = self._cast.media_controller.status
        content_type = status.content_type.split("/")[0] if status.content_type else None
        # We can't check against valid types, as some custom apps employ
        # a different scheme (like "application/dash+xml").
        return content_type != "image" if content_type else False

    @property
    def _is_idle(self):
        status = self._cast.media_controller.status
        # Dashcast (and maybe others) returns player_state == "UNKNOWN" while being active.
        # Checking stream_type appears to be reliable.
        return status.player_state in ["UNKNOWN", "IDLE"] and status.stream_type != "UNKNOWN"

    def _prep_app(self):
        """Make sure desired chromecast app is running."""

        if not self._cast_listener.app_ready.is_set():
            self._cast.start_app(self._cast_listener.app_id)
            self._cast_listener.app_ready.wait()

    def _prep_control(self):
        """Make sure chromecast is in an active state."""

        if self._cast.app_id == BACKDROP_APP_ID or not self._cast.app_id:
            raise CattCastError("Chromecast is inactive.")
        self._cast.media_controller.block_until_active(1.0)
        if self._is_idle:
            raise CattCastError("Nothing is currently playing.")

    def play_media_url(self, video_url, **kwargs):
        """
        CastController subclasses need to implement
        either play_media_url or play_media_id
        """

        raise NotImplementedError

    def play_media_id(self, video_id):
        """
        CastController subclasses need to implement
        either play_media_url or play_media_id
        """

        raise NotImplementedError

    def play_playlist(self, playlist_id):
        raise NotImplementedError

    def play(self):
        self._cast.media_controller.play()

    def pause(self):
        self._cast.media_controller.pause()

    def seek(self, seconds):
        if self._is_seekable:
            self._cast.media_controller.seek(seconds)
        else:
            raise CattCastError("Stream is not seekable.")

    def rewind(self, seconds):
        pos = self._cast.media_controller.status.current_time
        self.seek(pos - seconds)

    def ffwd(self, seconds):
        pos = self._cast.media_controller.status.current_time
        self.seek(pos + seconds)

    def skip(self):
        if self._is_seekable:
            self._cast.media_controller.skip()
        else:
            raise CattCastError("Stream is not skippable.")

    def volume(self, level):
        self._cast.set_volume(level)

    def volumeup(self, delta):
        self._cast.volume_up(delta)

    def volumedown(self, delta):
        self._cast.volume_down(delta)

    def kill(self, idle_only=False):
        """
        Kills current Chromecast session.

        :param idle_only: If set, session is only killed if the active Chromecast app
                          is idle. Use to avoid killing an active streaming session
                          when catt fails with certain invalid actions (such as trying
                          to cast an empty playlist).
        :type idle_only: bool
        """

        if idle_only and not self._is_idle:
            return
        self._cast.quit_app()

    def restore(self, data):
        """
        Recreates Chromecast state from save data.
        Subclasses can implement this if its possible to recreate
        a session from save data.
        """

        raise NotImplementedError

    def _not_supported(self):
        self.kill(idle_only=True)
        raise CattCastError("This action is not supported by the %s controller." % self.name.capitalize())

    def add(self, video_id):
        self._not_supported()


class DefaultCastController(CastController):
    def __init__(self, cast, name, app_id, prep=None):
        super(DefaultCastController, self).__init__(cast, name, app_id, prep=prep)
        self.info_type = "url"
        self.save_capability = (
            "complete" if (self._is_seekable and self._cast.app_id == DEFAULT_APP["app_id"]) else None
        )

    def play_media_url(self, video_url, **kwargs):
        content_type = kwargs.get("content_type") or "video/mp4"
        self._controller.play_media(
            video_url,
            content_type,
            current_time=kwargs.get("current_time"),
            title=kwargs.get("title"),
            thumb=kwargs.get("thumb"),
            subtitles=kwargs.get("subtitles"),
        )
        self._controller.block_until_active()

    def restore(self, data):
        self.play_media_url(
            data["content_id"], current_time=data["current_time"], title=data["title"], thumb=data["thumb"]
        )


class DashCastController(CastController):
    def __init__(self, cast, name, app_id, prep=None):
        self._controller = PyChromecastDashCastController()
        super(DashCastController, self).__init__(cast, name, app_id, prep=prep)

    def load_url(self, url, **kwargs):
        self._controller.load_url(url, force=True)

    def _prep_app(self):
        """Make sure desired chromecast app is running."""

        # We must force the launch of the DashCast app because it, by design,
        # becomes unresponsive after a website is loaded.
        self._cast.start_app(self._cast_listener.app_id, force_launch=True)
        self._cast_listener.app_ready.wait()

    def _prep_control(self):
        self._not_supported()


class YoutubeCastController(CastController):
    def __init__(self, cast, name, app_id, prep=None):
        self._controller = YouTubeController()
        super(YoutubeCastController, self).__init__(cast, name, app_id, prep=prep)
        self.info_type = "id"
        self.save_capability = "partial"
        self.playlist_capability = "complete"

    # The controller's start_new_session method needs a video id.
    def _prep_yt(self, video_id):
        if not self._controller.in_session:
            self._controller.start_new_session(video_id)

    def play_media_id(self, video_id):
        self._prep_yt(video_id)
        self._controller.play_video(video_id)

    def play_playlist(self, playlist):
        self.play_media_id(playlist[0])
        if len(playlist) > 1:
            for video_id in playlist[1:]:
                self.add(video_id)

    @catch_namespace_error
    def add(self, video_id):
        echo('Adding video id "%s" to the queue.' % video_id)
        self._prep_yt(video_id)
        # You can't add videos to the queue while the app is buffering.
        self._media_listener.not_buffering.wait()
        self._controller.add_to_queue(video_id)

    @catch_namespace_error
    def restore(self, data):
        self.play_media_id(data["content_id"])
        self._media_listener.playing.wait()
        self.seek(data["current_time"])
