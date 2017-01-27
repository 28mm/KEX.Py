#!/usr/bin/env python3

import json
from urllib import request
import pprint
import sys
import argparse
from datetime import datetime

from bs4 import BeautifulSoup
import spotipy
import spotipy.util as util


def main():

    parser = argparse.ArgumentParser( description = 'populate a new spotify playlist with songs from an hour or hours of KEXP Radio.')

    parser.add_argument('--username',
                        dest='username',
                        metavar='username',
                        required=True)

    # 
    parser.add_argument('--day',
                        dest='day',
                        metavar='day',
                        required=False)

    parser.add_argument('--weeks',
                        dest='weeks',
                        metavar='weeks',
                        default=1,
                        required=False)

    # 
    parser.add_argument('--mdy',
                        dest='mdy',
                        metavar='mdy',
                        required=False)

    parser.add_argument('--hour',
                        dest='hour',
                        metavar='hour',
                        required=False)

    parser.add_argument('--playlist',
                        dest='playlist',
                        metavar='playlist',
                        required=True) # <-- FIXME just generate a default

    args = parser.parse_args()
    username = args.username

    if args.hour is not None:
        hour = args.hour # FIXME check bounds.

        if args.mdy is not None:
            date  = datetime.strptime(args.mdy, '%m/%d/%Y')
        else:
            date  = datetime.now()

        month = date.strftime('%m')
        day   = date.strftime('%d')
        year  = date.strftime('%Y')

    radio  = kexp()

    if args.hour is not None or args.mdy is not None:
        hours = args.hour.split('-')
        tracks = []
        if len(hours) > 1:
            for h in range(int(hours[0]), int(hours[1])):
                tracks += radio.past_tracks(year, month, day, h)
        else:
            tracks = radio.past_tracks(year, month, day, hour)
    else:
        tracks = radio.current_tracks()

    #print(tracks)

    sp = spotify_wrapper(username)

    print('**** BUILDING PLAYLIST: "' + args.playlist + '" ****')
    for t in tracks:
        t.sid = sp.track_id(t)
        if t.sid:
            print('FOUND:   ' + str(t.artist) + ' ' + str(t.title))
        else:
            print('MISSING: ' + str(t.artist) + ' ' + str(t.title))
    playlist_id = sp.create_playlist(args.playlist)
    sp.playlist_add(playlist_id, tracks)

class spotify_wrapper:

    def __init__(self, username):
        self.username = username
        self.token = util.prompt_for_user_token(self.username,
                                                scope='playlist-modify-public')

        ## FIXME Don't do this here.
        if self.token is None:
            sys.exit(1)

        self.sp = spotipy.Spotify(auth=self.token)

    def track_id(self, t):
        """Search spotify for a track (by: artist and title).
        Return its sid as a string."""
        if t.artist is None or t.title is None:
            return None
        result = self.sp.search(str(t.artist) + ' ' + str(t.title),
                                type='track')

        ## FIXME: Log debug msgs somewhere
        #pprint.pprint(result['tracks']['items'][0]['id'])
        #sys.exit(0)

        try:
            return result['tracks']['items'][0]['id']
        except:
            return None

    def search_playlist(self, title):
        "Find a playlist whose title matches and return its id as a string"
        raise # FIXME

    def create_playlist(self, title):
        "Create a playlist and return its id as a string"
        playlist = self.sp.user_playlist_create(self.username, title)
        #pprint.pprint(playlist)
        return playlist['id']

    def playlist_add(self, playlist_id, tracks):
        """Take a list of tracks, and adds them to a given playlist.
        Silently ignore tracks for which we don't have spotify ids (sid)"""
        tracks = [ track.sid for track in tracks if track.sid is not None ]
        self.sp.user_playlist_add_tracks(self.username, playlist_id, tracks)

class track:
    def __init__(self, artist='', title='', label='', sid=''):
        self.artist = artist
        self.title  = title
        self.label  = label
        self.sid    = sid

    def __str__(self):
        return '[' + str(self.artist) + ' | ' \
            + str(self.title) + ' | '         \
            + str(self.label) + ']'

    def __repr__(self):
        return self.__str__()

class kexp:

    #
    # Treat as public methods

    def __init__(self):
        self.KEXP_BASE_URL = 'http://www.kexp.org/playlist'

    def current_tracks(self):
        tracks = []
        for elt in self.current_playlist_soup():
            track_json = json.loads(elt['data-playlistitem'])
            tracks.append( track(artist=track_json['ArtistName'],
                                 title=track_json['TrackName'],
                                 label=track_json['LabelName']))
        return tracks

    def past_tracks(self, year, month, day, hour):
        tracks = []
        for elt in self.past_playlist_soup(year, month, day, hour):
            track_json = json.loads(elt['data-playlistitem'])
            tracks.append( track(artist=track_json['ArtistName'],
                                 title=track_json['TrackName'],
                                 label=track_json['LabelName']))
        return tracks
    #
    # Treat as class-private:

    def current_playlist_soup(self):
        soup = BeautifulSoup(self.current_playlist_html(), 'html.parser')
        return [ elt for elt in soup.find_all('div', class_='Play') ]

    def past_playlist_soup(self, year, month, day, hour):
        soup = BeautifulSoup(self.past_playlist_html(year, month, day, hour),
                             'html.parser')
        return [ elt for elt in soup.find_all('div', class_='Play') ]


    def current_playlist_html(self):
        response = request.urlopen(self.KEXP_BASE_URL)
        return response

    def past_playlist_html(self, year, month, day, hour):
        #print(str(year) + ' ' + str(month) + ' ' + str(day) + ' ' + str(hour))
        #print(self.KEXP_BASE_URL + '/' + str(year)         \
        #                       + '/' + str(month)                      \
        #                       + '/' + str(day)                        \
        #                       + '/' + (str(hour) + 'AM'               \
        #                                    if int(hour) < 13               \
        #                                    else str(int(hour)-12) + 'PM'))
        response = request.urlopen(self.KEXP_BASE_URL + '/' + str(year)         \
                               + '/' + str(month)                      \
                               + '/' + str(day)                        \
                               + '/' + (str(hour) + 'AM'               \
                                            if int(hour) < 13               \
                                            else str(int(hour)-12) + 'PM'))
        return response


if __name__ == '__main__': main()
