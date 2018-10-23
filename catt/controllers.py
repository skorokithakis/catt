import hashlib
import json
import re
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
NO_PLAYER_STATE_IDS = ["84912283"]
DEVICES_WITH_TWO_MODEL_NAMES = {"Eureka Dongle": "Chromecast"}
DEFAULT_PORT = 8009
VALID_STATE_EVENTS = ["UNKNOWN", "IDLE", "BUFFERING", "PLAYING", "PAUSED"]


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


def get_cast(device_name):
    cache = Cache()
    cached_ip, cached_port = cache.get_data(device_name)

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
    return cast


def get_stream(url, device_info=None, host=None, ytdl_options=None):
    if device_info:
        model_name = DEVICES_WITH_TWO_MODEL_NAMES.get(device_info.model_name, device_info.model_name)
        cc_info = (device_info.manufacturer, model_name)
        cast_type = device_info.cast_type
    else:
        cc_info = cast_type = None
    return StreamInfo(url, host=host, model=cc_info, device_type=cast_type, ytdl_options=ytdl_options)


def get_app_info(id_or_name, cast_type=None, strict=False, show_warning=False):
    if id_or_name == "default":
        return DEFAULT_APP

    field = "app_id" if re.match("[0-9A-F]{8}$", id_or_name) else "app_name"
    try:
        app_info = next(a for a in APP_INFO if a[field] == id_or_name)
    except StopIteration:
        if strict:
            raise AppSelectionError("app not found (strict is set)")
        else:
            app_info = DEFAULT_APP

    if app_info["app_name"] != "default":
        if not cast_type:
            raise AppSelectionError("cast_type is needed for app selection")
        elif cast_type not in app_info["supported_device_types"]:
            msg = "The %s app is not available for this device." % app_info["app_name"].capitalize()
            if strict:
                raise CattCastError(msg)
            elif show_warning:
                warning(msg)
            app_info = DEFAULT_APP
    return app_info


def get_controller(cast, app_info, action=None, prep=None):
    app_name = app_info["app_name"]
    if app_name == "youtube":
        controller = YoutubeCastController
    elif app_name == "dashcast":
        controller = DashCastController
    else:
        controller = DefaultCastController
    if action and action not in dir(controller):
        raise CattCastError("This action is not supported by the %s controller." % app_name)
    return controller(cast, app_name, app_info["app_id"], prep=prep)


def setup_cast(device_name, video_url=None, controller=None, ytdl_options=None, action=None, prep=None):
    cast = get_cast(device_name)
    cast_type = cast.cast_type
    stream = (
        get_stream(video_url, device_info=cast.device, host=cast.host, ytdl_options=ytdl_options) if video_url else None
    )

    if controller:
        app_info = get_app_info(controller, cast_type, strict=True)
    elif stream and prep == "app":
        if stream.is_local_file:
            app_info = get_app_info("default")
        else:
            app_info = get_app_info(stream.extractor, cast_type, show_warning=True if stream else False)
    else:
        app_info = get_app_info(cast.app_id, cast_type)

    controller = get_controller(cast, app_info, action=action, prep=prep)
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


class ListenerError(Exception):
    pass


class AppSelectionError(Exception):
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
    def __init__(self, current_state, states, invert=False, fail=False):
        if any(s not in VALID_STATE_EVENTS for s in states):
            raise ListenerError("invalid state(s)")

        if invert:
            self._states_waited_for = [s for s in VALID_STATE_EVENTS if s not in states]
        else:
            self._states_waited_for = states
        if fail and current_state in self._states_waited_for:
            raise ListenerError("condition is already met (fail is set)")

        self._state_event = threading.Event()
        self._current_state = current_state

    def new_media_status(self, status):
        self._current_state = status.player_state
        if self._current_state in self._states_waited_for:
            self._state_event.set()
        else:
            self._state_event.clear()

    def wait_for_states(self):
        if self._current_state not in self._states_waited_for:
            self._state_event.wait()


class CastController:
    def __init__(self, cast, name, app_id, prep=None):
        self._cast = cast
        self.name = name
        self.info_type = None
        self.save_capability = None
        self.playlist_capability = None

        self._cast_listener = CastStatusListener(app_id, self._cast.app_id)
        self._cast.register_status_listener(self._cast_listener)

        try:
            self._cast.register_handler(self._controller)
        except AttributeError:
            self._controller = self._cast.media_controller

        if prep == "app":
            self._prep_app()
        elif prep == "control":
            self._prep_control()
        elif prep == "info":
            self._prep_info()

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
        # Dashcast (and maybe others) returns player_state == "UNKNOWN" while being active,
        # so we maintain a list of those apps.
        return status.player_state in ["UNKNOWN", "IDLE"] and self._cast.app_id not in NO_PLAYER_STATE_IDS

    def _prep_app(self):
        """Make sure desired chromecast app is running."""

        if not self._cast_listener.app_ready.is_set():
            self._cast.start_app(self._cast_listener.app_id)
            self._cast_listener.app_ready.wait()

    def _prep_control(self):
        """Make sure chromecast is not inactive or idle."""

        self._check_inactive()
        self._cast.media_controller.block_until_active(1.0)
        if self._is_idle:
            raise CattCastError("Nothing is currently playing.")

    def _prep_info(self):
        """Make sure chromecast is not inactive."""

        self._check_inactive()
        self._cast.media_controller.block_until_active(1.0)

    def _check_inactive(self):
        if self._cast.app_id == BACKDROP_APP_ID or not self._cast.app_id:
            raise CattCastError("Chromecast is inactive.")

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


class MediaControllerMixin:
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


class PlaybackBaseMixin:
    def play_media_url(self, video_url, **kwargs):
        raise NotImplementedError

    def play_media_id(self, video_id):
        raise NotImplementedError

    def play_playlist(self, playlist_id):
        raise NotImplementedError

    def wait_for(self, states, invert=False, fail=False):
        states = [states] if isinstance(states, str) else states
        media_listener = MediaStatusListener(
            self._cast.media_controller.status.player_state, states, invert=invert, fail=fail
        )
        self._cast.media_controller.register_status_listener(media_listener)
        media_listener.wait_for_states()

    def wait_for_playback_end(self):
        self.wait_for(["BUFFERING", "PLAYING"], invert=True, fail=True)

    def restore(self, data):
        raise NotImplementedError


class DefaultCastController(CastController, MediaControllerMixin, PlaybackBaseMixin):
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


class YoutubeCastController(CastController, MediaControllerMixin, PlaybackBaseMixin):
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
        self.wait_for("BUFFERING", invert=True)
        self._controller.add_to_queue(video_id)

    @catch_namespace_error
    def restore(self, data):
        self.play_media_id(data["content_id"])
        self.wait_for("PLAYING")
        self.seek(data["current_time"])
