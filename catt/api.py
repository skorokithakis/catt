from .controllers import get_app, get_chromecast, get_chromecast_with_ip, get_chromecasts, get_controller, get_stream
from .error import APIError, CastError


def discover() -> list:
    """Perform discovery of devices present on local network, and return result."""

    return [CattDevice(ip_addr=d.host) for d in get_chromecasts()]


class CattDevice:
    def __init__(self, name: str = "", ip_addr: str = "", lazy: bool = False) -> None:
        """
        Class to easily interface with a ChromeCast.

        :param name: Name of ChromeCast device to interface with.
                     Either name of ip-address must be supplied.
        :param ip_addr: Ip-address of device to interface with.
                       Either name of ip-address must be supplied.
        :param lazy: Postpone first connection attempt to device
                     until first playback action is attempted.
        """

        if not name and not ip_addr:
            raise APIError("Neither name nor ip were supplied")

        self.name = name
        self.ip_addr = ip_addr
        self.uuid = None

        self._cast = None
        self._cast_controller = None
        if not lazy:
            self._create_cast()

    def __repr__(self) -> str:
        return "<CattDevice: %s>" % (self.name or self.ip_addr)

    def _create_cast(self) -> None:
        self._cast = get_chromecast_with_ip(self.ip_addr) if self.ip_addr else get_chromecast(self.name)
        if not self._cast:
            raise CastError("Device could not be found")
        self._cast.wait()

        self.name = self._cast.name
        self.ip_addr = self._cast.host
        self.uuid = self._cast.uuid

    def _create_controller(self) -> None:
        self._cast_controller = get_controller(self._cast, get_app("default"))

    @property
    def controller(self):
        if not self._cast:
            self._create_cast()
        if not self._cast_controller:
            self._create_controller()
        return self._cast_controller

    def play_url(self, url: str, resolve: bool = False, block: bool = False) -> None:
        """
        Initiate playback of content.

        :param url: Network location of content.
        :param resolve: Try to resolve location of content stream with Youtube-dl.
                        If this is not set, it is assumed that the url points directly to the stream.
        :param block: Block until playback has stopped,
                      either by end of content being reached, or by interruption.
        """

        if resolve:
            stream = get_stream(url)
            url = stream.video_url
        self.controller.prep_app()
        self.controller.play_media_url(url)

        if self.controller.wait_for(["PLAYING"], timeout=10):
            if block:
                self.controller.wait_for(["UNKNOWN", "IDLE"])
        else:
            raise APIError("Playback failed")

    def stop(self) -> None:
        """Stop playback."""

        self.controller.kill()

    def play(self) -> None:
        """Resume playback of paused content."""

        self.controller.prep_control()
        self.controller.play()

    def pause(self) -> None:
        """Pause playback of content."""

        self.controller.prep_control()
        self.controller.pause()

    def seek(self, seconds: int) -> None:
        """
        Seek to arbitrary position in content.

        :param seconds: Position in seconds.
        """

        self.controller.prep_control()
        self.controller.seek(seconds)

    def rewind(self, seconds: int) -> None:
        """
        Seek backwards in content by arbitrary amount of seconds.

        :param seconds: Seek amount in seconds.
        """

        self.controller.prep_control()
        self.controller.rewind(seconds)

    def ffwd(self, seconds: int) -> None:
        """
        Seek forward in content by arbitrary amount of seconds.

        :param seconds: Seek amount in seconds.
        """

        self.controller.prep_control()
        self.controller.ffwd(seconds)

    def volume(self, level: float) -> None:
        """
        Set volume to arbitrary level.

        :param level: Volume level (valid range: 0.0-1.0).
        """
        self.controller.volume(level)

    def volumeup(self, delta: float) -> None:
        """
        Raise volume by arbitrary delta.

        :param delta: Volume delta (valid range: 0.0-1.0).
        """
        self.controller.volumeup(delta)

    def volumedown(self, delta: float) -> None:
        """
        Lower volume by arbitrary delta.

        :param delta: Volume delta (valid range: 0.0-1.0).
        """

        self.controller.volumedown(delta)
