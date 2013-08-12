from __future__ import unicode_literals

import logging
import pykka

from mopidy import settings
from mopidy.backends import base

from .library import SubsonicLibraryProvider

logger = logging.getLogger('mopidy.backends.subsonic')

class SubsonicBackend(pykka.ThreadingActor, base.Backend):

    def __init__(self, config, audio):
        super(SubsonicBackend, self).__init__()

        self.library = SubsonicLibraryProvider(backend=self, config=config)
        self.playback = SubsonicPlaybackProvider(audio=audio, backend=self)
        self.playlists = None

        self.uri_schemes = ['subsonic']


class SubsonicPlaybackProvider(base.BasePlaybackProvider):

    # FIXME
    def play(self, track):
        id = track.uri.split(';')[1]
        logger.info('Getting info for track %s with id %s' % (track.uri, id))
        track = self.backend.remote.get_track(id, True)
        return super(SubsonicPlaybackProvider, self).play(track)
