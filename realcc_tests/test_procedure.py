#!/usr/bin/env python3

import json
import subprocess
import time

import click

CMD_BASE = ["catt", "-d"]
VALIDATE_ARGS = ["info", "-j"]


class CattTestError(click.ClickException):
    pass


class CattTest:
    def __init__(self, desc, arguments, sleep=10, should_fail=False, check_data=None, check_err=None):
        if (should_fail and not check_err) or (not should_fail and not check_data):
            raise CattTestError("Expected outcome mismatch.")
        self.desc = desc
        self.arguments = arguments
        self.cmd = None
        self.validate_cmd = None
        self.sleep = sleep
        self.should_fail = should_fail
        self.check_key, self.check_val = check_data if check_data else (None, None)
        self.check_err = check_err

    def set_cmd_base(self, base):
        self.cmd = base + self.arguments
        self.validate_cmd = base + VALIDATE_ARGS

    def _subp_run(self, cmd):
        return subprocess.run(cmd, capture_output=True, universal_newlines=True)

    def _get_val(self, key):
        output = self._subp_run(self.validate_cmd)
        if output.returncode != 0:
            raise CattTestError("Failed to retrieve check value.")
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
        if catt_val != self.check_val:
            dump = 'Expected data from "{}" key:\n{}\nActual data:\n{}'.format(self.check_key, self.check_val, catt_val)
            return (False, dump)
        return (True, None)


SOME_TESTS = [
    CattTest(
        "h264 1280x720 / aac - default controller",
        ["cast", "https://clips.twitch.tv/CloudyEnticingChickpeaCeilingCat"],
        check_data=("content_id", "https://clips-media-assets2.twitch.tv/AT-cm%7C304482431.mp4"),
    )
]

STANDARD_TESTS = SOME_TESTS
AUDIO_TESTS = []  # type: list
ULTRA_TESTS = []  # type: list


def run_tests(standard=None, audio=None, ultra=None):
    complete_success = True
    suites = dict()
    if standard:
        suites.update({standard: STANDARD_TESTS})
    if audio:
        suites.update({audio: AUDIO_TESTS})
    if ultra:
        suites.update({ultra: ULTRA_TESTS})
    if not suites:
        raise CattTestError("There were no tests to run.")

    for device_name in suites.keys():
        click.secho('Running some tests on "{}".'.format(device_name), fg="magenta")
        click.secho("------------------------------------------", fg="magenta")
        for test in suites[device_name]:
            test.set_cmd_base(CMD_BASE + [device_name])
            click.echo(test.desc + "  ->  ", nl=False)
            success, dump = test.run()
            if success:
                click.secho("success!", fg="green")
            else:
                click.secho("failure!", fg="red")
                click.echo("\n" + dump + "\n")
                complete_success = False
    return complete_success


@click.command()
@click.option("-s", "--standard", help="Name of standard chromecast device.")
@click.option("-a", "--audio", help="Name of audio chromecast device.")
@click.option("-u", "--ultra", help="Name of ultra chromecast device.")
def cli(standard, audio, ultra):
    if not run_tests(standard=standard, audio=audio, ultra=ultra):
        raise CattTestError("Some tests were not successful.")


if __name__ == "__main__":
    cli()
