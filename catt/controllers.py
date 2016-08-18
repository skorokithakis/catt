import os
import time
import youtube_dl
import pychromecast
import shutil
import tempfile
from click import echo


def get_stream_info(video_url):
    ydl = youtube_dl.YoutubeDL({})
    info = ydl.extract_info(video_url, download=False)
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


class Cache:
    def __init__(self, cache_dir=os.path.join(tempfile.gettempdir(), "catt_cache/")):
        self.cache_dir = cache_dir
        try:
            os.mkdir(cache_dir)
        except:
            pass

    def _get_cache_filename(self, key):
        return os.path.join(self.cache_dir, key)

    def get(self, key, duration):
        cache_filename = self._get_cache_filename(key)
        if os.path.exists(cache_filename):
            if os.path.getctime(cache_filename) + duration > time.time():
                return open(cache_filename).read()
            else:
                os.remove(cache_filename)
        else:
            return None

    def set(self, key, value):
        open(self._get_cache_filename(key), "w").write(value)

    def clear(self):
        try:
            shutil.rmtree(self.cache_dir)
        except:
            pass


class CastController:
    def __init__(self):
        cache = Cache()

        cached_chromecast = cache.get("chromecast_host", 3 * 24 * 3600)
        if cached_chromecast:
            self.cast = pychromecast.Chromecast(cached_chromecast)
        else:
            self.cast = pychromecast.get_chromecast()
            cache.set("chromecast_host", self.cast.host)
        time.sleep(0.2)

    def play_media(self, url, content_type="video/mp4"):
        NON_BLOCKING_APPS = ['Backdrop', 'Default Media Receiver',
                             'BubbleUPnP']
        if self.cast.app_display_name not in NON_BLOCKING_APPS:
            self.kill()
            while self.cast.app_display_name != 'Backdrop':
                time.sleep(1)
        self.cast.play_media(url, content_type)

    def play(self):
        self.cast.media_controller.play()

    def pause(self):
        self.cast.media_controller.pause()

    def stop(self):
        self.cast.media_controller.stop()

    def seek(self, seconds):
        self.cast.media_controller.seek(int(seconds))

    def rewind(self, seconds):
        pos = self.cast.media_controller.status.current_time
        self.seek(pos - seconds)

    def ffwd(self, seconds):
        pos = self.cast.media_controller.status.current_time
        self.seek(pos + seconds)

    def volume(self, level):
        self.cast.set_volume(level)

    def volumeup(self):
        self.cast.volume_up()

    def volumedown(self):
        self.cast.volume_down()

    def status(self):
        status = self.cast.media_controller.status.__dict__
        if not status["duration"]:
            echo("Nothing currently playing.")
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
