from __future__ import unicode_literals

import logging
import pykka

from mopidy.backends import base

from .library import SubsonicLibraryProvider
from .playlist import SubsonicPlaylistsProvider
from .client import SubsonicRemoteClient

from mopidy.models import Track

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
        logger.debug('Getting info for track %s' % (track.name))
        id = track.uri.split("subsonic://")[1]
        real_uri = self.backend.remote.build_url_from_song_id(id)
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
        return super(SubsonicPlaybackProvider, self).play(ntrack)

