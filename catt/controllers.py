import json
import tempfile
import threading
from pathlib import Path

import pychromecast
from click import ClickException, echo

from .stream_info import StreamInfo
from .util import warning
from .youtube import YouTubeController


APP_INFO = [{"app_name": "youtube", "app_id": "233637DE", "supported_device_types": ["cast"]}]
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


def setup_cast(device_name, video_url=None, prep=None, controller=None):
    """
    Prepares selected chromecast and/or media file.

    :param device_name: Friendly name of chromecast device to use.
    :type device_name: str or NoneType
    :param video_url: If supplied, setup_cast will try to exctract a media url
                      from this, for playback or queing.
    :type video_url: str
    :param prep: If prep = "app", video_url, if supplied, is meant for playback.
                 The relevant chromecast app is started during initialization
                 of the CastController object.
                 If prep = "control", video_url, if supplied, is meant for
                 queing. The state of the selected chromecast is determined
                 during initialization of the CastController object.
                 If prep = None, no preparation is done. Should only be used
                 if the desired action can be carried out regardless of the
                 state of the chromecast (like volume adjustment).
    :type prep: str
    :param controller: If supplied, the normal logic for determining the appropriate
                       controller is bypassed, and the one specified here is
                       returned instead.
    :type controller: str
    :returns: controllers.DefaultCastController or controllers.YoutubeCastController,
              and stream_info.StreamInfo if video_url is supplied.
    """

    cache = Cache()
    cached_ip = cache.get_data(device_name)
    stream = None

    try:
        if not cached_ip:
            raise ValueError
        cast = pychromecast.Chromecast(cached_ip)
    except (pychromecast.error.ChromecastConnectionError, ValueError):
        cast = get_chromecast(device_name)
        cache.set_data(cast.name, cast.host)
    cast.wait()

    if video_url:
        cc_info = (cast.device.manufacturer, cast.model_name)
        stream = StreamInfo(video_url, model=cc_info, host=cast.host)

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

    if (not controller and app["app_name"] != "default" and
            cast.cast_type not in app["supported_device_types"]):
        if stream:
            warning("The %s app is not available for this device." % app["app_name"].capitalize())
        app = DEFAULT_APP

    if app["app_name"] == "youtube":
        controller = YoutubeCastController(cast, app["app_name"], app["app_id"], prep=prep)
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


class PlaybackError(Exception):
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

    def set_data(self, name, value):
        data = self._read_store()
        data[name] = value
        self._write_store(data)

    def clear(self):
        try:
            self.store_path.unlink()
            self.store_path.parent.rmdir()
        except FileNotFoundError:
            pass


class Cache(CattStore):
    def __init__(self):
        cache_path = Path(tempfile.gettempdir(), "catt_cache", "chromecast_hosts")
        super(Cache, self).__init__(cache_path)
        self._create_store_dir()

        if not self.store_path.exists():
            devices = pychromecast.get_chromecasts()
            self._write_store({d.name: d.host for d in devices})

    def get_data(self, name):
        data = self._read_store()
        # In the case that cache has been initialized with no cc's on the
        # network, we need to ensure auto-discovery.
        if not data:
            return None
        # When the user does not specify a device, we need to make an attempt
        # to consistently return the same IP, thus the alphabetical sorting.
        if not name:
            return data[min(data, key=str)]
        return data.get(name)


class CastState(CattStore):
    def __init__(self, state_path, create_dir=False):
        super(CastState, self).__init__(state_path)
        if create_dir:
            self._create_store_dir()
        if not self.store_path.exists():
            self._write_store({})

    def get_data(self, name):
        try:
            data = self._read_store()
            if set(next(iter(data.values())).keys()) != set(["controller", "data"]):
                raise ValueError
        except (json.decoder.JSONDecodeError,
                ValueError, StopIteration, AttributeError):
            raise StateFileError
        return data.get(name)


class CastStatusListener:
    def __init__(self, app_id, active_app_id):
        self.app_id = app_id
        self.app_ready = threading.Event()
        if app_id == active_app_id:
            self.app_ready.set()

    def new_cast_status(self, status):
        if status.app_id == self.app_id:
            self.app_ready.set()
        else:
            self.app_ready.clear()


class MediaStatusListener:
    def __init__(self, state):
        self.not_buffering = threading.Event()
        self.playing = threading.Event()
        if state != "BUFFERING":
            self.not_buffering.set()
        elif state == "PLAYING":
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
        return {"title": status.title,
                "content_id": status.content_id,
                "current_time": status.current_time if self._is_seekable else None,
                "thumb": status.images[0].url if status.images else None}

    @property
    def cast_info(self):
        status = self._cast.media_controller.status
        cinfo = self.media_info

        if self._is_seekable:
            duration, current = status.duration, status.current_time
            remaining = duration - current
            progress = int((1.0 * current / duration) * 100)
            cinfo.update({"duration": duration,
                          "remaining": remaining, "progress": progress})

        cinfo.update({"player_state": status.player_state,
                      "volume_level": str(int(round(self._cast.status.volume_level, 2) * 100))})
        return cinfo

    @property
    def is_streaming_local_file(self):
        status = self._cast.media_controller.status
        return True if status.content_id.endswith("?loaded_from_catt") else False

    @property
    def _is_seekable(self):
        status = self._cast.media_controller.status
        return True if (status.duration and
                        status.stream_type == "BUFFERED") else False

    def _prep_app(self):
        """Make shure desired chromecast app is running."""

        if not self._cast_listener.app_ready.is_set():
            self._cast.start_app(self._cast_listener.app_id)
            self._cast_listener.app_ready.wait()

    def _prep_control(self):
        """Make shure chromecast is in an active state."""

        if self._cast.app_id == BACKDROP_APP_ID or not self._cast.app_id:
            raise CattCastError("Chromecast is inactive.")
        self._cast.media_controller.block_until_active(1.0)
        if self._cast.media_controller.status.player_state in ["UNKNOWN", "IDLE"]:
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
        raise PlaybackError

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

        if (idle_only and
                self._cast.media_controller.status.player_state not in ["UNKNOWN", "IDLE"]):
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
        self.save_capability = "complete" if (self._is_seekable and
                                              self._cast.app_id == DEFAULT_APP["app_id"]) else None

    def play_media_url(self, video_url, **kwargs):
        self._controller.play_media(video_url, "video/mp4",
                                    current_time=kwargs.get("current_time"),
                                    title=kwargs.get("title"), thumb=kwargs.get("thumb"))
        self._controller.block_until_active()

    def restore(self, data):
        self.play_media_url(data["content_id"], current_time=data["current_time"],
                            title=data["title"], thumb=data["thumb"])


class YoutubeCastController(CastController):
    def __init__(self, cast, name, app_id, prep=None):
        self._controller = YouTubeController()
        super(YoutubeCastController, self).__init__(cast, name, app_id, prep=prep)
        self.info_type = "id"
        self.save_capability = "partial"

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
        echo("Adding video id \"%s\" to the queue." % video_id)
        self._prep_yt(video_id)
        # You can't add videos to the queue while the app is buffering.
        self._media_listener.not_buffering.wait()
        self._controller.add_to_queue(video_id)

    @catch_namespace_error
    def restore(self, data):
        self.play_media_id(data["content_id"])
        self._media_listener.playing.wait()
        self.seek(data["current_time"])
