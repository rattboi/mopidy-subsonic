from __future__ import unicode_literals

import logging
import re

from mopidy.backends import base
from mopidy.models import SearchResult
from mopidy.models import Track

from .client import SubsonicRemoteClient

logger = logging.getLogger('mopidy.backends.subsonic')

class SubsonicLibraryProvider(base.BaseLibraryProvider):

    def __init__(self, *args, **kwargs):
        super(SubsonicLibraryProvider, self).__init__(*args, **kwargs)
        self.config = self.backend.config
        self.remote = SubsonicRemoteClient(
            self.config['subsonic']['hostname'],
            self.config['subsonic']['port'],
            self.config['subsonic']['username'],
            self.config['subsonic']['password'],
            self.config['subsonic']['ssl'])

    def find_exact(self, query=None, uris=None):
            return self.search(query=query, uris=uris)

    def search(self, query=None, uris=None):
        logger.debug('Query "%s":' % query)

        if not query:
            # Fetch all artists(browse library)
            return SearchResult(
                uri='subsonic:search',
                tracks=self.remote.get_artists())

        return SearchResult(
            uri='subsonic:tracks',
            tracks=self.remote.get_tracks_by(query.get('artist'), query.get('album')))

    def lookup(self, uri):
        try:
            id_re = re.compile("(?<=id=)(?P<id>.*?)(?=&)")
            match = id_re.search(uri)
            song_id = match.group('id')
            track = self.remote.get_song(song_id)
            real_uri = uri.split("subsonic://")[1]
            logger.debug('Subsonic track id for "%s": %s' % (real_uri,id))
            ntrack = Track(
                uri=real_uri,
                name=track.name, 
                artists=track.artists, 
                album=track.album, 
                track_no=track.track_no, 
                disc_no=track.disc_no, 
                date=track.date, 
                length=track.length, 
                bitrate=track.bitrate)
            return [ntrack]
        except Exception as error:
            logger.debug('Failed to lookup "%s": %s' % (uri, error))
            return []
