===============================
Cast All The Things
===============================

.. image:: https://img.shields.io/pypi/v/catt.svg
        :target: https://pypi.python.org/pypi/catt

.. image:: https://img.shields.io/travis/skorokithakis/catt.svg
        :target: https://travis-ci.org/skorokithakis/catt


Cast All The Things allows you to send videos from many, many online sources
(YouTube, Vimeo, and a few hundred others) to your Chromecast. It also allows
you to cast local files.


Installation
------------

You can install Cast All The Things with pip::

    pip install catt

Usage
-----

To use Cast All The Things, just specify a URL::

    catt cast "https://www.youtube.com/watch?v=VZMfhtKa-wo"

CATT supports any service that youtube-dl supports, which includes most online
video hosting services.

CATT can also cast local files (if they're in a format the Chromecast supports
natively)::

    catt cast ./myvideo.mp4

You can also control your Chromecast through ``catt`` commands, for example with
``catt pause``. Try running ``catt --help`` to see the full list of commands.


Contributing
------------
If you want to contribute a feature to CATT, please open an issue (or comment on
an existing one) first, to make sure it's something that the maintainers are
interested in. Afterwards, just clone the repository and hack away!

To run CATT in development, you can use the following command::

    python -m catt.cli --help

Thanks!


Info
----

* Free software: BSD license
* Documentation: https://catt.readthedocs.org.

Features
--------

* Casts videos to Chromecast.
* From many, many online sources.
