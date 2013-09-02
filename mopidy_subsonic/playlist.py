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
        self.playlists = self._get_playlists()

    def lookup(self, uri):
        logger.debug('Playlist lookup. uri = %s' % uri)
        id = uri.split("subsonic://")[1]
        try:
            id = int(id)
            return self.remote.playlist_id_to_playlist(id)
        except:
            if (id == 'randomsongs'):
                return self.remote.generate_random_playlist()
            else:
                return self.remote.get_smart_playlist(id)

    def _get_playlists(self):
        smart_playlists = {'random':'Random Albums',
                           'newest':'Recently Added',
                           'highest': 'Top Rated',
                           'frequent': 'Most Played',
                           'recent': 'Recently Played',
                           'randomsongs': 'Random Songs'}
        playlists = self.remote.get_user_playlists()
        for type in smart_playlists.keys():
            playlists.append(Playlist(uri=u'subsonic://%s' % type,
                                      name='Smart Playlist: %s' % smart_playlists[type]))

        return playlists
