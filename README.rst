***************
Mopidy-Subsonic
***************

NOTE: This project is now unmaintained!
=======================================

It looks like `loldaves fork <https://github.com/loldaves/mopidy-subsonic>`_ is a lot more maintained. I'd go check that out.

Or even better, try this separate plugin: `Prior99/mopidy-subidy <https://github.com/Prior99/mopidy-subidy>`_







.. image:: https://pypip.in/v/Mopidy-Subsonic/badge.png
    :target: https://pypi.python.org/pypi/Mopidy-Subsonic/
    :alt: Latest PyPI version

.. image:: https://pypip.in/d/Mopidy-Subsonic/badge.png
    :target: https://pypi.python.org/pypi/Mopidy-Subsonic/
    :alt: Number of PyPI downloads


`Mopidy <http://www.mopidy.com/>`_ extension for playing music from
`Subsonic <http://www.subsonic.org/>`_.


Installation
============

Install by running::

    sudo pip install mopidy-subsonic

Or, if available, install the Debian/Ubuntu package from `apt.mopidy.com
<http://apt.mopidy.com/>`_.


Configuration
=============

Before starting Mopidy, you must tell it where to find Subsonic by adding the
following to your Mopidy configuration::

    [subsonic]
    hostname = some.website.com (leave off http/https)
    port = 8888
    username = USER
    password = PASS
    ssl = (yes/no)
    context = my-subsonic (if your subsonic is accessible on http://some.website.com:8888/my-subsonic/index.view)

Searches in Mopidy will now return results from your Subsonic library.


Project resources
=================

- `Source code <https://github.com/rattboi/mopidy-subsonic>`_
- `Issue tracker <https://github.com/rattboi/mopidy-subsonic/issues>`_
- `Download development snapshot <https://github.com/rattboi/mopidy-subsonic/tarball/master#egg={{ cookiecutter.dist_name }}-dev>`_


Changelog
=========

v1.0.0 (UNRELEASED)
-------------------

- Require Mopidy >= 1.0

- Update to work with new playback API in Mopidy 1.0

- Update to work with new search API in Mopidy 1.0

v0.3.1 (2014-01-28)
-------------------

- Removed last_modified field from Playlist generation, to avoid problem in Mopidy core

v0.3 (2014-01-19)
-----------------

- Require Mopidy >= 0.18.

- Fixed: ``ext.conf`` was missing from the PyPI package, stopping Mopidy from
  working as long as Mopidy-Subsonic is installed.

v0.2 (2013-11-13)
-----------------

- Fixed: Crash when starting Mopidy-Subsonic with zero playlists on server

v0.1 (2013-08-29)
-----------------

- Initial release.
