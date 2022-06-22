import random
from pathlib import Path

import yt_dlp

from .error import ExtractionError
from .error import FormatError
from .error import PlaylistError
from .util import get_local_ip
from .util import guess_mime

AUDIO_DEVICE_TYPES = ["audio", "group"]
# The manufacturer field is currently unavailable for Google products.
# It is still accessible via DIAL for some devices, but this resource
# is currently not being used by PyChromecast.
# See https://github.com/balloob/pychromecast/pull/197
ULTRA_MODELS = [("Xiaomi", "MIBOX3"), ("Unknown manufacturer", "Chromecast Ultra")]

BEST_MAX_2K = "best[width <=? 1920][height <=? 1080]"
BEST_MAX_4K = "best[width <=? 3840][height <=? 2160]"
BEST_ONLY_AUDIO = "bestaudio"
BEST_FALLBACK = "/best"
MAX_50FPS = "[fps <=? 50]"
TWITCH_NO_60FPS = "[format_id != 1080p60__source_][format_id != 720p60]"
MIXCLOUD_NO_DASH_HLS = "[format_id != dash-a1-x3][format_id !*= hls-6]"
BANDCAMP_NO_AIFF_ALAC = "[format_id != aiff-lossless][format_id != alac]"
AUDIO_FORMAT = BEST_ONLY_AUDIO + MIXCLOUD_NO_DASH_HLS + BANDCAMP_NO_AIFF_ALAC + BEST_FALLBACK
ULTRA_FORMAT = BEST_MAX_4K + BANDCAMP_NO_AIFF_ALAC
STANDARD_FORMAT = BEST_MAX_2K + MAX_50FPS + TWITCH_NO_60FPS + BANDCAMP_NO_AIFF_ALAC

DEFAULT_YTDL_OPTS = {"quiet": True, "no_warnings": True}


