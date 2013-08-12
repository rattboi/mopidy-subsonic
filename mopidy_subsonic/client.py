#!/usr/local/bin/python
# -*- coding: utf-8 -*-
#
from __future__ import unicode_literals

import logging
import libsonic
import time
from pprint import pprint

from mopidy.models import Track, Album, Artist

logger = logging.getLogger('mopidy.backends.subsonic.client')

class cache(object):
    ## TODO: merge this to util library
    def __init__(self, ctl=8, ttl=3600):
        self.cache = {}
        self.ctl = ctl
        self.ttl = ttl
        self._call_count = 1

    def __call__(self, func):
        def _memoized(*args):
            self.func = func
            now = time.time()
            try:
                value, last_update = self.cache[args]
                age = now - last_update
                if self._call_count >= self.ctl or \
                        age > self.ttl:
                    self._call_count = 1
                    raise AttributeError

                self._call_count += 1
                return value

            except (KeyError, AttributeError):
                value = self.func(*args)
                self.cache[args] = (value, now)
                return value

            except TypeError:
                return self.func(*args)
        return _memoized


class SubsonicRemoteClient(object):

    def __init__(self, endpoint, port, username, password):
        super(SubsonicRemoteClient, self).__init__()
        #self.api = requests.Session()
        if not (endpoint and port and username and password):
          logger.error('Subsonic API settings are not fully defined: %s %s %s %s' % (endpoint, port, username, password))
        else:
            self.api_endpoint = endpoint
            self.api_port = port
            self.api_user = username
            self.api_pass = password
            self.api = libsonic.Connection(self.api_endpoint, self.api_user, self.api_pass, port=int(self.api_port))
            logger.info('Connecting to Subsonic library %s:%s as user %s', self.api_endpoint, self.api_port, self.api_user)
            try:
                self.api.getIndexes()
            except Exception as e:
                print("exception")
                logger.error('Subsonic Authentication error: %s' % e)

    @cache()
    def get_artists(self):
        artist_list = self.api.getArtists().get('artists').get('index')
        categories = []
        for x in xrange(len(artist_list)):
          categories.append(artist_list[x].get('artist'))

        artists = []
        for category in xrange(len(categories)):
          for artist in xrange(len(categories[category])):
            artists.append(categories[category][artist])

        tracks = []
        for artist in artists:
            tracks.append(self.get_track(artist))
        return tracks
      
    @cache(ctl=16)
    def get_track(self, id, remote_url=False):
        stuff = self._convert_data(id, remote_url)
        #pprint(stuff)
        return stuff

    @cache()
    def get_item_by(self, name):
        res = self._get('/item/query/%s' % name).get('results')
        try:
            return self._parse_query(res)
        except Exception:
            return False

    @cache()
    def get_album_by(self, name):
        res = self._get('/album/query/%s' % name).get('results')
        try:
            return self._parse_query(res[0]['items'])
        except Exception:
            return False

    def _get(self, url):
        try:
            indexes = self.api.getIndexes()
            url = self.api_endpoint + ":" + self.api_port + url
            logger.debug('Requesting %s' % url)
            #req = self.api.get(url)
            #if req.status_code != 200:
                #raise logger.error('Request %s, failed with status code %s' % (
                    #url, req.status_code))

            #return req.json()
            return indexes
        except Exception as e:
            logger.error('Request %s, failed with error %s' % (
                url, e))
            return False

    def _parse_query(self, res):
        if len(res) > 0:
            tracks = []
            for track in res:
                tracks.append(self._convert_data(track))
            return tracks
        return None

    def _convert_data(self, data, remote_url=False):
        if not data:
            return
        # NOTE kwargs dict keys must be bytestrings to work on Python < 2.6.5
        # See https://github.com/mopidy/mopidy/issues/302 for details.

        track_kwargs = {}
        album_kwargs = {}
        artist_kwargs = {}
        albumartist_kwargs = {}

        if 'track' in data:
            track_kwargs[b'track_no'] = int(data['track'])

        if 'tracktotal' in data:
            album_kwargs[b'num_tracks'] = int(data['tracktotal'])

        if 'artist' in data:
            artist_kwargs[b'name'] = data['artist']
            albumartist_kwargs[b'name'] = data['artist']

        if 'name' in data:
            artist_kwargs[b'name'] = data['name']
            albumartist_kwargs[b'name'] = data['name']

        if 'albumartist' in data:
            albumartist_kwargs[b'name'] = data['albumartist']

        if 'album' in data:
            album_kwargs[b'name'] = data['album']

        if 'title' in data:
            track_kwargs[b'name'] = data['title']

        if 'date' in data:
            track_kwargs[b'date'] = data['date']

        if 'mb_trackid' in data:
            track_kwargs[b'musicbrainz_id'] = data['mb_trackid']

        if 'mb_albumid' in data:
            album_kwargs[b'musicbrainz_id'] = data['mb_albumid']

        if 'mb_artistid' in data:
            artist_kwargs[b'musicbrainz_id'] = data['mb_artistid']

        if 'mb_albumartistid' in data:
            albumartist_kwargs[b'musicbrainz_id'] = (
                data['mb_albumartistid'])

        if 'album_id' in data:
            album_art_url = '%s/album/%s/art' % (
                self.api_endpoint, data['album_id'])
            album_kwargs[b'images'] = [album_art_url]

        if artist_kwargs:
            artist = Artist(**artist_kwargs)
            track_kwargs[b'artists'] = [artist]

        if albumartist_kwargs:
            albumartist = Artist(**albumartist_kwargs)
            album_kwargs[b'artists'] = [albumartist]

        if album_kwargs:
            album = Album(**album_kwargs)
            track_kwargs[b'album'] = album

        if remote_url:
            track_kwargs[b'uri'] = '%s/item/%s/file' % (
                self.api_endpoint, data['id'])
        else:
            track_kwargs[b'uri'] = 'subsonic://%s' % data['id']
        track_kwargs[b'length'] = int(data.get('length', 0)) * 1000

        track = Track(**track_kwargs)

        return track
