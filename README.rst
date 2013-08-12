Mopidy-Subsonic
============

`Mopidy <http://www.mopidy.com/>`_ extension for playing music from
`Subsonic <http://www.subsonic.org/>`
Note
====

The below is inaccurate currently. Very much WIP.

Usage
-----

#. Install the Mopidy-Subsonic extension by running::

    sudo pip install mopidy-subsonic

#. Tell Mopidy where to find Subsonic by adding the following to
   your ``ext.conf``::

    [subsonic]
    hostname = 127.0.0.1
    port = 8888
    username = USER
    password = PASS

#. Restart Mopidy.

#. Searches in Mopidy will now return results from your Subsonic library.


Project resources
-----------------

- `Source code <https://github.com/rattboi/mopidy-subsonic>`_
