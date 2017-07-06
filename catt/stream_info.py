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
        if "://" not in video_url:
            if not os.path.isfile(video_url):
                raise CattInfoError("The chosen file does not exist.")

            self._video_url = video_url
            self.local_ip = get_local_ip(host)
            self.port = random.randrange(45000, 47000)
            self.is_local_file = True
        else:
            self._ydl = youtube_dl.YoutubeDL({"quiet": True, "no_warnings": True})
            self._preinfo = self._get_stream_preinfo(video_url)
            self.local_ip = None
            self.port = None
            self.is_local_file = False

            if self.is_playlist:
                items = list(self._preinfo["entries"])
                self._entries_first_item = items[0]

                # For non-supported playlists, we are obtaining "info" for
                # first video only.
                if self.is_youtube_playlist:
                    self._playlist_items = [item["id"] for item in items]
                else:
                    self._info = self._get_stream_info(self._entries_first_item)
            else:
                self._info = self._get_stream_info(self._preinfo)

    @property
    def title(self):
        if self.is_local_file:
            return os.path.basename(self._video_url)
        # For non-supported playlists, we are returning
        # the title of the first video.
        elif self.is_playlist and not self.is_youtube_playlist:
            return self._info["title"]
        else:
            # "preinfo" does not contain a "title" key, when the user casts
            # an url that points directly to a media file.
            try:
                return self._preinfo["title"]
            except KeyError:
                return self._preinfo["webpage_url_basename"]

    @property
    def video_url(self):
        if self.is_local_file:
            return "http://%s:%s/" % (self.local_ip, self.port)
        elif self.is_youtube_playlist:
            # We are doing this, so that we can avoid calling _get_stream_info
            # in the contructor, when the user is casting a YouTube playlist
            # to a non-audio device (where "info" is not needed).
            # The below return statement is only used when the user tries to
            # cast a YouTube playlist to an audio device.
            return self._get_stream_url(self._get_stream_info(self._entries_first_item))
        else:
            return self._get_stream_url(self._info)

    @property
    def video_id(self):
        if self.is_youtube_video:
            return self._preinfo["id"]
        elif self.is_youtube_playlist:
            return self._playlist_items[0]
        else:
            return None

    @property
    def playlist(self):
        return self._playlist_items if self.is_youtube_playlist else None

    @property
    def playlist_id(self):
        return self._preinfo["id"] if self.is_youtube_playlist else None

    @property
    def is_youtube_video(self):
        if not self.is_local_file:
            return True if self._preinfo["extractor"] == "youtube" else False
        else:
            return False

    @property
    def is_youtube_playlist(self):
        if not self.is_local_file:
            return True if self._preinfo["extractor"] == "youtube:playlist" else False
        else:
            return False

    @property
    def is_playlist(self):
        if not self.is_local_file:
            return True if "entries" in self._preinfo else False
        else:
            return False

    def _get_stream_preinfo(self, video_url):
        try:
            return self._ydl.extract_info(video_url, process=False)
        except youtube_dl.utils.DownloadError:
            raise CattInfoError("Remote resource not found.")

    def _get_stream_info(self, preinfo):
        try:
            return self._ydl.process_ie_result(preinfo, download=False)
        except (youtube_dl.utils.ExtractorError, youtube_dl.utils.DownloadError):
            raise CattInfoError("Youtube-dl extractor failed.")

    def _get_stream_url(self, info):
        format_selector = self._ydl.build_format_selector("best")

        try:
            best_format = list(format_selector(info))[0]
        except KeyError:
            best_format = info

        return best_format["url"]
