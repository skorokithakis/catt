===============================
Cast All The Things
===============================

.. image:: https://img.shields.io/pypi/v/catt.svg
        :target: https://pypi.python.org/pypi/catt

.. image:: https://img.shields.io/travis/skorokithakis/catt.svg
        :target: https://travis-ci.org/skorokithakis/catt


Cast All The Things allows you to send videos from many, many online sources
(YouTube, Vimeo, and a few hundred others) to your Chromecast.

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

You can also control your Chromecast through ``catt`` commands, for example with
``catt pause``. Try running ``catt --help`` to see the full list of commands.


Info
----

* Free software: BSD license
* Documentation: https://catt.readthedocs.org.

Features
--------

* Casts videos to Chromecast.
* From many, many online sources.
