import os
from flask import Flask, request, redirect, render_template, session, url_for
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask_session import Session
from functools import wraps
from dotenv import load_dotenv
import lyricsgenius as lg
import re

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = 'http://127.0.0.1:5000/callback'
GENIUS_CLIENT = os.getenv("GENIUS_CLIENT_TOKEN")

def spotifyOAuth():
    return SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope="user-library-read user-read-currently-playing playlist-modify-private playlist-modify-public user-modify-playback-state playlist-read-private",
        show_dialog=True
    )


def login_required(f):
    @wraps(f)
    def decorated_function(*args,**kwargs):
        if 'token_info' not in session:
            return redirect(url_for('login'))
        return f(*args,**kwargs)
    return decorated_function

def fetch_current_track(token_info):
    sp = spotipy.Spotify(auth=token_info['access_token'])
    results = sp.current_user_playing_track()

    if results and results.get('item'):
        track = results['item']
        return {
            "is_playing": results['is_playing'],
            "track_id": track['id'],
            "track_name": track['name'],
            "track_uri": track['uri'],
            "track_image": track['album']['images'][0]['url'],
            "album_name": track['album']['name'],
            "artist_name": [artist['name'] for artist in track['artists']],
            "lyrics" : get_lyrics(track['name'],[artist['name'] for artist in track['artists']])
        }
    return {"track_id": None}

def clean_string(input_string):
    input_string = re.sub(r'\s*\(.*?\)\s*', '', input_string)
    input_string = re.sub(r'[^\w\s]', '', input_string)
    return input_string.strip()

def get_lyrics(track_name, artist_name):
    genius = lg.Genius(GENIUS_CLIENT)
    clean_track_name = clean_string(track_name)
    try:
        for artist in artist_name:
            clean_artist_name = clean_string(artist)
            song = genius.search_song(clean_track_name, clean_artist_name)
            if clean_string(song.title) == clean_track_name and clean_string(song.artist) == clean_artist_name:
                print(f"Found song: {song.title} by {song.artist}")
                lyrics = song.lyrics
                lyrics_lines = lyrics.split('\n')
                if len(lyrics_lines) > 1:
                    lyrics = '\n'.join(lyrics_lines[1:])
                return lyrics
        else:
            return 'Lyrics not found'
    except Exception as e:
        print(f"Error fetching lyrics: {e}")
        return 'Lyrics not found'


def get_playlists(token_info):
    sp = spotipy.Spotify(auth=token_info['access_token'])
    results = sp.current_user_playlists()
    playlists = results['items']
    playlists_details = []
    for playlist in playlists:
        owner = sp.user(playlist['owner']['id'])
        playlist_info = {
            'playlist_id': playlist['id'],
            'playlist_name': playlist['name'],
            'description': re.sub(r'<a[^>]*>(.*?)</a>', r'\1',playlist['description']),
            'playlist_image': playlist['images'][0]['url'] if playlist['images'] else None,
            'owner_id': owner['id'],
            'owner_name': owner['display_name'],
            'owner_image': owner['images'][0]['url'] if owner['images'] else None,
            'total_tracks': playlist['tracks']['total']
        }
        playlists_details.append(playlist_info)
    
    return playlists_details
