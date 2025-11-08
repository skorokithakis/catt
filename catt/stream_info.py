import random
from pathlib import Path

import yt_dlp

from .error import ExtractionError
from .error import FormatError
from .error import PlaylistError
from .util import get_local_ip
from .util import guess_mime
from .util import echo_debug
from .util import echo_trace
from .util import echo_warning
from .util import echo_verbose

AUDIO_DEVICE_TYPES = ["audio", "group"]
# The manufacturer field is currently unavailable for Google products.
# It is still accessible via DIAL for some devices, but this resource
# is currently not being used by PyChromecast.
# See https://github.com/balloob/pychromecast/pull/197
ULTRA_MODELS = [("Xiaomi", "MIBOX3"), ("Unknown manufacturer", "Chromecast Ultra")]

BEST_MAX_2K = "best[width <=? 1920][height <=? 1080][vcodec!^=?av1][vcodec!^=?av01][vcodec!^=?vp9][vcodec!^=?h265]"
BEST_MAX_4K = "best[width <=? 3840][height <=? 2160]"
BEST_ONLY_AUDIO = "bestaudio"
BEST_FALLBACK = "/best"
MAX_50FPS = "[fps <=? 50]"
TWITCH_NO_60FPS = "[format_id !=? 1080p60__source_][format_id !=? 720p60]"
MIXCLOUD_NO_DASH_HLS = "[format_id !=? dash-a1-x3][format_id !*=? hls-6]"
BANDCAMP_NO_AIFF_ALAC = "[format_id !=? aiff-lossless][format_id !=? alac]"
AUDIO_FORMAT = (
    BEST_ONLY_AUDIO + MIXCLOUD_NO_DASH_HLS + BANDCAMP_NO_AIFF_ALAC + BEST_FALLBACK
)
ULTRA_FORMAT = BEST_MAX_4K + BANDCAMP_NO_AIFF_ALAC
STANDARD_FORMAT = BEST_MAX_2K + MAX_50FPS + TWITCH_NO_60FPS + BANDCAMP_NO_AIFF_ALAC

# DEFAULT_YTDL_OPTS depends on verbosity:
DEFAULT_YTDL_OPTS = {
    0: {"quiet": True, "no_warnings": True},
    1: {"quiet": True},
    2: {},
    3: {"verbose": True},
    4: {"verbose": True, "print_traffic": True},
}

SUBTITLE_PRIORITY = {"vtt": 30, "ttml": 20, "srt": 10}


