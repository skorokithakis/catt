from .controllers import (
    get_app_info,
    get_chromecast,
    get_chromecast_with_ip,
    get_chromecasts,
    get_controller,
    get_stream,
)


def discover() -> list:
    """Perform discovery of devices present on local network, and return result."""

    return [CattDevice(ipaddr=d.host) for d in get_chromecasts()]


class CattAPIError(Exception):
    pass


class CattDevice:
    def __init__(self, name: str = "", ipaddr: str = "", lazy: bool = False) -> None:
        """
        Class to easily interface with a ChromeCast.

        :param name: Name of ChromeCast device to interface with.
                     Either name of ip-address must be supplied.
        :param ipaddr: Ip-address of device to interface with.
                       Either name of ip-address must be supplied.
        :param lazy: Postpone first connection attempt to device
                     until first playback action is attempted.
        """

        if not name and not ipaddr:
            raise CattAPIError("neither name nor ip were supplied")
        self.name = name
        self.ipaddr = ipaddr

        self._cast = None
        self._cast_controller = None
        if not lazy:
            self._create_cast()

    def __repr__(self) -> str:
        return "<CattDevice: %s>" % (self.name or self.ipaddr)

    def _create_cast(self) -> None:
        self._cast = get_chromecast_with_ip(self.ipaddr) if self.ipaddr else get_chromecast(self.name)
        if not self._cast:
            raise CattAPIError("device could not be found")
        self._cast.wait()
        self.name = self._cast.name
        self.ipaddr = self._cast.host

    def _create_ctrl(self) -> None:
        self._cast_controller = get_controller(self._cast, get_app_info("default"))

    @property
    def ctrl(self):
        if not self._cast:
            self._create_cast()
        if not self._cast_controller:
            self._create_ctrl()
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
        self.ctrl.prep_app()
        self.ctrl.play_media_url(url)

        if self.ctrl.wait_for(["PLAYING"], timeout=10):
            if block:
                self.ctrl.wait_for(["UNKNOWN", "IDLE"])
        else:
            raise CattAPIError("playback failed")

    def stop(self) -> None:
        """Stop playback."""

        self.ctrl.kill()

    def play(self) -> None:
        """Resume playback of paused content."""

        self.ctrl.prep_control()
        self.ctrl.play()

    def pause(self) -> None:
        """Pause playback of content."""

        self.ctrl.prep_control()
        self.ctrl.pause()

    def seek(self, seconds: int) -> None:
        """
        Seek to arbitrary position in content.

        :param seconds: Position in seconds.
        """

        self.ctrl.prep_control()
        self.ctrl.seek(seconds)

    def rewind(self, seconds: int) -> None:
        """
        Seek backwards in content by arbitrary amount of seconds.

        :param seconds: Seek amount in seconds.
        """

        self.ctrl.prep_control()
        self.ctrl.rewind(seconds)

    def ffwd(self, seconds: int) -> None:
        """
        Seek forward in content by arbitrary amount of seconds.

        :param seconds: Seek amount in seconds.
        """

        self.ctrl.prep_control()
        self.ctrl.ffwd(seconds)

    def volume(self, level: float) -> None:
        """
        Set volume to arbitrary level.

        :param level: Volume level (valid range: 0.0-1.0).
        """
        self.ctrl.volume(level)

    def volumeup(self, delta: float) -> None:
        """
        Raise volume by arbitrary delta.

        :param delta: Volume delta (valid range: 0.0-1.0).
        """
        self.ctrl.volumeup(delta)

    def volumedown(self, delta: float) -> None:
        """
        Lower volume by arbitrary delta.

        :param delta: Volume delta (valid range: 0.0-1.0).
        """

        self.ctrl.volumedown(delta)
