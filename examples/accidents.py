import sys

from catt.api import CattDevice

VIDEOS = [
    "https://www.youtube.com/watch?v=mt084vYqbnY",
    "https://www.youtube.com/watch?v=INxcj8_Zlo8",
    "https://www.youtube.com/watch?v=KDrpPqsXfVU",
]


def ouch(device):
    cast = CattDevice(name=device)
    for video in VIDEOS:
        cast.play_url(video, resolve=True, block=True)
        print("OOOOUUUUUUUUUUUUCCHHH!!!!!")


if __name__ == "__main__":
    ouch(sys.argv[1])
