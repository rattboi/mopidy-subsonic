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
# Unescapes all the unicode values in a query return value
#
#
#

def unescapeobj(obj):
    if type(obj) == dict:
        newdict = {}
        for key,val in obj.iteritems():
            newdict[key] = unescapeobj(val)
        return newdict
    elif type(obj) == list:
        newlist = []
        for val in obj:
            newlist.append(unescapeobj(val))
        return newlist
    elif type(obj) == unicode:
        return unescape(obj)
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

    def __init__(self, hostname, port, username, password):
        super(SubsonicRemoteClient, self).__init__()

        if not (hostname and port and username and password):
          logger.error('Subsonic API settings are not fully defined: %s %s %s %s' % (hostname, port, username, password))
        else:
            self.api_hostname = hostname
            self.api_port = port
            self.api_user = username
            self.api_pass = password
            self.api = libsonic.Connection(self.api_hostname, self.api_user, self.api_pass, port=int(self.api_port))
            logger.info('Connecting to Subsonic library %s:%s as user %s', self.api_hostname, self.api_port, self.api_user)
            try:
                self.api.getIndexes()
            except Exception as e:
                logger.error('Subsonic Authentication error: %s' % e)

    @cache()
    def get_artists(self):
        artist_list = unescapeobj(self.api.getArtists()).get('artists').get('index')
        categories = []
        for x in xrange(len(artist_list)):
          artists = []
          artist = artist_list[x].get('artist')
          if type(artist) == dict:
            artists.append(artist)
          else:
            artists = artist
          categories.append(artists)

        artists = []
        for category in xrange(len(categories)):
          for artist in xrange(len(categories[category])):
            artists.append(categories[category][artist])

        tracks = []
        for artist in artists:
            tracks.append(self.get_track(artist))

        return tracks

    @cache()
    def get_albums_by(self, name):
      tracks = self.get_artists()

      artist_id = None

      for track in tracks:
        artist = next(iter(track.artists))
        if (artist.name == name):
          artist_id = int(''.join(x for x in track.uri if x.isdigit()))
          break

      if artist_id:
        tracks = []

        albums = unescapeobj(self.api.getArtist(artist_id))

        if int(albums['artist']['albumCount']) > 1:
          for album in albums['artist']['album']:
            tracks.append(self.get_album(album))
        else:
          tracks.append(self.get_album(albums['artist']['album']))

        return tracks

      return []

    @cache()
    def get_tracks_by(self, artist_query, album_query):
      q_artist = next(iter(artist_query))
      q_album  = next(iter(album_query))
      
      tracks = self.get_artists()

      artist_id = None

      for track in tracks:
        artist = next(iter(track.artists))
        if (artist.name == q_artist):
          artist_id = int(''.join(x for x in track.uri if x.isdigit()))
          break

      if artist_id:
        tracks = []

        albums = unescapeobj(self.api.getArtist(artist_id))

        if int(albums['artist']['albumCount']) > 1:
          for album in albums['artist']['album']:
            if album['name'] == q_album:
              album_id = album['id']
              songs = unescapeobj(self.api.getAlbum(album_id))
              for song in songs['album']['song']:
                tracks.append(self.get_track(song))
        else:
            if albums['artist']['album']['name'] == q_album:
              album_id = albums['artist']['album']['id']
              songs = unescapeobj(self.api.getAlbum(album_id))
              for song in songs['album']['song']:
                tracks.append(self.get_track(song))

        return tracks

      return []

    @cache(ctl=16)
    def get_album(self, id):
        stuff = self._get_album(id)
        return stuff

    @cache(ctl=16)
    def get_track(self, id, remote_url=False):
        stuff = self._convert_data(id, remote_url)
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
            url = self.api_hostname + ":" + self.api_port + url
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

    def _get_album(self, data):
        if not data:
            return

        track_kwargs = {}
        album_kwargs = {}
        artist_kwargs = {}
        albumartist_kwargs = {}

        if 'track' in data:
            track_kwargs['track_no'] = int(data['track'])

        if 'songCount' in data:
            album_kwargs['num_tracks'] = int(data['songCount'])

        if 'artist' in data:
            artist_kwargs['name'] = data['artist']
            albumartist_kwargs['name'] = data['artist']

        if 'name' in data:
            album_kwargs['name'] = data['name']

        if 'albumartist' in data:
            albumartist_kwargs['name'] = data['albumartist']

        if artist_kwargs:
            artist = Artist(**artist_kwargs)
            track_kwargs['artists'] = [artist]

        if albumartist_kwargs:
            albumartist = Artist(**albumartist_kwargs)
            album_kwargs['artists'] = [albumartist]

        if album_kwargs:
            album = Album(**album_kwargs)
            track_kwargs['album'] = album

        track_kwargs['uri'] = 'subsonic://%s' % data['id']
        track_kwargs['length'] = int(data.get('duration', 0)) 

        track = Track(**track_kwargs)

        return track

    def _convert_data(self, data, remote_url=False):
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

        if remote_url:
            track_kwargs['uri'] = '%s/item/%s/file' % (
                self.api_hostname, data['id'])
        else:
            track_kwargs['uri'] = 'subsonic://%s' % data['id']
        track_kwargs['length'] = int(data.get('length', 0)) * 1000

        track = Track(**track_kwargs)

        return track
