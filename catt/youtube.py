"""
Controller to interface with the YouTube-app.
"""

import re
import threading
try:
    from json import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

import requests
from pychromecast.controllers import BaseController

YOUTUBE_BASE_URL = "https://www.youtube.com/"
YOUTUBE_WATCH_VIDEO_URL = YOUTUBE_BASE_URL + "watch?v="

# id param is const(YouTube sets it as random xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx so it should be fine).
RANDOM_ID = "12345678-9ABC-4DEF-0123-0123456789AB"
VIDEO_ID_PARAM = '%7B%22videoId%22%3A%22{video_id}%22%2C%22currentTime%22%3A5%2C%22currentIndex%22%3A0%7D'
TERMINATE_PARAM = "terminate"

REQUEST_URL_SET_PLAYLIST = YOUTUBE_BASE_URL + "api/lounge/bc/bind?"
BASE_REQUEST_PARAMS = {"device": "REMOTE_CONTROL", "id": RANDOM_ID, "name": "Desktop&app=youtube-desktop",
                       "mdx-version": 3, "loungeIdToken": None, "VER": 8, "v": 2, "t": 1, "ui": 1, "RID": 75956,
                       "CVER": 1}

SET_PLAYLIST_METHOD = {"method": "setPlaylist", "params": VIDEO_ID_PARAM, "TYPE": None}
REQUEST_PARAMS_SET_PLAYLIST = dict(**dict(BASE_REQUEST_PARAMS, **SET_PLAYLIST_METHOD))

REQUEST_DATA_SET_PLAYLIST = "count=0"
REQUEST_DATA_ADD_TO_PLAYLIST = "count=1&ofs=%d&req0__sc=addVideo&req0_videoId=%s"
REQUEST_DATA_REMOVE_FROM_PLAYLIST = "count=1&ofs=%d&req0__sc=removeVideo&req0_videoId=%s"
REQUEST_DATA_CLEAR_PLAYLIST = "count=1&ofs=%d&req0__sc=clearPlaylist"

REQUEST_URL_LOUNGE_TOKEN = YOUTUBE_BASE_URL + "api/lounge/pairing/get_lounge_token_batch"
REQUEST_DATA_LOUNGE_TOKEN = "screen_ids={screenId}&session_token={XSRFToken}"

YOUTUBE_SESSION_TOKEN_REGEX = 'XSRF_TOKEN\W*(.*)="'
SID_REGEX = '"c","(.*?)",\"'
PLAYLIST_ID_REGEX = 'listId":"(.*?)"'
FIRST_VIDEO_ID_REGEX = 'firstVideoId":"(.*?)"'
GSESSION_ID_REGEX = '"S","(.*?)"]'
NOW_PLAYING_REGEX = 'videoId":"(.*?)"'

EXPIRED_LOUNGE_ID_RESPONSE_CONTENT = "Expired lounge id token"

MEDIA_NAMESPACE = "urn:x-cast:com.google.cast.media"
MESSAGE_TYPE = "type"
TYPE_GET_SCREEN_ID = "getMdxSessionStatus"
TYPE_STATUS = "mdxSessionStatus"
ATTR_SCREEN_ID = "screenId"
TYPE_PLAY = "PLAY"
TYPE_PAUSE = "PAUSE"
TYPE_STOP = "STOP"


class YoutubeSessionError(Exception):
    pass


class YoutubeControllerError(Exception):
    pass


