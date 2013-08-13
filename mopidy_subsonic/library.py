from __future__ import unicode_literals

import logging

from mopidy.backends import base
from mopidy.models import SearchResult

from .client import SubsonicRemoteClient

logger = logging.getLogger('mopidy.backends.subsonic')

class SubsonicLibraryProvider(base.BaseLibraryProvider):

    def __init__(self, *args, **kwargs):
        super(SubsonicLibraryProvider, self).__init__(*args, **kwargs)
        self.config = self.backend.config
        self.remote = SubsonicRemoteClient(self.config['subsonic']['hostname'],
            self.config['subsonic']['port'],
            self.config['subsonic']['username'],
            self.config['subsonic']['password'])

    def find_exact(self, query=None, uris=None):
            return self.search(query=query, uris=uris)

    def search(self, query=None, uris=None):
        logger.debug('Query "%s":' % query)
#        if not self.remote.has_connection:
#            return []

        if not query:
            # Fetch all artists(browse library)
            return SearchResult(
                uri='subsonic:search',
                tracks=self.remote.get_artists())

        self._validate_query(query)
        if 'any' in query:
            return SearchResult(
                uri='subsonic:search-any',
                tracks=self.remote.get_item_by(query['any'][0]) or [])
        else:
            search = []
            for (field, val) in query.iteritems():

                if field == "album":
                    search.append(val[0])
                if field == "artist":
                    search.append(val[0])
                if field == "track":
                    search.append(val[0])
                if field == "date":
                    search.append(val[0])
            logger.debug('Search query "%s":' % search)
            return SearchResult(
                uri='subsonic:search-' + '-'.join(search),
                tracks=self.remote.get_item_by('/'.join(search)) or [])

    def lookup(self, uri):
        try:
            id = uri.split("//")[1]
            logger.debug('Subsonic track id for "%s": %s' % id, uri)
            return [self.remote.get_track(id, True)]
        except Exception as error:
            logger.debug('Failed to lookup "%s": %s' % (uri, error))
            return []

    def _validate_query(self, query):
        for (_, values) in query.iteritems():
            if not values:
                raise LookupError('Missing query')
            for value in values:
                if not value:
                    raise LookupError('Missing query')
