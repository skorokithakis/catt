import re

import requests

from .error import SubtitlesError
from .util import create_temp_file
from .util import guess_mime


class SubsInfo:
    """
    This class facilitates fetching/reading a remote/local subtitles file,
    converting it to webvtt if needed, and then exposing a path to a tempfile
    holding the subtitles, ready to be served.
    An url to the (expected to be) served file is also exposed.

    This class accepts the following input:
        - subs_url: a string with the location of the subtitles.
        - local_ip: a string with the IP for this computer (to be used only if
          the subtitles file is in this computer, and not on the internet)
        - port: an integer with the port where a web server will be opened
          (again, if and only if the subtitles file is in this computer)

    Three variables are defined after the subtitles file is retrieved:
        - mimetype: a string with the MIME type of the subtitles.
        - local_subs: a Boolean that is True if the subtitles file is in this
          computer, False otherwise.
        - file: a variable representing the subtitles file itself.

    For local subtitle files, _read_subs() returns a blank MIME type.
    local_subs is then set to True, and the MIME type is inferred from the file
    extension. Then, after checking the value of local_subs, CATT will start a
    web server in this computer so that ChromeCast can fetch the subtitles.
    Only devices in the same network can access this file.

    Subtitle files in SubRip format (.SRT application/x-subrip) will be
    converted locally to WebVTT format. This converted file will be served to
    the ChromeCast, and treated like any local file.

    If the subtitle file is remote and doesn't need to be converted, subs_url
    will be the original url, local_subs will be False, and the MIME type will
    be retrieved directly from the web server.
    """

    def __init__(self, subs_url: str, local_ip: str, port: int) -> None:
        self._subs_url = subs_url
        self.local_ip = local_ip
        self.port = port
        subs, self.mimetype = self._read_subs(subs_url)
        if self.mimetype == "":
            self.local_subs = True
            self.mimetype = guess_mime(subs_url)
        else:
            self.local_subs = False
        self.file = self._subs_url
        if "application/x-subrip" in self.mimetype:
            subs = self._convert_srt_to_webvtt(subs)
            self.file = create_temp_file(subs)
            self.local_subs = True

    @property
    def url(self) -> str:
        if self.local_subs:
            return "http://{}:{}/{}".format(self.local_ip, self.port, self.file)
        else:
            return self._subs_url

    def _read_subs(self, subs_url: str) -> tuple[str, str]:
        """
        Returns:
            - a str with the url where have ChromeCast will fetch the file from
            - a bool that is True if the file will be pulled from a web server on
            this computer, and False otherwise
        """
        if "://" in subs_url:
            return self._fetch_remote_subs(subs_url)
        else:
            return self._read_local_subs(subs_url)

    def _convert_srt_to_webvtt(self, content: str) -> str:
        content = re.sub(
            r"^(.*? \-\-\> .*?)$",
            lambda m: m.group(1).replace(",", "."),
            content,
            flags=re.MULTILINE,
        )
        return "WEBVTT\n\n" + content

    def _read_local_subs(self, filename: str) -> tuple[str, str]:
        for possible_encoding in ["utf-8", "iso-8859-15"]:
            try:
                with open(filename, "r", encoding=possible_encoding) as srtfile:
                    content = srtfile.read()
                    return content, ""
            except UnicodeDecodeError:
                pass
        raise SubtitlesError(
            "Could not find the proper encoding of {}. Please convert it to utf-8".format(
                filename
            )
        )

    def _fetch_remote_subs(self, url: str) -> tuple[str, str]:
        response = requests.get(url)
        if not response:
            raise SubtitlesError("Remote subtitles file not found")
        return response.text, response.headers["content-type"]
