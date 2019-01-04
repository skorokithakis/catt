#!/usr/bin/env python3

import json
import subprocess
import time

import click

CMD_BASE = ["catt", "-d"]
VALIDATE_ARGS = ["info", "-j"]
STOP_ARGS = ["stop"]


class CattTestError(click.ClickException):
    pass


class CattTest:
    def __init__(self, desc, arguments, sleep=10, should_fail=False, check_data=None, check_err=None):
        if (should_fail and not check_err) or (not should_fail and not check_data):
            raise CattTestError("Expected outcome mismatch.")
        self.desc = desc
        self._arguments = arguments
        self._cmd = None
        self._validate_cmd = None
        self._sleep = sleep
        self._should_fail = should_fail
        self._check_key, self._check_val = check_data if check_data else (None, None)
        self._check_err = check_err
        self._output = None
        self._failed = None
        self._dump = str()

    def set_cmd_base(self, base):
        self._cmd = base + self._arguments
        self._validate_cmd = base + VALIDATE_ARGS

    def _subp_run(self, cmd):
        return subprocess.run(cmd, capture_output=True, universal_newlines=True)

    def _get_val(self, key):
        output = self._subp_run(self._validate_cmd)
        if output.returncode != 0:
            raise CattTestError("Failed to retrieve check value.")
        catt_json = json.loads(output.stdout)
        return catt_json[key]

    def _should_fail_test(self):
        if self._should_fail == self._failed:
            if not self._should_fail:
                return True
            else:
                if self._output.stderr.splitlines()[-1] == "Error: " + self._check_err:
                    return True
                else:
                    self._dump += self._output.stderr
                    return False
        else:
            self._dump += self._output.stderr if self._failed else self._output.stdout
            return False

    def _regular_test(self):
        catt_val = self._get_val(self._check_key)
        if catt_val == self._check_val:
            return True
        else:
            self._dump += 'Expected data from "{}" key:\n{}\nActual data:\n{}'.format(
                self._check_key, self._check_val, catt_val
            )
            return False

    def run(self):
        self._output = self._subp_run(self._cmd)
        self._failed = self._output.returncode != 0
        time.sleep(self._sleep)
        return (self._should_fail_test() and self._regular_test(), self._dump)


DEFAULT_CTRL_TESTS = [
    CattTest(
        "h264 1280x720 / aac - default controller",
        ["cast", "https://clips.twitch.tv/CloudyEnticingChickpeaCeilingCat"],
        check_data=("content_id", "https://clips-media-assets2.twitch.tv/AT-cm%7C304482431.mp4"),
    ),
    CattTest("set volume to 50", ["volume", "50"], sleep=3, check_data=("volume_level", 0.5)),
    CattTest("set volume to 100", ["volume", "100"], sleep=3, check_data=("volume_level", 1.0)),
]

STANDARD_TESTS = DEFAULT_CTRL_TESTS
AUDIO_TESTS = []  # type: list
ULTRA_TESTS = []  # type: list


def run_tests(standard=None, audio=None, ultra=None):
    test_outcomes = list()
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
        cbase = CMD_BASE + [device_name]

        for test in suites[device_name]:
            test.set_cmd_base(cbase)
            click.echo(test.desc + "  ->  ", nl=False)
            success, dump = test.run()
            if success:
                click.secho("success!", fg="green")
                test_outcomes.append(True)
            else:
                click.secho("failure!", fg="red")
                click.echo("\n" + dump + "\n")
                test_outcomes.append(False)

        subprocess.run(cbase + STOP_ARGS)

    if test_outcomes:
        return all(t for t in test_outcomes)
    else:
        return False


@click.command()
@click.option("-s", "--standard", help="Name of standard chromecast device.")
@click.option("-a", "--audio", help="Name of audio chromecast device.")
@click.option("-u", "--ultra", help="Name of ultra chromecast device.")
def cli(standard, audio, ultra):
    if run_tests(standard=standard, audio=audio, ultra=ultra):
        click.echo("All tests were successfully completed.")
    else:
        raise CattTestError("Some tests were not successful.")


if __name__ == "__main__":
    cli()
