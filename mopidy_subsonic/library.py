from __future__ import unicode_literals

import logging

from mopidy.backends import base
from mopidy.models import SearchResult
from mopidy.models import Track

from .client import SubsonicRemoteClient

logger = logging.getLogger('mopidy.backends.subsonic')

class SubsonicLibraryProvider(base.BaseLibraryProvider):

    def __init__(self, *args, **kwargs):
        super(SubsonicLibraryProvider, self).__init__(*args, **kwargs)
        self.remote = self.backend.remote
        
    def find_exact(self, query=None, uris=None):
        if not query:
            # Fetch all artists(browse library)
            return SearchResult(
                uri='subsonic:search',
                tracks=self.remote.get_artists())

        return SearchResult(
            uri='subsonic:tracks',
            tracks=self.remote.get_tracks_by(query.get('artist'), query.get('album')))

    def search(self, query=None, uris=None):
        logger.debug('Query "%s":' % query)

        artist,album,title,any = None,None,None,None

        if 'artist' in query:
            artist = query['artist'][0]

        if 'album' in query:
            album = query['album'][0]

        if 'track' in query:
            title = query['track'][0]

        if 'any' in query:
            any = query['any'][0]

        return SearchResult(
                uri='subsonic:tracks',
                tracks=self.remote.search_tracks(artist,album,title,any))

    def lookup(self, uri):
        try:
            song_id = uri.split("subsonic://")[1]
            track = self.remote.get_song(song_id)
            return [track]
        except Exception as error:
            logger.debug('Failed to lookup "%s": %s' % (uri, error))
            return []
