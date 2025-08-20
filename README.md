Cast All The Things
===================

[![image](https://img.shields.io/pypi/v/catt.svg)](https://pypi.python.org/pypi/catt)

Cast All The Things allows you to send videos from many, many online
sources (YouTube, Vimeo, and a few hundred others) to your Chromecast.
It also allows you to cast local files or render websites.

Installation
------------

You can run Cast All The Things with uv without installing:

    uxv catt

You can install Cast All The Things with pipx:

    pipx install catt

Or with pip, but that's not as good:

    pip3 install catt

`catt` requires Python 3.11 or higher. For older Python versions,
you can install `catt` version 0.12.x which supports Python 3.7+.

Usage
-----

To use Cast All The Things, just specify a URL:

    catt cast "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

`catt` supports any service that yt-dlp supports, which includes most
online video hosting services.

`catt` can also cast local files (if they're in a format the Chromecast
supports natively):

    catt cast ./myvideo.mp4

You can also control your Chromecast through `catt` commands, for
example with `catt pause`. Try running `catt --help` to see the full
list of commands.

If you have subtitles and the name is similar to the name of the local
file, `catt` will add them automatically. You can, of course, specify
any other subtitle if you want. Although Chromecast only supports
WEBVTT, TTML and Line 21 subtitles, `catt` conveniently converts SRTs to
WEBVTT for you on the fly. Here is how to use it:

    catt cast -s ./mysubtitle.srt /myvideo.mp4

`catt` can also tell your Chromecast to display any website:

    catt cast_site https://en.wikipedia.org/wiki/Rickrolling

Please note that the Chromecast has a slow CPU but a reasonably recent
version of Google Chrome. The display resolution is 1280x720.

If you want to pass yt-dlp options to catt through the [-y]{.title-ref}
command-line flag, you need to use yt-dlp's [internal option
name](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/__init__.py#L620),
rather than its command-line name.

If you notice that catt stops working with video sites (YouTube, Vimeo,
etc), just upgrade yt-dlp with [pip install -U yt-dlp]{.title-ref} and
that will probably fix it. This is because sites keep changing and
yt-dlp is updated very regularly to keep them all working.

You can also run `catt` in Docker, if you prefer:

    docker run --net=host --rm -it python:3.7 /bin/bash -c "pip install catt; catt cast 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'"

### Configuration file

CATT can utilize a config-file stored at `~/.config/catt/catt.cfg`
(`%APPDATA%\catt\catt.cfg` on Windows, `~/Library/Application Support/catt/catt.cfg` on macOS).

The format is as following:

```ini
[options]
device = chromecast_one

[aliases]
one = chromecast_one
two = chromecast_two
```

In the `[options]` section, `device` denotes the default device that
will be selected, when you have not selected a device via the cli.

You can write your choice of default device to `catt.cfg` by doing:

    catt -d <name_of_chromecast> set_default

In the `[aliases]` section, you can specify aliases for the names of
your chromecasts. You can then select a device just by doing:

    catt -d <alias> <command>

You can write an alias name for a device to `catt.cfg` by doing:

    catt -d <name_of_chromecast> set_alias <alias>

Firewall
--------

For the casting of local files to work you need to allow in the port range 45000-47000 over tcp.

Contributing
------------

If you want to contribute a feature to `catt`, please open an issue (or
comment on an existing one) first, to make sure it's something that the
maintainers are interested in. Afterwards, just clone the repository and
hack away!

To run `catt` in development, you can use the following command:

    python -m catt.cli --help

Before committing, please make sure you install `pre-commit` and install
its hooks:

    pip install pre-commit
    pre-commit install

That's all, now you can commit and the hooks will run. Black (which is
used to format the code) requires Python 3.6 to run, but please make the
effort, as our CI will yell at you if the code is not formatted, and
nobody wants that.

Thanks!

Info
----

-   Free software: BSD license

Features
--------

- Casts videos to Chromecast
- From [many, many online
  sources](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)
- Casts local files (videos, photos and music)
- Casts any website to Chromecast

Thanks
------

Catt would not be possible without these great projects:

- [pychromecast](https://github.com/balloob/pychromecast) - Library
  for Python 3 to communicate with the Google Chromecast
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Command-line program to
  download videos from YouTube.com and other video sites
- [casttube](https://github.com/ur1katz/casttube) - YouTube Chromecast
  API
