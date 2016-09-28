#!/usr/bin/env python
"""

Use raspbery pi to :
- download 30 second clips from a specific playlist.
- Play the track
- use xiloborg board to detect sudden shocks.
- Change track playing on sudden shocks

"""
# coding: latin-1
import threading
import logging
import XLoBorg
from random import choice
import pygame
import requests
from math import fabs
import sys
import os
import spotipy
import spotipy.util as util
from spotipy import oauth2
pygame.mixer.init()

XLoBorg.printFunction = XLoBorg.NoPrint
XLoBorg.Init()

pygame.init()
SENSITIVITY = 0.7
current = XLoBorg.ReadAccelerometer()
thread = None


def show_tracks(results):
    for i, item in enumerate(tracks['items']):
        track = item['track']
        print("   %d %32.32s %s %s" % (i, track['artists'][0]['name'], track['name'], track['preview_url']))


def get_previews(tracks):
    return [track['track']['preview_url'] for track in tracks['tracks']['items'] if
            track['track']['preview_url'] is not None]


def get_playlist_tracks():
    # type: () -> object
    USERNAME = 'YOUR SPOTIFY USER NAME'
    SPOTIFY_CLIENT_ID = 'YOUR APP ID'
    SPOTIFY_SECRET = 'YOUR APP SECRET KEY'
    tokenobj = oauth2.SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID,
                                               client_secret=SPOTIFY_SECRET
                                               )
    token = tokenobj.get_access_token()
    previews = []
    if token:
        spotify_obj = spotipy.Spotify(auth=token)
        playlists = spotify_obj.user_playlists(USERNAME)
        previews = get_spotify_playlist(USERNAME,
                                        playlists,
                                        previews,
                                        spotify_obj
                                        )
    else:
        print("Can't get token for", USERNAME)
    return previews


def get_spotify_playlist(USERNAME, playlists, previews, spotify_object, spotify_source_playlist='jumperoo'):
    global tracks
    for playlist in playlists['items']:
        if spotify_source_playlist in playlist['name']:
            results = spotify_object.user_playlist(USERNAME, playlist['id'], fields="tracks,next")
            tracks = results['tracks']
            show_tracks(tracks)
            previews = get_previews(results)
        else:
            print '.',
    return previews


def save_previews():
    # type: () -> object
    previews = get_playlist_tracks()
    for i, previewpath in enumerate(previews):
        spotifydownload(filepath=previewpath,
                        filename='music%s.mp3' % str(i)
                        )
    return len(previews)


def spotifydownload(filepath, filename='music.mp3', chunk_size=1024):
    r = requests.get(filepath)
    with open(filename, 'wb') as fd:
        for chunk in r.iter_content(chunk_size):
            fd.write(chunk)


def worker(tracktoplay):
    """thread worker function"""
    pygame.mixer.music.load("music%s.mp3" % tracktoplay)
    pygame.mixer.music.play()
    print 'play music'


def current_accelleration(acc):
    return [fabs(i) for i in acc]


def accelleration_delta(current, prev):
    return [round(fabs(current[i] - prev[i]), 3) for i in range(3)]


def start_jumperoo(trackcount):
    current = (0, 0, 0)
    while True:
        prev = current
        current = current_accelleration(acc=XLoBorg.ReadAccelerometer())
        delta = accelleration_delta(current=current, prev=prev)
        summa = sum(delta)
        if summa > SENSITIVITY:
            main_thread = threading.currentThread()
            for t in threading.enumerate():
                if t is main_thread:
                    continue
                logging.debug('joining %s', t.getName())
                t.join()
            print threading.enumerate()
            tracktoplay = choice(range(0, trackcount))
            thread = threading.Thread(target=worker, args=(tracktoplay,))
            thread.start()


if __name__ == '__main__':
    trackcount = save_previews()
    start_jumperoo(trackcount)
