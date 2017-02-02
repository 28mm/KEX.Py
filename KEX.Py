#!/usr/bin/env python3

import json
import requests
import pprint
import sys
import argparse
from datetime import datetime, timedelta, timezone, tzinfo

import spotipy
import spotipy.util as util


def main():

    parser = argparse.ArgumentParser( description = 'populate a new spotify playlist with songs from an hour or hours of KEXP Radio.')

    parser.add_argument('--username',
                        dest='username',
                        metavar='username',
                        required=True)

    # start date time    
    parser.add_argument('--mdyh',
                        dest='mdyh',
                        help='Example: --mdyh \"01/31/2017T18\"',
                        metavar='\"mm/dd/yyyyThh\"',
                        required=False)

    # number of hours to get playlist for; default to 3 hours
    parser.add_argument('--hours',
                        dest='hours',
                        metavar='num_of_hours',
                        help='Number of hours of KEXP playlist to grab.  Default = 3 hours',
                        default=3,
                        required=False)

    parser.add_argument('--playlist',
                        dest='playlist',
                        metavar='playlist',
                        help='Spotify playlist name',
                        required=True) # <-- FIXME just generate a default

    parser.add_argument('--always_create_new_playlist',
                        dest='always_create_new_playlist',
                        action='store_true')

    args = parser.parse_args()
    username = args.username
    always_create_new_playlist = args.always_create_new_playlist
    
    # Create datetime representation of time interval
    # Use current datetime if one not provided in args
    # FIXME should specify pacific timezone on this. currently assumes local
    if args.mdyh is not None:
        start_datetime = datetime.strptime(args.mdyh, '%m/%d/%YT%H') # FIXME check start date is in the past otherwise no songs will be returned
    else:
        start_datetime = datetime.now()  # FIXME this may be a bug because end_time will be in the future.  Check what happens on KEXP API
    
    num_of_hours = int(args.hours)
    if num_of_hours is not None and num_of_hours > 0:   # FIXME confirm failure if args.hours is not an int
        end_datetime = start_datetime + timedelta(hours=num_of_hours)
    else:
        sys.exit(1) # FIXME include error message

    # Get track instances for the time interval
    radio  = kexp()
    print('**** FETCHING KEXP PLAYLIST FOR ' + 
        start_datetime.strftime('%a %b %d, %Y %H:%M') + ' to ' + 
        end_datetime.strftime('%a %b %d, %Y %H:%M'))
    tracks = radio.get_tracks(datetime.utcfromtimestamp(start_datetime.timestamp()), 
                                datetime.utcfromtimestamp(end_datetime.timestamp()))
    
    # Check that we have tracks
    # debug: KEXP cache can get stale somtimes, http://cache.kexp.org/cache/info
    if len(tracks) == 0: 
        print('No tracks found for: ' + start_datetime.strftime('%a %b %d, %Y %H:%M'))
        print('Perhaps the KEXP cache is stale? See http://cache.kexp.org/cache/info')  # FIXME lookup cache stats and offer evaluation
        sys.exit(0)

    # Lookup tracks in Spotify
    sp = spotify_wrapper(username)
    print('**** MATCHING TRACKS AGAINST SPOTIFY ****')
    for t in tracks:
        t.sid = sp.track_id(t)
        if t.sid:
            print('FOUND:   ' + str(t.artist) + ' - ' + str(t.title))
        else:
            print('MISSING: ' + str(t.artist) + ' - ' + str(t.title))
    
    # Use existing playlist if exists and user wants to add to it; otherwise create new playlist
    playlist_id = None
    if not always_create_new_playlist:
        print('**** SEARCHING FOR PLAYLIST: "' + args.playlist + '" ****')
        playlist_id = sp.search_playlist(args.playlist)
        if playlist_id is not None:
            print('**** FOUND IT! ****')
    
    if playlist_id is None: 
        print('**** CREATING PLAYLIST: "' + args.playlist + '" ****')
        playlist_id = sp.create_playlist(args.playlist)
    
    # add tracks to playlist
    print('**** ADDING FOUND TRACKS TO PLAYLIST: "' + args.playlist + '" ****')
    sp.playlist_add(playlist_id, tracks) # FIXME Handle duplicate tracks appropriately

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
        # Fetch playlists from spotipy
        playlists = self.sp.user_playlists(self.username)
        
        # Enumerate playlist items and search for title (accounting for pagination) # FIXME Cleaner implementation?
        while playlists:
            for playlist in playlists['items']:
                if playlist['name'] == title:                    
                    return playlist['id']
            if playlists['next']:
                playlists = self.sp.next(playlists)
            else:
                return None

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
        #self.KEXP_BASE_URL = 'http://www.kexp.org/playlist'
        self.KEXP_BASE_URL = 'http://cache.kexp.org/cache/plays'

    def get_tracks(self, start_datetime_utc, end_datetime_utc): 
        tracks = []

        request_details = { 'startTime': start_datetime_utc.isoformat(timespec='minutes'),
                            'endTime': end_datetime_utc.isoformat(timespec='minutes'), 
                            'channel': '1'}
        r = requests.get(self.KEXP_BASE_URL, params=request_details) 

        # FIXME Check for HTTP 200 response

        # parse json track listings
        playlist_json = r.json()

        # for each track, create a track instance and add to array
        for track_listing in playlist_json['Plays']:
            # ignore air breaks  # FIXME What are the other track listing types?
            if track_listing['Type'] == 1:
                if track_listing['Artist'] is not None and track_listing['Track'] is not None:
                    tracks.append(track(artist=track_listing['Artist']['Name'], 
                                        title=track_listing['Track']['Name']))
        return tracks


if __name__ == '__main__': main()
