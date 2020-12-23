===============================
Cast All The Things
===============================

.. image:: https://img.shields.io/pypi/v/catt.svg
        :target: https://pypi.python.org/pypi/catt

.. image:: https://img.shields.io/travis/skorokithakis/catt.svg
        :target: https://travis-ci.org/skorokithakis/catt

.. image:: https://badges.gitter.im/Join%20Chat.svg
        :target: https://gitter.im/skorokithakis/catt

Cast All The Things allows you to send videos from many, many online sources
(YouTube, Vimeo, and a few hundred others) to your Chromecast. It also allows
you to cast local files or render websites.


Installation
------------

You can install Cast All The Things with pip::

    pip3 install catt


``catt`` is only compatible with Python 3. If you need a Python 2-compatible
version, please install ``0.5.6``, the last py2-compatible release.


Usage
-----

To use Cast All The Things, just specify a URL::

    catt cast "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

``catt`` supports any service that youtube-dl supports, which includes most online
video hosting services.

``catt`` can also cast local files (if they're in a format the Chromecast supports
natively)::

    catt cast ./myvideo.mp4

You can also control your Chromecast through ``catt`` commands, for example with
``catt pause``. Try running ``catt --help`` to see the full list of commands.

If you have subtitles and the name is similar to the name of the local file, ``catt`` will add them automatically.
You can, of course, specify any other subtitle if you want. Although Chromecast only supports WEBVTT,
TTML and Line 21 subtitles, ``catt`` conveniently converts SRTs to WEBVTT for you on the fly. Here is how to use it::

    catt cast -s ./mysubtitle.srt /myvideo.mp4

``catt`` can also tell your Chromecast to display any website::

    catt cast_site https://en.wikipedia.org/wiki/Rickrolling

Please note that the Chromecast has a slow CPU but a reasonably recent version of Google Chrome. The display
resolution is 1280x720.

If you want to pass youtube-dl options to catt through the `-y` command-line flag, you need to use youtube-dl's
`internal option name <https://github.com/ytdl-org/youtube-dl/blob/master/youtube_dl/__init__.py#L317>`_, rather
than its command-line name.

If you notice that catt stops working with video sites (YouTube, Vimeo, etc), just upgrade youtube-dl with `pip install
-U youtube-dl` and that will probably fix it. This is because sites keep changing and youtube-dl is updated very
regularly to keep them all working.

You can also run ``catt`` in Docker, if you prefer::

    docker run --net=host --rm -it python:3.7 /bin/bash -c "pip install catt; catt cast 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'"


Configuration file
""""""""""""""""""

CATT can utilize a config-file stored at ``~/.config/catt/catt.cfg`` (``%APPDATA%\catt\catt.cfg`` on Windows).

The format is as following::

    [options]
    device = chromecast_one

    [aliases]
    one = chromecast_one
    two = chromecast_two

In the ``[options]`` section, ``device`` denotes the default device that will
be selected, when you have not selected a device via the cli.

You can write your choice of default device to ``catt.cfg`` by doing::

    catt -d <name_of_chromecast> set_default

In the ``[aliases]`` section, you can specify aliases for the names of your
chromecasts. You can then select a device just by doing::

    catt -d <alias> <command>

You can write an alias name for a device to ``catt.cfg`` by doing::

    catt -d <name_of_chromecast> set_alias <alias>


Contributing
------------

If you want to contribute a feature to ``catt``, please open an issue (or comment on
an existing one) first, to make sure it's something that the maintainers are
interested in. Afterwards, just clone the repository and hack away!

To run ``catt`` in development, you can use the following command::

    python -m catt.cli --help

Before committing, please make sure you install ``pre-commit`` and install its hooks::

    pip install pre-commit
    pre-commit install

That's all, now you can commit and the hooks will run. Black (which is used to format
the code) requires Python 3.6 to run, but please make the effort, as our CI will yell
at you if the code is not formatted, and nobody wants that.


Thanks!


Info
----

* Free software: BSD license


Features
--------

* Casts videos to Chromecast
* From `many, many online sources <http://rg3.github.io/youtube-dl/supportedsites.html>`_
* Casts local files (videos, photos and music)
* Casts any website to Chromecast


Thanks
------

Catt would not be possible without these great projects:

* `pychromecast <https://github.com/balloob/pychromecast>`_ - Library for Python 3 to communicate with the Google Chromecast
* `youtube-dl <https://github.com/ytdl-org/youtube-dl>`_ - Command-line program to download videos from YouTube.com and other video sites
* `casttube <https://github.com/ur1katz/casttube>`_ - YouTube Chromecast API
