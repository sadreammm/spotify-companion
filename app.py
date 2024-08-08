import os
from flask import Flask, request, redirect, render_template, session, url_for, jsonify
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask_session import Session
import time
import re


from functions import spotifyOAuth, login_required, fetch_current_track, get_lyrics, get_playlists
app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SESSION_COOKIE_NAME'] = 'spotify-cookie'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

TOKEN_INFO = 'token_info'

@app.route('/')
@login_required
def index():
    try:
        token_info = get_token()
    except:
        print("User not logged in")
        return redirect('/login')

    track_info = fetch_current_track(token_info)
    display_name = session['user_info']['display_name']
    return render_template('index.html', track=track_info)

@app.route('/current-track')
@login_required
def current_track():
    try:
        token_info = get_token()
    except:
        print("User not logged in")
        return {'track_id' : None}

    track_info = fetch_current_track(token_info)
    if track_info['track_id'] is None:
        return {"track_id": None}
    return track_info


@app.route('/login')
def login():
    sp_oauth = spotifyOAuth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)


@app.route('/songs', methods=["POST"])
@login_required
def songs():
    track = request.form.get('track')
    token_info = get_token()
    sp = spotipy.Spotify(auth=token_info['access_token'])
    results = sp.search(q=track, type="track")
    tracks = results['tracks']['items']
    owner_id = sp.current_user()['id']

    track_details = []

    playlists = sp.current_user_playlists()['items']

    for track in tracks:
        track_info = {
            'uri' : track['uri'],
            'id': track['id'],
            'name': track['name'],
            'artist': track['artists'][0]['name'],
            'track_image': track['album']['images'][0]['url'] if track['album']['images'] else None,
        }
        track_details.append(track_info)
    
    playlist_details = []

    for playlist in playlists:
        if owner_id == playlist['owner']['id']:
            playlist_info = {
                'playlist_id' : playlist['id'],
                'playlist_name' : playlist['name']
            }
            playlist_details.append(playlist_info)
    
    return render_template('songs.html', tracks=track_details, playlists = playlist_details)

@app.route('/song/<track_id>')
@login_required
def song(track_id):
    token_info = get_token()
    sp = spotipy.Spotify(auth=token_info['access_token'])
    track = sp.track(track_id)
    artist = sp.artist(track['artists'][0]['id'])
    owner_id = sp.current_user()['id']

    playlists = sp.current_user_playlists()['items']

    track_info = {
        'track_uri':track['uri'],
        'track_image': track['album']['images'][0]['url'] if track['album']['images'] else None,
        'track_name': track['name'],
        "artist_name": [artist['name'] for artist in track['artists']][0],
        'feat_name': [artist['name'] for artist in track['artists'][1:]],
        'album_type': track['album']["album_type"],
        'album_name': track['album']["name"],
        'release_date': track['album']["release_date"],
        'lyrics': get_lyrics(track['name'],[artist['name'] for artist in track['artists']])
    }

    playlist_details = []

    for playlist in playlists:
        if owner_id == playlist['owner']['id']:
            playlist_info = {
                'playlist_id' : playlist['id'],
                'playlist_name' : playlist['name']
            }
            playlist_details.append(playlist_info)

    return render_template('song.html', track_info=track_info, playlists=playlist_details)

@app.route('/add-playlist', methods=['POST'])
@login_required
def add_playlist():
    playlist_id = request.form.get('playlist_id')
    track_uri = request.form.get('track_uri')

    token_info = get_token()
    sp = spotipy.Spotify(auth=token_info['access_token'])

    playlist_tracks = sp.playlist_tracks(playlist_id)['items']
    track_uris = [item['track']['uri'] for item in playlist_tracks]

    if track_uri in track_uris:
        return jsonify({'exists':True, 'playlist_id':playlist_id, 'track_uri':track_uri})
    
    sp.playlist_add_items(playlist_id, [track_uri])
    return jsonify({'exists':False})

@app.route('/confirm-add', methods=['POST'])
@login_required
def confirm():
    playlist_id = request.form.get('playlist_id')
    track_uri = request.form.get('track_uri')

    token_info = get_token()
    sp = spotipy.Spotify(auth=token_info['access_token'])

    sp.playlist_add_items(playlist_id,[track_uri])
    return jsonify({'status':'success'})


@app.route('/playlists')
@login_required
def playlists():
    token_info = get_token()
    playlists_details = get_playlists(token_info)
    return render_template('playlists.html', playlists=playlists_details)
@app.route('/playlist/<playlist_id>')
@login_required
def playlist(playlist_id):
    token_info = get_token()
    sp = spotipy.Spotify(auth=token_info['access_token'])
    owner_id = sp.current_user()['id']
    offset = 0
    limit = 100
    all_tracks = []
    
    while True:
        results = sp.playlist_tracks(playlist_id=playlist_id, offset=offset, limit=limit)
        tracks = results['items']
        
        if not tracks:
            break
        
        for track in tracks:
            track_info = {
                'uri': track['track']['uri'],
                'track_id': track['track']['id'],
                'track_image': track['track']['album']['images'][0]['url'] if track['track']['album']['images'] else None,
                'track_name': track['track']['name'],
                'artist_name': [artist['name'] for artist in track['track']['artists']],
                'popularity': track['track']['popularity']
            }
            all_tracks.append(track_info)
        
        offset += limit
        if len(tracks) < limit:
            break

    playlist_details = []
    playlists = get_playlists(token_info)
    for playlist in playlists:
        if playlist['playlist_id'] == playlist_id:
            playlist_details.append(playlist)

    return render_template(
        "playlist_tracks.html", playlist=all_tracks, playlist_details=playlist_details, playlist_id=playlist_id, owner_id=owner_id)

@app.route('/delete-track', methods=["POST"])
@login_required
def delete():
    playlist_id = request.form.get('playlist_id')
    track_uri = request.form.get('track_uri')
    token_info = get_token()
    sp=spotipy.Spotify(auth=token_info['access_token'])

    sp.playlist_remove_all_occurrences_of_items(playlist_id,[track_uri])

    return redirect(url_for('playlist',playlist_id=playlist_id))

@app.route('/callback')
def callback():
    sp_oauth = spotifyOAuth()
    session.clear()
    token_info = sp_oauth.get_access_token(request.args['code'])
    session[TOKEN_INFO] = token_info

    sp = spotipy.Spotify(auth=token_info['access_token'])
    user = sp.current_user()
    user_info = {
        'id': user['id'],
        'display_name': user['display_name']
    }
    session['user_info'] = user_info

    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

def get_token():
    token_info = session.get(TOKEN_INFO)
    if not token_info:
        raise Exception("Token not found")

    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 60
    if is_expired:
        sp_oauth = spotifyOAuth()
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session[TOKEN_INFO] = token_info

    return token_info

if __name__ == '__main__':
    app.run(debug=True)
