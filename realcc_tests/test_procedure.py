#!/usr/bin/env python3

import json
import subprocess
import time
from typing import Any

import click

CMD_BASE = ["catt", "-d"]
VALIDATE_ARGS = ["info", "-j"]
STOP_ARGS = ["stop"]


# Uses subprocess.run(), so py3.5+ is required.
def subp_run(cmd, allow_failure: bool = False) -> subprocess.CompletedProcess:
    output = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    if not allow_failure and output.returncode != 0:
        raise CattTestError('The command "{}" failed.'.format(" ".join(cmd)))
    return output


class CattTestError(click.ClickException):
    pass


class CattTest:
    def __init__(
        self,
        desc: str,
        cmd_args: list,
        sleep: int = 10,
        should_fail: bool = False,
        substring: bool = False,
        check_data: Any = None,
        check_err: str = "",
    ) -> None:
        if (should_fail and not check_err) or (not should_fail and not check_data):
            raise CattTestError("Expected outcome mismatch.")
        self.desc = desc
        self._cmd_args = cmd_args
        self._cmd = []  # type: list
        self._validate_cmd = []  # type: list
        self._sleep = sleep
        self._should_fail = should_fail
        self._substring = substring
        self._check_key, self._check_val = check_data if check_data else (None, None)
        self._check_err = check_err
        self._output = None  # type: Any
        self._failed = False  # type: bool
        self.dump = ""  # type: str

    def set_cmd_base(self, base: list) -> None:
        self._cmd = base + self._cmd_args
        self._validate_cmd = base + VALIDATE_ARGS

    def _get_val(self, key: str) -> Any:
        output = subp_run(self._validate_cmd)
        catt_json = json.loads(output.stdout)
        return catt_json[key]

    def _should_fail_test(self) -> bool:
        if self._should_fail == self._failed:
            return True
        else:
            self.dump += self._output.stderr if self._failed else self._output.stdout
            return False

    def _failure_test(self) -> bool:
        output_errmsg = self._output.stderr.splitlines()[-1]
        if output_errmsg == "Error: " + self._check_err:
            self.dump += output_errmsg + "\n - The expected error message."
            return True
        else:
            self.dump += self._output.stderr
            return False

    def _regular_test(self) -> bool:
        catt_val = self._get_val(self._check_key)
        if catt_val == self._check_val or (self._substring and self._check_val in catt_val):
            return True
        else:
            self.dump += 'Expected data from "{}" key:\n{} {}\nActual data:\n{}'.format(
                self._check_key, self._check_val, "(substring)" if self._substring else "", catt_val
            )
            return False

    def run(self) -> bool:
        self._output = subp_run(self._cmd, allow_failure=True)
        self._failed = self._output.returncode != 0
        time.sleep(self._sleep)
        if self._should_fail_test():
            if self._failed:
                return self._failure_test()
            else:
                return self._regular_test()
        else:
            return False


DEFAULT_CTRL_TESTS = [
    CattTest(
        "cast h264 1280x720 / aac content from twitch.tv",
        ["cast", "https://clips.twitch.tv/CloudyEnticingChickpeaCeilingCat"],
        check_data=("content_id", "https://clips-media-assets2.twitch.tv/AT-cm%7C304482431.mp4"),
    ),
    CattTest("set volume to 50", ["volume", "50"], sleep=3, check_data=("volume_level", 0.5)),
    CattTest("set volume to 100", ["volume", "100"], sleep=3, check_data=("volume_level", 1.0)),
    CattTest("lower volume by 50 ", ["volumedown", "50"], sleep=3, check_data=("volume_level", 0.5)),
    CattTest("raise volume by 50", ["volumeup", "50"], sleep=3, check_data=("volume_level", 1.0)),
    CattTest(
        "cast h264 640x360 / aac content from twitch.tv",
        ["cast", "-y", "format=360", "https://clips.twitch.tv/CloudyEnticingChickpeaCeilingCat"],
        check_data=("content_id", "https://clips-media-assets2.twitch.tv/AT-cm%7C304482431-360.mp4"),
    ),
    CattTest(
        "cast h264 1280x720 / aac content directly from google commondatastorage",
        ["cast", "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"],
        check_data=("content_id", "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"),
    ),
]

YOUTUBE_CTRL_TESTS = [
    CattTest(
        "cast playlist from youtube",
        ["cast", "https://www.youtube.com/watch?list=PLQNHYNv9IpSzzaQMuH7ji2bEy6o8T8Wwn"],
        check_data=("content_id", "CIvzV5ZdYis"),
    ),
    CattTest("skip to next entry in playlist", ["skip"], sleep=15, check_data=("content_id", "Ff_FvEkuG8w")),
    CattTest(
        "try to add invalid video-url to playlist (should fail)",
        ["add", "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"],
        sleep=3,
        should_fail=True,
        check_err="This url cannot be added to the queue.",
    ),
]

# Some of the audio tests will fail on non-audio devices,
# as they are fed the regular video+audio streams.
AUDIO_ONLY_TESTS = [
    CattTest(
        "cast audio-only DASH aac content from facebook",
        ["cast", "https://www.facebook.com/PixarCars/videos/10158549620120183/"],
        substring=True,
        check_data=("content_id", "18106055_10158549666610183_8333687643300691968_n.mp4"),
    )
]

STANDARD_TESTS = DEFAULT_CTRL_TESTS + YOUTUBE_CTRL_TESTS
AUDIO_TESTS = AUDIO_ONLY_TESTS
ULTRA_TESTS = []  # type: list


def run_tests(standard: str = "", audio: str = "", ultra: str = ""):
    test_outcomes = []  # type: list
    suites = {}  # type: dict
    if standard:
        suites.update({standard: STANDARD_TESTS})
    if audio:
        suites.update({audio: AUDIO_TESTS})
    if ultra:
        suites.update({ultra: ULTRA_TESTS})
    if not suites:
        raise CattTestError("There were no tests to run.")

    for device_name, suite in suites.items():
        click.secho('Running some tests on "{}".'.format(device_name), fg="magenta")
        click.secho("------------------------------------------", fg="magenta")
        cbase = CMD_BASE + [device_name]

        for test in suite:
            test.set_cmd_base(cbase)
            click.echo(test.desc + "  ->  ", nl=False)
            if test.run():
                click.secho("success!", fg="green")
                test_outcomes.append(True)
            else:
                click.secho("failure!", fg="red")
                test_outcomes.append(False)
            if test.dump:
                click.echo("\n" + test.dump + "\n")

        subp_run(cbase + STOP_ARGS)
    return all(t for t in test_outcomes) if test_outcomes else False


@click.command()
@click.option("-s", "--standard", help="Name of standard chromecast device.")
@click.option("-a", "--audio", help="Name of audio chromecast device.")
@click.option("-u", "--ultra", help="Name of ultra chromecast device.")
def cli(standard, audio, ultra):
    if run_tests(standard=standard, audio=audio, ultra=ultra):
        click.echo("\nAll tests were successfully completed.")
    else:
        raise CattTestError("Some tests were not successful.")


if __name__ == "__main__":
    cli()
