import os
import random
import socket

import click
import youtube_dl


def get_local_ip(cc_host):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect((cc_host, 0))
    return sock.getsockname()[0]


class CattInfoError(click.ClickException):
    pass


class StreamInfo:
    def __init__(self, video_url, host):
        self.ydl = youtube_dl.YoutubeDL({"quiet": True, "no_warnings": True})

        if "://" not in video_url:
            if not os.path.isfile(video_url):
                raise CattInfoError("The chosen file does not exist.")

            self._info = None
            self.local_ip = get_local_ip(host)
            self.port = random.randrange(45000, 47000)
            self.title = os.path.basename(video_url)
            self.video_id = None
            self.is_local_file = True
        else:
            self._info = self._get_stream_info(video_url)
            self.local_ip = None
            self.port = None
            self.title = self._info["title"]
            self.video_id = self._info["id"]
            self.is_local_file = False

    @property
    def url(self):
        if self.is_local_file:
            return "http://%s:%s/" % (self.local_ip, self.port)
        else:
            return self._get_stream_url(self._info)

    @property
    def is_youtube_video(self):
        if self._info:
            return True if self._info["extractor"] == "youtube" else False
        else:
            return False

    @property
    def is_youtube_playlist(self):
        if self._info:
            return True if self._info["extractor"] == "youtube:playlist" else False
        else:
            return False

    def _get_stream_info(self, video_url):
        try:
            return self.ydl.extract_info(video_url, process=False)
        except youtube_dl.utils.DownloadError:
            raise CattInfoError("Remote resource not found.")

    def _get_stream_url(self, preinfo):
        try:
            info = self.ydl.process_ie_result(preinfo, download=False)
        except (youtube_dl.utils.ExtractorError, youtube_dl.utils.DownloadError):
            raise CattInfoError("Youtube-dl extractor failed.")

        format_selector = self.ydl.build_format_selector("best")

        try:
            best_format = list(format_selector(info))[0]
        except KeyError:
            best_format = info

        return best_format["url"]