class StreamInfo:
    def __init__(self, video_url, cast_info=None, ytdl_options=None, throw_ytdl_dl_errs=False):
        self._throw_ytdl_dl_errs = throw_ytdl_dl_errs
        self.local_ip = get_local_ip(cast_info.host) if cast_info else None
        self.port = random.randrange(45000, 47000) if cast_info else None

        if "://" in video_url:
            self._ydl = yt_dlp.YoutubeDL(dict(ytdl_options) if ytdl_options else DEFAULT_YTDL_OPTS)
            self._preinfo = self._get_stream_preinfo(video_url)
            # Some playlist urls needs to be re-processed (such as youtube channel urls).
            if self._preinfo.get("ie_key"):
                self._preinfo = self._get_stream_preinfo(self._preinfo["url"])
            self.is_local_file = False

            model = (cast_info.manufacturer, cast_info.model_name) if cast_info else None
            cast_type = cast_info.cast_type if cast_info else None
            if "format" in self._ydl.params:
                # We pop the "format" item, as it will make get_stream_info fail,
                # if it holds an invalid value.
                self._best_format = self._ydl.params.pop("format")
            elif cast_type and cast_type in AUDIO_DEVICE_TYPES:
                self._best_format = AUDIO_FORMAT
            elif model and model in ULTRA_MODELS:
                self._best_format = ULTRA_FORMAT
            else:
                self._best_format = STANDARD_FORMAT

            if self.is_playlist:
                self._entries = list(self._preinfo["entries"])
                # There appears to be no way to extract both a YouTube video id,
                # and ditto playlist id in one go (in the case of an url containing both),
                # so we set the "noplaylist" option and then fetch preinfo again.
                self._ydl.params.update({"noplaylist": True})
                vpreinfo = self._get_stream_preinfo(video_url)
                self._info = self._get_stream_info(vpreinfo) if "entries" not in vpreinfo else None
            else:
                self._info = self._get_stream_info(self._preinfo)
        else:
            self._local_file = video_url
            self.is_local_file = True

    @property
    def is_remote_file(self):
        return not self.is_local_file and not self.is_playlist

    @property
    def _is_direct_link(self):
        return self.is_remote_file and self._info.get("direct")

    @property
    def is_playlist(self):
        return not self.is_local_file and "entries" in self._preinfo

    @property
    def is_playlist_with_active_entry(self):
        return self.is_playlist and self._info

    @property
    def extractor(self):
        return self._preinfo["extractor"].split(":")[0] if not self.is_local_file else None

    @property
    def video_title(self):
        if self.is_local_file:
            return Path(self._local_file).stem
        elif self._is_direct_link:
            return Path(self._preinfo["webpage_url_basename"]).stem
        elif self.is_remote_file or self.is_playlist_with_active_entry:
            return self._info["title"]
        else:
            return None

    @property
    def video_url(self):
        if self.is_local_file:
            return "http://{}:{}/?loaded_from_catt".format(self.local_ip, self.port)
        elif self.is_remote_file or self.is_playlist_with_active_entry:
            return self._get_stream_url(self._info)
        else:
            return None

    @property
    def video_id(self):
        return self._info["id"] if self.is_remote_file or self.is_playlist_with_active_entry else None

    @property
    def video_thumbnail(self):
        return self._info.get("thumbnail") if self.is_remote_file or self.is_playlist_with_active_entry else None

    @property
    def guessed_content_type(self):
        if self.is_local_file:
            return guess_mime(Path(self._local_file).name)
        elif self._is_direct_link:
            return guess_mime(self._info["webpage_url_basename"])
        else:
            return None

    @property
    def guessed_content_category(self):
        content_type = self.guessed_content_type
        return content_type.split("/")[0] if content_type else None

    @property
    def playlist_length(self):
        return len(self._entries) if self.is_playlist else None

    @property
    def playlist_all_ids(self):
        if self.is_playlist and self._entries and self._entries[0].get("id"):
            return [entry["id"] for entry in self._entries]
        else:
            return None

    @property
    def playlist_title(self):
        return self._preinfo["title"] if self.is_playlist else None

    @property
    def playlist_id(self):
        return self._preinfo["id"] if self.is_playlist else None

    def set_playlist_entry(self, number):
        if self.is_playlist:
            # Some playlist entries needs to be re-processed.
            if self._entries[number].get("ie_key"):
                entry = self._get_stream_preinfo(self._entries[number]["url"])
            else:
                entry = self._entries[number]
            self._info = self._get_stream_info(entry)
        else:
            raise PlaylistError("Called on non-playlist")

    def _get_stream_preinfo(self, video_url):
        try:
            return self._ydl.extract_info(video_url, process=False)
        except yt_dlp.utils.DownloadError:
            # We sometimes get CI failures when testing with YouTube videos,
            # as YouTube throttles our connections intermittently. We evaluated
            # various solutions and the one we agreed on was ignoring the specific
            # "Too many requests" exceptions when testing.
            # To do that, we needed a way to raise exceptions instead of swallowing
            # them, so we could ignore the ones we didn't need in the tests. This
            # property is the way to do that.
            if self._throw_ytdl_dl_errs:
                raise
            else:
                raise ExtractionError("Remote resource not found")

    def _get_stream_info(self, preinfo):
        try:
            return self._ydl.process_ie_result(preinfo, download=False)
        except (yt_dlp.utils.ExtractorError, yt_dlp.utils.DownloadError):
            raise ExtractionError("yt-dlp extractor failed")

    def _get_stream_url(self, info):
        try:
            format_selector = self._ydl.build_format_selector(self._best_format)
        except ValueError:
            raise FormatError("The specified format filter is invalid")

        info.setdefault("incomplete_formats", {})
        try:
            best_format = next(format_selector(info))
        except StopIteration:
            raise FormatError("No suitable format was found")
        # This is thrown when url points directly to media file.
        except KeyError:
            best_format = info

        return best_format["url"]
