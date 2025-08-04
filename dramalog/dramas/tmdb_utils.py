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

        # 🔁 NEW: Fetch full details using ID
        detail_url = f"https://api.themoviedb.org/3/tv/{tmdb_id}"
        detail_params = {
            "api_key": TMDB_API_KEY,
            "language": "en-US"
        }
        detail_response = requests.get(detail_url, params=detail_params)
        detail_data = detail_response.json()

        return {
            "title": first["name"], 
            "description": first["overview"],
            "poster_url": f"https://image.tmdb.org/t/p/w500{first['poster_path']}" if first.get("poster_path") else None,
            "release_year": first["first_air_date"][:4],
            "tmdb_id": tmdb_id,
            "total_episodes": detail_data.get("number_of_episodes", 0)
        }

    return None

