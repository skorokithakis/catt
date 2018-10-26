from .controllers import get_app_info, get_cast, get_cast_with_ip, get_chromecasts, get_controller, get_stream


def discover():
    return [CattDevice(d.name, d.host) for d in get_chromecasts(fail=False)]


class CattDevice:
    def __init__(self, name=None, ip=None, lazy=False):
        self.name = name
        self.ip = ip

        self._cast = None
        self._cast_controller = None
        if not lazy:
            self._create_cast()

    def __repr__(self):
        return "<CattDevice: %s>" % (self.name or self.ip)

    def _create_cast(self):
        if self._cast:
            return
        self._cast = get_cast_with_ip(self.ip) if self.ip else get_cast(self.name, use_cache=False)
        self.name = self._cast.name

    def _create_controller(self, prep=None):
        self._create_cast()
        if self._cast_controller:
            return
        self._cast_controller = get_controller(self._cast, get_app_info("default"), prep=prep)

    def play_url(self, url, resolve=False):
        self._create_controller(prep="app")
        if resolve:
            stream = get_stream(url)
            url = stream.video_url
        self._cast_controller.play_media_url(url)

    def stop(self):
        self._create_controller()
        self._cast.quit_app()
