from __future__ import unicode_literals

import logging
import re

from mopidy.backends import base
from mopidy.models import Track
from mopidy.models import Playlist

from .client import SubsonicRemoteClient

logger = logging.getLogger('mopidy.backends.subsonic')

class SubsonicPlaylistsProvider(base.BasePlaylistsProvider):
    def __init__(self, *args, **kwargs):
        super(SubsonicPlaylistsProvider, self).__init__(*args, **kwargs)
        self.remote = self.backend.remote
        self.playlists = []

    def lookup(self, uri):
        logger.info("Playlist lookup")
        return None
