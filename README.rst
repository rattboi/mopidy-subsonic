Mopidy-Subsonic
===============

`Mopidy <http://www.mopidy.com/>`_ extension for playing music from
`Subsonic <http://www.subsonic.org/>`_

Usage
-----

#. Install the Mopidy-Subsonic extension by running::

    sudo pip install mopidy-subsonic

#. Tell Mopidy where to find Subsonic by adding the following to
   your ``ext.conf``::

    [subsonic]
    hostname = some.website.com (leave off http/https)
    port = 8888
    username = USER
    password = PASS
    ssl = (yes/no)

#. Restart Mopidy.

#. Searches in Mopidy will now return results from your Subsonic library.


Project resources
-----------------

- `Source code <https://github.com/rattboi/mopidy-subsonic>`_
