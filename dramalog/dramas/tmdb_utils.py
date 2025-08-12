import os
import requests
from dotenv import load_dotenv

load_dotenv() 

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

def search_kdrama(title):
    url = "https://api.themoviedb.org/3/search/tv"
    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
        "language": "en-US"
    }
    response = requests.get(url, params=params)
    data = response.json()

    if data["results"]:
        first = data["results"][0]
        tmdb_id = first["id"]
        

        # Fetch full details using ID
        detail_url = f"https://api.themoviedb.org/3/tv/{tmdb_id}"
        detail_params = {
            "api_key": TMDB_API_KEY,
            "language": "en-US"
        }
        detail_response = requests.get(detail_url, params=detail_params)

        if detail_response.status_code == 200:
            detail_data = detail_response.json()
            return {
                "title": first["name"], 
                "description": first["overview"],
                "poster_url": f"https://image.tmdb.org/t/p/w500{first['poster_path']}" if first.get("poster_path") else None,
                "release_year": first["first_air_date"][:4],
                "tmdb_id": tmdb_id,
                "total_episodes": detail_data.get("number_of_episodes", 0),
                "genre_names": [g["name"] for g in detail_data.get("genres", [])] 
            }

    return None

def search_kdrama_candidates(title: str, limit: int = 8):
    """
    Return a list of candidate shows for preview (no DB writes).
    """
    url = "https://api.themoviedb.org/3/search/tv"
    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
        "language": "en-US",
        "include_adult": False
    }
    r = requests.get(url, params=params)
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
    url = f"https://api.themoviedb.org/3/tv/{tmdb_id}"
    params = {"api_key": TMDB_API_KEY, "language": "en-US"}
    r = requests.get(url, params=params)
    if r.status_code != 200:
        return None
    d = r.json()
    return {
        "title": d.get("name"),
        "description": d.get("overview"),
        "poster_url": f"https://image.tmdb.org/t/p/w500{d['poster_path']}" if d.get("poster_path") else None,
        "release_year": (d.get("first_air_date") or "")[:4] if d.get("first_air_date") else None,
        "tmdb_id": tmdb_id,
        "total_episodes": d.get("number_of_episodes", 0),
        "genre_names": [g["name"] for g in d.get("genres", [])],
    }