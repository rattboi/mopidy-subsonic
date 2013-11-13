#!/usr/local/bin/python
# -*- coding: utf-8 -*-
#
from __future__ import unicode_literals

import logging
import libsonic
import time
import re
from datetime import datetime
from pprint import pprint

from mopidy.models import Track, Album, Artist, Playlist

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
    def album_to_tracks(self, album):
        album_id = album['id']
        songs = self.id_to_dir(album_id)
        return [self.get_track(song) for song in makelist(songs)]

    @cache()
    def id_to_albums(self, id):
        dirs = makelist(self.id_to_dir(id))

        albums = []
        for dir in dirs:
            if dir.get('album'):
                albums.append(dir)
            else:
                albums.extend(self.id_to_albums(dir.get('id')))
        return albums

    @cache()
    def get_tracks_by(self, artist_query, album_query):
        q_artist = None
        q_album = None

        if artist_query:
            q_artist = next(iter(artist_query))
        if album_query:
            q_album  = next(iter(album_query))

        artist_id = self.get_artist_id(q_artist)
        albums = makelist(self.id_to_albums(artist_id))

        tracks = []
        for album in albums:
            if q_album:
                if album.get('album') == q_album:
                    tracks.extend(self.album_to_tracks(album))
            else:
                tracks.extend(self.album_to_tracks(album))

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
        track = self._convert_data(data) 
        return track

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

        track_kwargs['uri'] = 'subsonic://%s' % data['id']

        track = Track(**track_kwargs)

        return track

    def build_url_from_song_id(self, id):
        uri="%s:%d/%s/%s?id=%s&u=%s&p=%s&c=mopidy&v=1.8" % (self.api._baseUrl,
                                                            self.api._port,
                                                            self.api._serverPath,
                                                            'stream.view',
                                                            id,
                                                            self.api._username,
                                                            self.api._rawPass)
        return uri

    def search_artist(self, artist):
        artist_set = set()
        results = unescapeobj(self.api.search2(artist,100,0,0,0,0,0).get('searchResult2'))

        if 'artist' in results:
            for artist in makelist(results.get('artist')):
                artist_id = artist.get('id')
                for album in makelist(self.id_to_albums(artist_id)):
                    artist_set |= set(self.album_to_tracks(album))
        return artist_set

    def search_album(self, album):
        album_set = set()
        results = unescapeobj(self.api.search2(album,0,0,100,0,0,0).get('searchResult2'))

        if 'album' in results:
            for album in makelist(results.get('album')):
                album_set |= set(self.album_to_tracks(album))
        return album_set

    def search_title(self, title):
        title_set = set()
        results = unescapeobj(self.api.search2(title,0,0,0,0,1000,0).get('searchResult2'))

        if 'song' in results:
            title_set = set([self.get_track(song) for song in makelist(results.get('song'))])
        return title_set

    def search_any(self, any):
        artist_set = self.search_artist(any)
        album_set  = self.search_album(any)
        title_set  = self.search_title(any)
        return artist_set | album_set | title_set

    def search_tracks(self, artist, album, title, any):
        any_set,artist_set,album_set,title_set = set(),set(),set(),set()

        if any is not None:
            any_set = self.search_any(any)
        if artist is not None:
            artist_set = self.search_artist(artist)
        if album is not None:
            album_set = self.search_album(album)
        if title is not None:
            title_set = self.search_title(title)

        final_set = set()
        if any is not None:
            final_set = any_set    if not final_set else (final_set & any_set)
        if artist is not None:
            final_set = artist_set if not final_set else (final_set & artist_set)
        if album is not None:
            final_set = album_set  if not final_set else (final_set & album_set)
        if title is not None:
            final_set = title_set   if not final_set else (final_set & title_set)

        final_list = list(final_set)
        final_list.sort(key=lambda x: (next(iter(x.artists)).name, x.album.name, x.track_no))

        return final_list

    # MPD doesn't like /, \n, or \r in names
    # should only necessary until next release of mopidy
    def fix_playlist_name(self, name):
        _invalid_playlist_chars = re.compile(r'[\n\r/]') 
        fixed_name = _invalid_playlist_chars.sub('-', name)
        return fixed_name 

    def get_user_playlists(self):
        results = self.api.getPlaylists().get('playlists')
        if results is u'':
            return []
        else:
            results = makelist(unescapeobj(self.api.getPlaylists().get('playlists').get('playlist')))
            return [Playlist(uri=u'subsonic://%s' % playlist.get('id'),
                         name='User Playlist: %s' % self.fix_playlist_name(playlist.get('name')),
                         last_modified=datetime.strptime(playlist.get('created'),'%Y-%m-%dT%H:%M:%S'))
                         for playlist in results]

    def playlist_id_to_playlist(self, id):
        playlist = unescapeobj(self.api.getPlaylist(id).get('playlist'))
        songs = playlist.get('entry')
        return Playlist(uri=u'subsonic://%s' % playlist.get('id'),
                        name='User Playlist: %s' % self.fix_playlist_name(playlist.get('name')),
                        last_modified=datetime.strptime(playlist.get('created'),'%Y-%m-%dT%H:%M:%S'),
                        tracks=[self.get_track(song) for song in makelist(songs)])

    def get_smart_playlist(self, type):
        tracks = []
        try:
            albums = makelist(unescapeobj(self.api.getAlbumList(type,5).get('albumList').get('album')))
            for album in albums:
                tracks.extend(self.album_to_tracks(album))
            return Playlist(uri=u'subsonic://%s' % type,
                            name=type,
                            tracks=tracks)
        except:
            return Playlist(uri=u'subsonic://%s' % type,
                            name=type,
                            tracks=[])

    def generate_random_playlist(self):
        try:
            songs = makelist(unescapeobj(self.api.getRandomSongs(100).get('randomSongs').get('song')))
            return Playlist(uri=u'subsonic://randomsongs',
                            name='randomsongs',
                            tracks=[self.get_track(song) for song in songs])
        except:
            return Playlist(uri=u'subsonic://randomsongs',
                            name='randomsongs',
                            tracks=[])
