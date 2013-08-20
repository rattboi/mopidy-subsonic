#!/usr/local/bin/python
# -*- coding: utf-8 -*-
#
from __future__ import unicode_literals

import logging
import libsonic
import time
import re
from pprint import pprint

from mopidy.models import Track, Album, Artist

logger = logging.getLogger('mopidy.backends.subsonic.client')

##
# Forces hashes into lists
#
def makelist(x):
    if isinstance(x, list):
        return x
    else:
        return [x]

##
# Unescapes all the unicode values in a query return value
#
def unescapeobj(obj):
  return apply_to_struct(obj, unescape, unicode)

def apply_to_struct(obj, f, t):
    if isinstance(obj, dict):
        newdict = {}
        for key,val in obj.iteritems():
            newdict[key] = apply_to_struct(val, f, t)
        return newdict
    elif isinstance(obj,list):
        newlist = []
        for val in obj:
            newlist.append(apply_to_struct(val, f, t))
        return newlist
    elif isinstance(obj,t):
        return f(obj)
    else:
        return obj

##
# Removes HTML or XML character references and entities from a text string.
#
# @param text The HTML (or XML) source text.
# @return The plain text, as a Unicode string, if necessary.

def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)

class cache(object):
    # TODO: merge this to util library
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

    def __init__(self, hostname, port, username, password, ssl):
        super(SubsonicRemoteClient, self).__init__()

        if not (hostname and port and username and password):
            logger.error('Subsonic API settings are not fully defined: %s %s %s %s %s' % (hostname, port, username, password, ssl))
        else:
            self.api_hostname = hostname
            self.api_port = port
            self.api_user = username
            self.api_pass = password
            if ssl: 
              self.api_hostname = "https://" + hostname
            else:
              self.api_hostname = "http://" + hostname

            self.api = libsonic.Connection(self.api_hostname, self.api_user, self.api_pass, port=int(self.api_port))
            logger.info('Connecting to Subsonic library %s:%s as user %s', self.api_hostname, self.api_port, self.api_user)
            try:
                self.api.ping()
            except Exception as e:
                logger.error('Subsonic Authentication error: %s' % e)
                exit()

    @cache()
    def get_artists(self):
        try:
            # get the artist indexes (segmented by a,b,c,...)
            indexes = unescapeobj(self.api.getIndexes().get('indexes').get('index'))

            # for each index, get it's artists out, turn them into tracks, and return those tracks
            tracks = []
            for index in indexes:
                artists = makelist(index.get('artist'))
                for artist in artists:
                    tracks.append(self.get_track(artist))
            return tracks
        except Exception as error:
            logger.debug('Failed in get_artists: %s' % error)
            return []

    @cache()
    def get_artist_id(self, artist_query):
        artist_tracks = self.get_artists()

        for track in artist_tracks:
            artist = next(iter(track.artists)) #unpack the frozenset
            if (artist.name == artist_query):
                return int(''.join(x for x in track.uri if x.isdigit())) # pull the id number from the URI
        return None

    @cache()
    def id_to_dir(self, id):
        try:
            if not id:
                return []
            return unescapeobj(self.api.getMusicDirectory(id).get('directory').get('child'))
        except Exception as error:
            logger.debug('Failed in id_to_dir: %s' % error)
            return []

    @cache()
    def get_tracks_by(self, artist_query, album_query):
        q_artist = None
        q_album = None

        if artist_query:
            q_artist = next(iter(artist_query))
        if album_query:
            q_album  = next(iter(album_query))

        artist_id = self.get_artist_id(q_artist)
        albums = makelist(self.id_to_dir(artist_id))

        tracks = []
        for album in albums:
            if q_album:
                if album['album'] == q_album:
                    album_id = album['id']
                    songs = self.id_to_dir(album_id)
                    for song in makelist(songs):
                        tracks.append(self.get_track(song))
            else:
                album_id = album['id']
                songs = self.id_to_dir(album_id)
                for song in makelist(songs):
                    tracks.append(self.get_track(song))

        return tracks

    @cache()
    def get_song(self, id):
        try:
            song = unescapeobj(self.api.getSong(id).get('song'))
            track = self.get_track(song)
            return track
        except Exception as error:
            logger.debug('Failed in get_song: %s' % error)
            return []

    @cache(ctl=16)
    def get_track(self, data):
        stuff = self._convert_data(data)
        return stuff

    def _convert_data(self, data):
        if not data:
            return

        track_kwargs = {}
        album_kwargs = {}
        artist_kwargs = {}
        albumartist_kwargs = {}

        if 'track' in data:
            track_kwargs['track_no'] = int(data['track'])

        if 'tracktotal' in data:
            album_kwargs['num_tracks'] = int(data['tracktotal'])

        if 'artist' in data:
            artist_kwargs['name'] = data['artist']
            albumartist_kwargs['name'] = data['artist']

        if 'name' in data:
            artist_kwargs['name'] = data['name']
            albumartist_kwargs['name'] = data['name']

        if 'albumartist' in data:
            albumartist_kwargs['name'] = data['albumartist']

        if 'album' in data:
            album_kwargs['name'] = data['album']

        if 'title' in data:
            track_kwargs['name'] = data['title']

        if 'year' in data:
            track_kwargs['date'] = data['year']

        if 'album_id' in data:
            album_art_url = '%s/album/%s/art' % (
                self.api_hostname, data['album_id'])
            album_kwargs['images'] = [album_art_url]

        if artist_kwargs:
            artist = Artist(**artist_kwargs)
            track_kwargs['artists'] = [artist]

        if albumartist_kwargs:
            albumartist = Artist(**albumartist_kwargs)
            album_kwargs['artists'] = [albumartist]

        if album_kwargs:
            album = Album(**album_kwargs)
            track_kwargs['album'] = album

        track_kwargs['length'] = int(data.get('duration', 0)) * 1000
        track_kwargs['bitrate'] = data.get('bitRate', 0)

        if not 'title' in data:
          track_kwargs['uri'] = 'subsonic://%s' % data['id']
        else:
          track_kwargs['uri'] = 'subsonic://%s' % self.build_url_from_song_id(data['id'])

        track = Track(**track_kwargs)

        return track
      
    def build_url_from_song_id(self, id):
        uri="%s:%d/%s/%s?id=%s&u=%s&p=%s&c=mopidy&v=1.8" % (self.api._baseUrl, self.api._port, self.api._serverPath, 'stream.view', id, self.api._username, self.api._rawPass)  
        return uri
