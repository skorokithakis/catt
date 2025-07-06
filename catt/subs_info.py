import re

import requests

from .error import SubtitlesError
from .util import create_temp_file


class SubsInfo:
    """
    This class facilitates fetching/reading a remote/local subtitles file,
    converting it to webvtt if needed, and then exposing a path to a tempfile
    holding the subtitles, ready to be served.
    An url to the (expected to be) served file is also exposed.

    For local subtitle files, the url points to this computer. The variable
    self.local_subs will be True; CATT will detect this and start a web
    server so that ChromeCast can fetch it. Only devices in the same network
    can access this file.
    local_ip and port params are used for this purpose.

    If a tempfile was generated to convert it to WebVTT, this tempfile will
    be served to the ChromeCast in the same way, and self.local_subs will be
    set to True.

    If the subtitle file is remote and doesn't need to be converted, the
    url exposed will be the original url, and self.local_subs will be False.
    """

    def __init__(self, subs_url: str, local_ip: str, port: int) -> None:
        self._subs_url = subs_url
        self.local_ip = local_ip
        self.port = port
        subs, self.local_subs = self._read_subs(subs_url)
        self.file = self._subs_url
        ext = subs_url.lower().split(".")[-1]
        if ext == "srt":
            subs = self._convert_srt_to_webvtt(subs)
            self.file = create_temp_file(subs)
            self.local_subs = True

    @property
    def url(self):
        if self.local_subs:
            return "http://{}:{}/{}".format(self.local_ip, self.port, self.file)
        else:
            return self._subs_url

    def _read_subs(self, subs_url: str) -> tuple[str, bool]:
        """
        Returns:
            - a str with the url where have ChromeCast will fetch the file from
            - a bool that is True if the file will be pulled from a web server on
            this computer, and False otherwise
        """
        if "://" in subs_url:
            return self._fetch_remote_subs(subs_url), False
        else:
            return self._read_local_subs(subs_url), True

    def _convert_srt_to_webvtt(self, content: str) -> str:
        content = re.sub(
            r"^(.*? \-\-\> .*?)$",
            lambda m: m.group(1).replace(",", "."),
            content,
            flags=re.MULTILINE,
        )
        return "WEBVTT\n\n" + content

    def _read_local_subs(self, filename: str) -> str:
        for possible_encoding in ["utf-8", "iso-8859-15"]:
            try:
                with open(filename, "r", encoding=possible_encoding) as srtfile:
                    content = srtfile.read()
                    return content
            except UnicodeDecodeError:
                pass
        raise SubtitlesError(
            "Could not find the proper encoding of {}. Please convert it to utf-8".format(
                filename
            )
        )

    def _fetch_remote_subs(self, url: str) -> str:
        response = requests.get(url)
        if not response:
            raise SubtitlesError("Remote subtitles file not found")
        return response.text
