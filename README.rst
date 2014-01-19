***************
Mopidy-Subsonic
***************

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

Searches in Mopidy will now return results from your Subsonic library.


Project resources
=================

- `Source code <https://github.com/rattboi/mopidy-subsonic>`_
- `Issue tracker <https://github.com/rattboi/mopidy-subsonic/issues>`_
- `Download development snapshot <https://github.com/rattboi/mopidy-subsonic/tarball/master#egg={{ cookiecutter.dist_name }}-dev>`_


Changelog
=========

v0.3 (UNRELEASED)
-----------------

- Require Mopidy >= 0.18.

- Fixed: ``ext.conf`` was missing from the PyPI package, stopping Mopidy from
  working as long as Mopidy-Subsonic is installed.

v0.2 (2013-11-13)
-----------------

- TODO: Write

v0.1 (2013-08-29)
-----------------

- Initial release.
