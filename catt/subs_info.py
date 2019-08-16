import re

import requests

from .error import SubtitlesError
from .util import create_temp_file


class SubsInfo:
    def __init__(self, subs_url: str, local_ip: str, port: int) -> None:
        self._subs_url = subs_url
        self.local_ip = local_ip
        self.port = port
        subs = self._read_subs(subs_url)
        ext = subs_url.lower().split(".")[-1]

        if ext == "srt":
            subs = self._convert_srt_to_webvtt(subs)
        self.file = create_temp_file(subs)

    @property
    def url(self):
        return "http://{}:{}/{}".format(self.local_ip, self.port, self.file)

    def _read_subs(self, subs_url: str) -> str:
        if "://" in subs_url:
            return self._fetch_remote_subs(subs_url)
        else:
            return self._read_local_subs(subs_url)

    def _convert_srt_to_webvtt(self, content: str) -> str:
        content = re.sub(r"^(.*? \-\-\> .*?)$", lambda m: m.group(1).replace(",", "."), content, flags=re.MULTILINE)
        return "WEBVTT\n\n" + content

    def _read_local_subs(self, filename: str) -> str:
        for possible_encoding in ["utf-8", "iso-8859-15"]:
            try:
                with open(filename, "r", encoding=possible_encoding) as srtfile:
                    content = srtfile.read()
                    return content
            except UnicodeDecodeError:
                pass
        raise SubtitlesError("Could not find the proper encoding of {}. Please convert it to utf-8".format(filename))

    def _fetch_remote_subs(self, url: str) -> str:
        response = requests.get(url)
        if not response:
            raise SubtitlesError("Remote subtitles file not found")
        return response.text
