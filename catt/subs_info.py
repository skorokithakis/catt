import re

import requests

from .error import SubtitlesError
from .util import create_temp_file


class SubsInfo:
    def __init__(self, subs_url, local_ip, port):
        self._subs_url = subs_url
        self._local_ip = local_ip
        self.port = port

        ext = subs_url.lower().split(".")[-1]
        if "://" in subs_url:
            if ext == "srt":
                conv_subs = self._convert_srt_to_webvtt(self._fetch_remote_subs(subs_url))
                self.file = create_temp_file(conv_subs)
            else:
                self.file = create_temp_file(self._fetch_remote_subs(subs_url))
        else:
            if ext == "srt":
                conv_subs = self._convert_srt_to_webvtt(self._read_srt_subs(subs_url))
                self.file = create_temp_file(conv_subs)
            else:
                self.file = subs_url

    @property
    def url(self):
        return "http://{}:{}/{}".format(self._local_ip, self.port, self.file)

    def _convert_srt_to_webvtt(self, content):
        content = re.sub(r"^(.*? \-\-\> .*?)$", lambda m: m.group(1).replace(",", "."), content, flags=re.MULTILINE)
        return "WEBVTT\n\n" + content

    def _read_srt_subs(self, filename):
        for possible_encoding in ["utf-8", "iso-8859-15"]:
            try:
                with open(filename, "r", encoding=possible_encoding) as srtfile:
                    content = srtfile.read()
                    return content
            except UnicodeDecodeError:
                pass
        raise SubtitlesError("Could not find the proper encoding of {}. Please convert it to utf-8".format(filename))

    def _fetch_remote_subs(self, url):
        response = requests.get(url)
        if not response:
            raise SubtitlesError("Remote subtitles file not found")
        return response.text
