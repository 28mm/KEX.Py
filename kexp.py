#!/usr/bin/env python3

import json
from urllib import request

from bs4 import BeautifulSoup
import spotipy

def main():
    radio  = kexp()
    tracks = radio.current_tracks()
    print(tracks)




class track:
    def __init__(self, artist='', title='', label=''):
        self.artist = artist
        self.title  = title
        self.label  = label

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
        response = request.urlopen(self.KEXP_BASE_URL + '/' + str(year)         \
                               + '/' + str(month)                      \
                               + '/' + str(day)                        \
                               + '/' + (str(hour) + 'AM'               \
                                            if hour < 13               \
                                            else str(hour-12) + 'PM'))
        return response


if __name__ == '__main__': main()