class YouTubeController(BaseController):
    """ Controller to interact with Youtube."""

    def __init__(self):
        super(YouTubeController, self).__init__(
            "urn:x-cast:com.google.youtube.mdx", "233637DE")

        self._xsrf_token = None
        self._lounge_token = None
        self._gsession_id = None
        self._sid = None
        self._ofs = 0
        self._first_video = None
        self._playlist_id = None
        self.screen_id = None
        self.video_id = None
        self.playlist = None
        self._now_playing = None
        self.status_update_event = threading.Event()

    @property
    def video_url(self):
        """Returns the base watch video url with the current video_id"""
        video = self._now_playing or self.video_id
        return YOUTUBE_WATCH_VIDEO_URL + video

    @property
    def status(self):
        """ Returns the media_controller status handler when Youtube app is launched."""
        if self.is_active:
            return self._socket_client.media_controller.status
        else:
            return None

    @property
    def in_session(self):
        """ Returns True if session params are not None."""
        if self._gsession_id and self._sid and self._lounge_token:
            return True
        else:
            return False

    def _do_post(self, url, data, params=None, referer=None):
        """
        Does all post requests.
        will raise if response is not 200-ok
        :param url:(str)the request url
        :param data:(str) the request body
        :param params:(dict) the request urlparams
        :param referer:(str) the referer. default is the video url that started the session.
        :return: the response
        """
        headers = {
            "Origin": YOUTUBE_BASE_URL,
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": (referer or self.video_url)
        }
        response = requests.post(url, headers=headers, data=data, params=params)
        response.raise_for_status()
        return response

    def update_screen_id(self):
        """
        Sends a getMdxSessionStatus to get the screen id and waits for response.
        This function is blocking but if connected we should always get a response
        (send message will launch app if it is not running).
        """
        self.status_update_event.clear()
        self.send_message({MESSAGE_TYPE: TYPE_GET_SCREEN_ID})
        self.status_update_event.wait()
        self.status_update_event.clear()

    def _get_xsrf_token(self):
        """
        Get the xsrf_token used as the session token.
        video_id must be initialized.
        Sets the session token(xsrf_token).
        """
        if not self.video_id:
            raise ValueError("Cant start a session without the video_id.")
        response = requests.get(self.video_url)
        response.raise_for_status()
        token = re.search(YOUTUBE_SESSION_TOKEN_REGEX, str(response.content))
        if not token:
            raise YoutubeSessionError("Could not fetch the xsrf token")
        self._xsrf_token = token.group(1)

    def _get_lounge_id(self):
        """
        Gets the lounge_token.
        session_token(xsrf_token) and screenId must be initialized.
        Sets the lounge token.
        """
        if not self.screen_id:
            raise ValueError("Screen id is None. update_screen_id must be called.")
        if not self._xsrf_token:
            raise ValueError("xsrf token is None. Get xsrf token must be called.")
        data = REQUEST_DATA_LOUNGE_TOKEN.format(screenId=self.screen_id, XSRFToken=self._xsrf_token)
        response = self._do_post(REQUEST_URL_LOUNGE_TOKEN, data=data)
        if response.status_code == 401:
            # Screen id is not None and it is updated with a message from the Chromecast.
            #  It is very unlikely that screen_id caused the problem.
            raise YoutubeSessionError("Could not get lounge id. XSRF token has expired or is not valid.")
        response.raise_for_status()
        try:
            lounge_token = response.json()["screens"][0]["loungeToken"]
        except JSONDecodeError:
            raise YoutubeSessionError("Could not get lounge id. XSRF token has expired or not valid.")
        self._lounge_token = lounge_token

    def _set_playlist(self):
        """
        Sends a POST to start the session.
        Uses loung_token and video id as parameters.
        Sets session SID and gsessionid on success.
        """
        if not self.video_id:
            raise ValueError("Can't start a session without the video_id.")
        if not self._lounge_token:
            raise ValueError("lounge token is None. _get_lounge_token must be called")
        url_params = REQUEST_PARAMS_SET_PLAYLIST.copy()
        url_params['loungeIdToken'] = self._lounge_token
        url_params['params'] = VIDEO_ID_PARAM.format(video_id=self.video_id)
        response = self._do_post(REQUEST_URL_SET_PLAYLIST, data=REQUEST_DATA_SET_PLAYLIST, params=url_params)
        content = str(response.content)
        if response.status_code == 401 and content.find(EXPIRED_LOUNGE_ID_RESPONSE_CONTENT) != -1:
            raise YoutubeSessionError("The lounge token expired.")
        response.raise_for_status()
        if not self.in_session:
            self._extract_session_parameters(content)

    def _update_session_parameters(self):
        """
        Sends a POST with no playlist parameters.
        Gets the playlist id, SID, gsession id.
        First video(the playlist base video) and now playing are also returned if  playlist is initialized.
        """
        url_params = BASE_REQUEST_PARAMS.copy()
        url_params['loungeIdToken'] = self._lounge_token
        response = self._do_post(REQUEST_URL_SET_PLAYLIST, data='', params=url_params)
        self._extract_session_parameters(str(response.content))
        return response

    def _extract_session_parameters(self, response_packet_content):
        """
        Extracts the playlist id, SID, gsession id, first video(the playlist base video)
        and now playing from a session response.
        :param response_packet_content: (str) the response packet content
        """
        content = response_packet_content
        playlist_id = re.search(PLAYLIST_ID_REGEX, content)
        sid = re.search(SID_REGEX, content)
        gsession = re.search(GSESSION_ID_REGEX, content)
        first_video = re.search(FIRST_VIDEO_ID_REGEX, content)
        now_playing = re.search(NOW_PLAYING_REGEX, content)
        if not (sid and gsession and playlist_id):
            raise YoutubeSessionError("Could not parse session parameters.")
        self._sid = sid.group(1)
        self._gsession_id = gsession.group(1)
        self._playlist_id = playlist_id.group(1)
        if first_video:
            self._first_video = first_video.group(1)
        else:
            self._first_video = None
        if now_playing:
            self._now_playing = now_playing.group(1)
        else:
            self._now_playing = None

    def _manage_playlist(self, data, referer=None, **kwargs):
        """
        Manages all request to an existing session.
        _gsession_id, _sid, video_id and _lounge_token must be initialized.
        :param data: data of the request
        :param video_id: video id in the request
        :param refer: used for the request heders referer field.video_url by default.
        """
        if not self._gsession_id:
            raise ValueError("gsession must be initialized to manage playlist")
        if not self._sid:
            raise ValueError("sid must be initialized to manage playlist")
        if not self.video_id:
            raise ValueError("video_id can't be empty")
        if self.in_session:
            self._update_session_parameters()
        param_video_id = self._first_video or self.video_id

        url_params = REQUEST_PARAMS_SET_PLAYLIST.copy()
        url_params["loungeIdToken"] = self._lounge_token
        url_params["params"] = VIDEO_ID_PARAM.format(video_id=param_video_id)
        url_params["gsessionid"] = self._gsession_id
        url_params["SID"] = self._sid
        for key in kwargs:
            if key in url_params:
                url_params[key] = kwargs[key]
        try:
            self._do_post(REQUEST_URL_SET_PLAYLIST, referer=referer, data=data, params=url_params)
        except requests.HTTPError:
            # Try to re-get session variables and post again.
            self._set_playlist()
            url_params["loungeIdToken"] = self._lounge_token
            url_params["params"] = VIDEO_ID_PARAM.format(video_id=self._first_video)
            url_params["gsessionid"] = self._gsession_id
            url_params["SID"] = self._sid
            self._ofs = 0
            self._do_post(REQUEST_URL_SET_PLAYLIST, referer=referer, data=data, params=url_params)

    def clear_playlist(self, terminate_session=False):
        """
        clears all tracks on queue without closing the session.
        terminate_session: close the existing session after clearing playlist.
        App closes after a few minutes idle so terminate session if idle for a few minutes.
        """
        self._ofs += 1
        self._manage_playlist(REQUEST_DATA_CLEAR_PLAYLIST % self._ofs)
        if terminate_session:
            self.terminate_session()
        self.playlist = None

    def terminate_session(self):
        """
        terminates the open lounge session.
        """
        try:
            self.clear_playlist()
            self._manage_playlist(data='', video_id=self.video_id, TYPE=TERMINATE_PARAM)
        except requests.RequestException:
            # Session has expired or not in sync.Clean session parameters anyway.
            pass
        self.screen_id = None
        self.video_id = None
        self._xsrf_token = None
        self._lounge_token = None
        self._gsession_id = None
        self._sid = None
        self._ofs = 0
        self.playlist = None
        self._first_video = None

    def receive_message(self, message, data):
        """ Called when a media message is received. """
        if data[MESSAGE_TYPE] == TYPE_STATUS:
            self._process_status(data.get("data"))

            return True

        else:
            return False

    def start_new_session(self, youtube_id):
        self.video_id = youtube_id
        self.update_screen_id()
        self._get_xsrf_token()
        self._get_lounge_id()
        self._update_session_parameters()

    def play_video(self, youtube_id):
        """
        Starts playing a video in the YouTube app.
        The youtube id is also a session identifier used in all requests for the session.
        :param youtube_id: The video id to play.
        """
        if not self.in_session:
            self.start_new_session(youtube_id)
        if self._first_video:
            self.clear_playlist()
        self._set_playlist()
        self._update_session_parameters()

    def add_to_queue(self, youtube_id):
        """
        Adds a video to the queue video will play after the currently playing video ends.
        If video is buffering it wil not be added!
        :param youtube_id: The video id to add to the queue
        """
        if not self.in_session:
            raise YoutubeSessionError('Session must be initialized to add to queue')
        if not self.playlist:
            self.playlist = [self.video_id]
        elif youtube_id in self.playlist:
            raise YoutubeControllerError("Video already in queue")
        self.update_screen_id()
        # if self.status.player_is_idle:
        #     raise YoutubeControllerError("Can't add to queue while video is idle")
        if self.status.player_state == "BUFFERING":
            raise YoutubeControllerError("Can't add to queue while video is buffering")
        self._ofs += 1
        self._manage_playlist(data=REQUEST_DATA_ADD_TO_PLAYLIST % (self._ofs, youtube_id))
        self.playlist.append(youtube_id)

    def _send_command(self, message, namespace=MEDIA_NAMESPACE):
        """
        Sends a message to a specific namespace.
        :param message:(dict) the message to sent to chromecast
        :param namespace:(str) the namespace to send the message to. default is media namespace.
        """
        self._socket_client.send_app_message(namespace, message)

    def play(self):
        self._send_command({MESSAGE_TYPE: TYPE_PLAY})

    def pause(self):
        self._send_command({MESSAGE_TYPE: TYPE_PAUSE})

    def stop(self, clear_queue=True):
        if clear_queue:
            self.clear_playlist()
        self._send_command({MESSAGE_TYPE: TYPE_STOP})

    def _process_status(self, status):
        """ Process latest status update. """
        self.screen_id = status.get(ATTR_SCREEN_ID)
        self.status_update_event.set()

    def tear_down(self):
        """ Called when controller is destroyed. """
        super(YouTubeController, self).tear_down()
        self.terminate_session()
