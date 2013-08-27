from __future__ import unicode_literals

import logging
import pykka

from mopidy.backends import base

from .library import SubsonicLibraryProvider
from .playlist import SubsonicPlaylistsProvider
from .client import SubsonicRemoteClient

from mopidy.models import Track
from pprint import pprint

logger = logging.getLogger('mopidy.backends.subsonic')

class SubsonicBackend(pykka.ThreadingActor, base.Backend):

    def __init__(self, config, audio):
        super(SubsonicBackend, self).__init__()

        self.remote = SubsonicRemoteClient(
            config['subsonic']['hostname'],
            config['subsonic']['port'],
            config['subsonic']['username'],
            config['subsonic']['password'],
            config['subsonic']['ssl'])

        self.config = config
        self.library = SubsonicLibraryProvider(backend=self)
        self.playback = SubsonicPlaybackProvider(audio=audio, backend=self)
        self.playlists = SubsonicPlaylistsProvider(backend=self)

        self.uri_schemes = ['subsonic']


class SubsonicPlaybackProvider(base.BasePlaybackProvider):

    def play(self, track):
        logger.info('Getting info for track %s' % (track.uri))
        return super(SubsonicPlaybackProvider, self).play(track)

