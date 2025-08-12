# dramas/spotify_utils.py
import os
from typing import Optional
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv

load_dotenv()

client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

_spotify: Optional[Spotify] = None
if client_id and client_secret:
    try:
        _spotify = Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=client_id,
                client_secret=client_secret,
            )
        )
    except Exception:
        # If auth fails, just leave _spotify as None so we skip OST lookup
        _spotify = None

def get_ost_playlist_url(drama_title: str) -> Optional[str]:
    """
    Best-effort Spotify search. Returns a playlist URL or None.
    Never raises.
    """
    if not _spotify:
        return None

    try:
        query = f"{drama_title} OST"
        results = _spotify.search(q=query, type="playlist", limit=5) or {}
        playlists = (results.get("playlists") or {}).get("items") or []
        for item in playlists:
            if not isinstance(item, dict):
                continue
            name = (item.get("name") or "").lower()
            if "ost" in name or "soundtrack" in name or drama_title.lower() in name:
                url = (item.get("external_urls") or {}).get("spotify")
                if url:
                    return url
    except Exception:
        # swallow any Spotify API errors
        return None

    return None
