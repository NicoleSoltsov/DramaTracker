import os
import requests
from dotenv import load_dotenv

load_dotenv() 

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE = "https://api.themoviedb.org/3"

def search_kdrama(title):
    url = f"{TMDB_BASE}/search/tv"
    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
        "language": "en-US"
    }
    response = requests.get(url, params=params, timeout=15)
    data = response.json()

    if data.get("results"):
        first = data["results"][0]
        tmdb_id = first["id"]

        # Fetch full details using ID
        detail_url = f"{TMDB_BASE}/tv/{tmdb_id}"
        detail_params = {"api_key": TMDB_API_KEY, "language": "en-US"}
        detail_response = requests.get(detail_url, params=detail_params, timeout=15)

        if detail_response.status_code == 200:
            detail_data = detail_response.json()
            return {
                "title": first.get("name"), 
                "description": first.get("overview", "") or "",
                "poster_url": f"https://image.tmdb.org/t/p/w500{first['poster_path']}" if first.get("poster_path") else None,
                "release_year": (first.get("first_air_date") or "")[:4] if first.get("first_air_date") else None,
                "tmdb_id": tmdb_id,
                "total_episodes": detail_data.get("number_of_episodes", 0),
                "genre_names": [g["name"] for g in detail_data.get("genres", [])] 
            }

    return None

def search_kdrama_candidates(title: str, limit: int = 8):
    """
    Return a list of candidate shows for preview (no DB writes).
    """
    url = f"{TMDB_BASE}/search/tv"
    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
        "language": "en-US",
        "include_adult": False
    }
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()

    results = []
    for item in (data.get("results") or [])[:limit]:
        results.append({
            "tmdb_id": item.get("id"),
            "title": item.get("name"),
            "overview": item.get("overview"),
            "year": (item.get("first_air_date") or "")[:4] if item.get("first_air_date") else None,
            "poster_url": f"https://image.tmdb.org/t/p/w500{item['poster_path']}" if item.get("poster_path") else None,
        })
    return results

def fetch_kdrama_by_tmdb_id(tmdb_id: int):
    url = f"{TMDB_BASE}/tv/{tmdb_id}"
    params = {"api_key": TMDB_API_KEY, "language": "en-US"}
    r = requests.get(url, params=params, timeout=15)
    if r.status_code != 200:
        return None
    d = r.json()
    return {
        "title": d.get("name"),
        "description": d.get("overview") or "",
        "poster_url": f"https://image.tmdb.org/t/p/w500{d['poster_path']}" if d.get("poster_path") else None,
        "release_year": (d.get("first_air_date") or "")[:4] if d.get("first_air_date") else None,
        "tmdb_id": tmdb_id,
        "total_episodes": d.get("number_of_episodes", 0),
        "genre_names": [g["name"] for g in d.get("genres", [])],
    }

def get_tv_seasons(tmdb_id: int, language: str = "en-US"):
    """
    Returns a list of dicts:
    [{season_number, episode_count, name, air_date, poster_path}]
    Uses /tv/{id} so we avoid one call per season.
    """
    if not TMDB_API_KEY:
        raise RuntimeError("TMDB_API_KEY is not set")

    r = requests.get(
        f"{TMDB_BASE}/tv/{tmdb_id}",
        params={"api_key": TMDB_API_KEY, "language": language},
        timeout=15
    )
    r.raise_for_status()
    data = r.json()

    seasons = []
    for s in data.get("seasons", []):
        seasons.append({
            "season_number": s.get("season_number"),
            "episode_count": s.get("episode_count"),
            "name": s.get("name"),
            "air_date": s.get("air_date"),
            "poster_path": s.get("poster_path"),
        })
    # caller may sort; we keep raw order
    return seasons