class StreamInfo:
    def __init__(
        self,
        video_url,
        settings={},
        ytdl_options=None,
        throw_ytdl_dl_errs=False,
        stream_type=None,
    ):
        cast_info = settings.get("cast_info")
        verbosity = settings.get("verbosity", 0)
        self._throw_ytdl_dl_errs = throw_ytdl_dl_errs
        self.stream_type = stream_type
        self.local_ip = get_local_ip(cast_info.host) if cast_info else None
        self.port = random.randrange(45000, 47000) if cast_info else None
        self.media_info = {}
        self.guessed_content_type = None

        if "://" in video_url:
            self._ydl = yt_dlp.YoutubeDL(
                dict(ytdl_options) or DEFAULT_YTDL_OPTS[verbosity]
            )
            self._preinfo = self._get_stream_preinfo(video_url)
            # Some playlist urls needs to be re-processed (such as youtube channel urls).
            if self._preinfo.get("ie_key"):
                echo_verbose("Got playlist, reprocessing")
                self._preinfo = self._get_stream_preinfo(self._preinfo["url"])
            self.is_local_file = False
            if self.stream_type is None and "duration" in self._preinfo:
                if self._preinfo["duration"] is None:
                    self.stream_type = "LIVE"
                else:
                    self.stream_type = "BUFFERED"
                echo_verbose("Autoselected stream_type {}".format(self.stream_type))
            else:
                echo_verbose(
                    "Manually selected stream_type {}".format(self.stream_type)
                )
            subs = self._preinfo.get("subtitles")
            if subs:
                # YouTube (and other platforms) serves subtitles for
                # a single language in multiple formats
                # This code traverses the raw information from yt-dlp.
                for lang, formats in subs.items():
                    # Pick the best format, as decided by SUBTITLE_PRIORITY
                    # Incomptible subtitles have no entry in that dict,
                    # and get zero priority by default.
                    # If the subtitle has no defined format, assume VTT.
                    best = max(
                        formats,
                        key=lambda f: SUBTITLE_PRIORITY.get(f.get("ext", "vtt"), 0),
                    )
                    echo_debug(f"Found potential subtitles: {best}")
                    best.setdefault("ext", "vtt")
                    # Add a blank name if there is none:
                    best.setdefault("name", "")
                    # Only add the subtitle if compatible
                    # (subtitles with zero priority are discarded)
                    if SUBTITLE_PRIORITY.get(best["ext"], 0) > 0:
                        echo_verbose(
                            'Adding subtitle "{}" in {} language and {} format'.format(
                                best["name"],
                                lang,
                                best["ext"],
                            ),
                        )
                        self._add_track_to_stream(
                            {
                                "trackContentId": best["url"],
                                "language": lang,
                                "subtype": "SUBTITLES",
                                "type": "TEXT",
                                "trackContentType": guess_mime(
                                    "subtitles." + best["ext"]
                                ),
                                "name": f"[{lang}] " + best["name"],
                            }
                        )
                    else:
                        echo_debug("Discarding subtitle")

            model = (
                (cast_info.manufacturer, cast_info.model_name) if cast_info else None
            )
            cast_type = cast_info.cast_type if cast_info else None
            # If a `format` was input, CATT will assume it is valid and
            # compatible with the current ChromeCast, but will ask the user to
            # manually check if it is the case.
            # If no `format` was provided, CATT will select a default according
            # to the ChromeCast.
            if "format" in self._ydl.params:
                echo_warning(
                    "A format was provided manually. CATT will not check if the format is compatible with your device.\n"
                    + "To see the list of compatible formats and codecs, please check your device version at:\n"
                    + "\n"
                    + "https://developers.google.com/cast/docs/media\n"
                    + "\n"
                    + "CATT will select the best format for your specific device if none is provided"
                )
                self._best_format = self._ydl.params["format"]
            elif cast_type and cast_type in AUDIO_DEVICE_TYPES:
                echo_verbose("Casting audio")
                self._best_format = AUDIO_FORMAT
            elif model and model in ULTRA_MODELS:
                echo_verbose("Not casting audio. Ultra model")
                self._best_format = ULTRA_FORMAT
            else:
                echo_verbose("Not casting audio. Not an ultra model")
                self._best_format = STANDARD_FORMAT
            echo_verbose('Format selector: "{}"'.format(self._best_format))

            if self.is_playlist:
                echo_verbose("Playlist detected")
                self._entries = list(self._preinfo["entries"])
                # There appears to be no way to extract both a YouTube video id,
                # and ditto playlist id in one go (in the case of an url containing both),
                # so we set the "noplaylist" option and then fetch preinfo again.
                self._ydl.params.update({"noplaylist": True})
                vpreinfo = self._get_stream_preinfo(video_url)
                self._info = (
                    self._get_stream_info(vpreinfo)
                    if "entries" not in vpreinfo
                    else None
                )
            else:
                echo_verbose("Target is not playlist")
                self._info = self._get_stream_info(self._preinfo)
            ext = self._info.get("ext")
            echo_debug(f"yt-dlp reports extension as {ext}")
            self.guessed_content_type = guess_mime("a." + ext) if ext else None
        else:
            self._local_file = video_url
            self.is_local_file = True
            self.guessed_content_type = guess_mime(video_url)
            if self.stream_type is None:
                if (self.guessed_content_type.split("/"))[0] == "application":
                    echo_warning(
                        "Setting stream type to BUFFERED (not a live stream).\n"
                        + "\n"
                        + "This is a safe choice for the vast majority of cases.\n"
                        + "However, it is not adequate if the file is a streaming manifest pointing to a live stream.\n"
                        + "If that is the case, please run CATT with the flag `--stream-type live`"
                    )
                else:
                    echo_verbose(
                        "Stream type set automatically to BUFFERED (not a live stream)",
                    )
                self.stream_type = "BUFFERED"
        echo_verbose("guessed_content_type set to {}".format(self.guessed_content_type))

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
        return (
            self._preinfo["extractor"].split(":")[0] if not self.is_local_file else None
        )

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
        return (
            self._info["id"]
            if self.is_remote_file or self.is_playlist_with_active_entry
            else None
        )

    @property
    def video_thumbnail(self):
        return (
            self._info.get("thumbnail")
            if self.is_remote_file or self.is_playlist_with_active_entry
            else None
        )

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
            data = self._ydl.extract_info(video_url, process=False)
            echo_verbose("Running yt_dlp.extract_info()")
            echo_trace(data)
            return data
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
        echo_debug("Entering _get_stream_url()")
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

        echo_debug(f'best_format = "{best_format}"')
        return best_format["url"]

    def _add_track_to_stream(self, track):
        if self.media_info.get("tracks") is None:
            echo_debug("Initializing list of extra tracks to cast")
            self.media_info["tracks"] = []
        if track.get("trackId") is None:
            track["trackId"] = len(self.media_info["tracks"]) + 1
        echo_verbose('Adding new track to self.media_info["tracks"]')
        echo_debug(track)
        self.media_info["tracks"].append(track)
