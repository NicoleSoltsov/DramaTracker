# dramas/spotify_utils.py
import os
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv

load_dotenv()

client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

sp = Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))

def get_ost_playlist_url(drama_title):
    query = f"{drama_title} OST"
    results = sp.search(q=query, type="playlist", limit=3)
    playlists = results.get('playlists', {}).get('items', [])
    
    for playlist in playlists:
        name = playlist.get("name", "").lower()
        if "ost" in name or "soundtrack" in name:
            return playlist["external_urls"]["spotify"]
    
    return None
