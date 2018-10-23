import sys

from catt.controllers import get_stream, setup_cast

VIDEOS = [
    "https://www.liveleak.com/view?t=kUPSD_1540225257",
    "https://www.liveleak.com/view?t=aLIc5_1540063261",
    "https://www.liveleak.com/view?t=aeI4T_1539973765",
]


def ouch(device):
    player = setup_cast(device, prep="app")
    stream_urls = list()
    for video in VIDEOS:
        stream = get_stream(video)
        stream.set_playlist_entry(0)
        stream_urls.append(stream.video_url)
    for url in stream_urls:
        player.play_media_url(url)
        player.wait_for_playback_end()
        print("OOOOUUUUUUUUUUUUCCHHH!!!!!")


if __name__ == "__main__":
    ouch(sys.argv[1])
