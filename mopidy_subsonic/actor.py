from __future__ import unicode_literals

import logging
import pykka

from mopidy import settings
from mopidy.backends import base

from .library import SubsonicLibraryProvider
from .client import SubsonicRemoteClient

logger = logging.getLogger('mopidy.backends.subsonic')

class SubsonicBackend(pykka.ThreadingActor, base.Backend):

    def __init__(self, config, audio):
        super(SubsonicBackend, self).__init__()

        subsonic_endpoint = 'http://%s:%s' % (
            config['subsonic']['hostname'], config['subsonic']['port'])

        #self.beets_api = SubsonicRemoteClient(beets_endpoint)
        self.library = SubsonicLibraryProvider(backend=self)
        self.playback = SubsonicPlaybackProvider(audio=audio, backend=self)
        self.playlists = None

        self.uri_schemes = ['subsonic']


class SubsonicPlaybackProvider(base.BasePlaybackProvider):

    # FIXME
    def play(self, track):
        id = track.uri.split(';')[1]
        logger.info('Getting info for track %s with id %s' % (track.uri, id))
        #track = self.backend.beets_api.get_track(id, True)
        return super(SubsonicPlaybackProvider, self).play(track)
