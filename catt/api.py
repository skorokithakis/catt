from .controllers import get_app_info, get_cast, get_cast_with_ip, get_chromecasts, get_controller, get_stream


def discover():
    return [CattDevice(d.name, d.host) for d in get_chromecasts(fail=False)]


class CattDevice:
    def __init__(self, name=None, ipaddr=None, lazy=False):
        self.name = name
        self.ipaddr = ipaddr

        self._cast = None
        self._cast_controller = None
        if not lazy:
            self._create_cast()

    def __repr__(self):
        return "<CattDevice: %s>" % (self.name or self.ipaddr)

    def _create_cast(self):
        self._cast = get_cast_with_ip(self.ipaddr) if self.ipaddr else get_cast(self.name, use_cache=False)
        self.name = self._cast.name
        self.ipaddr = self._cast.host

    def _create_ctrl(self):
        self._cast_controller = get_controller(self._cast, get_app_info("default"))

    @property
    def cst(self):
        if not self._cast:
            self._create_cast()
        return self._cast

    @property
    def ctrl(self):
        if not self._cast:
            self._create_cast()
        elif not self._cast_controller:
            self._create_ctrl()
        return self._cast_controller

    def play_url(self, url, resolve=False):
        if resolve:
            stream = get_stream(url)
            url = stream.video_url
        self.ctrl.prep_app()
        self.ctrl.play_media_url(url)

    def stop(self):
        self.cst.quit_app()
