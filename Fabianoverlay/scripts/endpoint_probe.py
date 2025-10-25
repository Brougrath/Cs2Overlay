import requests
import sys
from pathlib import Path

# Ensure project root is on sys.path so we can import config
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
import config

headers = {"_leetify_key": config.API_KEY, "Accept": "application/json"}

base = config.API_BASE.rstrip('/')
sid = config.STEAM_ID

candidates = [
    f"{base}/v3/profile/{sid}",
    f"{base}/v3/profile/{sid}/matches",
    f"{base}/v3/profile?steam_id={sid}",
    f"{base}/v3/profile?steamId={sid}",
    f"{base}/v3/profile?steam={sid}",
    f"{base}/v3/profile?identifiers=steam:{sid}",
    f"{base}/v3/profile/steam/{sid}",
    f"{base}/v3/profile/steam/{sid}/matches",
    f"{base}/v2/matches/{sid}",
    f"{base}/players/{sid}/stats",
    f"{base}/players/{sid}/matches/latest",
    f"{base}/profile/{sid}",
]

for url in candidates:
    try:
        r = requests.get(url, headers=headers, timeout=10)
        print("URL:", url)
        print("Status:", r.status_code)
        print("Content-Type:", r.headers.get('Content-Type'))
        text = r.text or ''
        print(text[:500])
        print("---\n")
    except Exception as e:
        print("ERROR for", url, e)
