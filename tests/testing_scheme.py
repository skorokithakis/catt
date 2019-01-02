#!/usr/bin/env python3

import json
import subprocess
import time

import click

GET_VAL_CMD = ["catt", "-d", "video", "info", "-j"]
RESULT_PAD = "  ->  "


class CattTestError(Exception):
    pass


class CattTest:
    def __init__(self, desc, arguments, sleep, should_fail=False, check_data=None, check_err=None):
        if (should_fail and not check_err) or (not should_fail and not check_data):
            raise CattTestError("expected outcome mismatch.")
        self.desc = desc
        self.cmd = ["catt"]
        self.cmd.extend(arguments)
        self.sleep = sleep
        self.should_fail = should_fail
        self.check_key, self.check_val = check_data if check_data else (None, None)
        self.check_err = check_err

    def _subp_run(self, cmd):
        return subprocess.run(cmd, capture_output=True, universal_newlines=True)

    def _get_val(self, key):
        output = self._subp_run(GET_VAL_CMD)
        if output.returncode != 0:
            raise CattTestError("failed to retrieve check value")
        catt_json = json.loads(output.stdout)
        return catt_json[key]

    def run(self):
        output = self._subp_run(self.cmd)

        failed = output.returncode != 0
        if self.should_fail != failed:
            return (False, output.stderr if failed else output.stdout)
        if self.should_fail and output.stderr != "Error: " + self.check_err:
            return (False, output.stderr)

        time.sleep(self.sleep)
        catt_val = self._get_val(self.check_key)
        if self.check_val != catt_val:
            return (False, "{}\n{}".format(self.check_val, catt_val))

        return (True, None)


TESTS = [
    CattTest(
        "h264 1280x720 / aac - default controller",
        ["-d", "video", "cast", "https://clips.twitch.tv/CloudyEnticingChickpeaCeilingCat"],
        10,
        check_data=("content_id", "https://clips-media-assets2.twitch.tv/AT-cm%7C304482431.mp4"),
    )
]


def main():
    for test in TESTS:
        click.echo(test.desc + RESULT_PAD, nl=False)
        success, dump = test.run()
        if success:
            click.secho("success!", fg="green")
        else:
            click.secho("failure!", fg="red")
            click.echo(dump)


if __name__ == "__main__":
    main()
