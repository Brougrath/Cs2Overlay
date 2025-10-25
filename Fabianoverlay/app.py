from flask import Flask, jsonify, render_template
import requests
import time
import logging
from datetime import datetime, timezone
import config

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_cache = {
    "last_fetch": 0,
    "data": None
}

def validate_api_key():
    """Validiert den Leetify API Key"""
    logger.info("Validiere API Key...")
    
    if config.API_KEY == "DEIN_LEETIFY_API_KEY":
        logger.error("API Key nicht konfiguriert! Bitte in config.py einen gültigen API Key eintragen.")
        raise ValueError("API Key nicht konfiguriert")
    
    headers = {
        "_leetify_key": config.API_KEY,
        "Accept": "application/json"
    }
    
    try:
        validate_resp = requests.get(f"{config.API_BASE}/api-key/validate", headers=headers)
        if validate_resp.status_code == 200:
            logger.info("API Key ist gültig")
            return True
        elif validate_resp.status_code == 401:
            logger.error("API Key ist ungültig")
            raise ValueError("Ungültiger API Key")
        else:
            logger.error(f"Fehler bei der API Key Validierung: Status {validate_resp.status_code}")
            raise Exception(f"API Key Validierung fehlgeschlagen: {validate_resp.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Fehler bei der API Key Validierung: {str(e)}")
        raise

def fetch_data_from_leetify():
    """Holt Spielerdaten von der Leetify API"""
    logger.info("Starte API-Abfrage...")
    
    # Validiere API Key vor der Abfrage
    validate_api_key()
    
    headers = {
        "_leetify_key": config.API_KEY,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # API v3 Endpunkte mit steam64_id query parameter
    endpoints = {
        "stats": f"{config.API_BASE}/v3/profile?steam64_id={config.STEAM_ID}",
        "matches": f"{config.API_BASE}/v3/profile/matches?steam64_id={config.STEAM_ID}"
    }
    
    logger.info(f"Verwende API Endpunkte: {endpoints}")
    logger.info(f"Verwende Headers: {headers}")
    
    # Requests Session mit Retry-Logik
    session = requests.Session()
    session.headers.update(headers)
    
    try:
        # Statistiken abrufen
        logger.info("Rufe Statistiken ab...")
        stats_resp = session.get(endpoints["stats"])
        logger.info(f"Stats Response Status: {stats_resp.status_code}")
        logger.info(f"Stats Response Headers: {dict(stats_resp.headers)}")
        logger.info(f"Stats Response Text: {stats_resp.text[:500]}")  # Erste 500 Zeichen des Responses
        
        if stats_resp.status_code != 200:
            logger.error(f"API Error (Stats): Status {stats_resp.status_code}")
            logger.error(f"Response: {stats_resp.text}")
            raise Exception(f"API Error: {stats_resp.status_code} - {stats_resp.text}")
        
        stats_data = stats_resp.json()
        logger.info("========================= STATS RESPONSE START =========================")
        logger.info("Raw stats response (first 1000 chars):")
        logger.info(stats_resp.text[:1000])
        logger.info("Complete stats_data object:")
        logger.info(stats_data)
        logger.info("========================= STATS RESPONSE END =========================")
        logger.info("Stats Data erfolgreich geladen")
        
        # Letzte Matches abrufen
        logger.info("Rufe Matches ab...")
        matches_resp = session.get(endpoints["matches"])
        logger.info(f"Matches Response Status: {matches_resp.status_code}")
        logger.info(f"Matches Response Headers: {dict(matches_resp.headers)}")
        
        try:
            response_text = matches_resp.text
            logger.info(f"Matches Response Text: {response_text[:500]}")  # Erste 500 Zeichen des Responses
        except Exception as e:
            logger.error(f"Fehler beim Lesen der Response: {str(e)}")
            response_text = "Unable to read response text"

        if matches_resp.status_code == 404:
            logger.error("404 Error - Endpoint nicht gefunden")
            logger.error(f"Versuchter Endpoint: {endpoints['matches']}")
            raise Exception(f"API Endpoint nicht gefunden: {endpoints['matches']}")
        elif matches_resp.status_code != 200:
            logger.error(f"API Error (Matches): Status {matches_resp.status_code}")
            logger.error(f"Response: {response_text}")
            raise Exception(f"API Error: {matches_resp.status_code} - {response_text}")
            
        try:
            matches_data = matches_resp.json()
            logger.info(f"Raw matches response: {matches_resp.text[:1000]}")  # Log the first 1000 chars
            logger.info(f"Parsed matches_data: {matches_data}")
        except ValueError as e:
            logger.error(f"JSON Parse Error: {str(e)}")
            logger.error(f"Raw Response: {response_text}")
            raise Exception("Invalid JSON response from API")
        logger.info("Matches Data erfolgreich geladen")
        
        # Daten extrahieren und formatieren
        logger.info("Extrahiere Daten aus API Response...")
        
        try:
            # Log full response structure
            logger.info(f"Full stats_data structure: {stats_data}")
            
            # Log data at each step of extraction
            logger.info("========================= STATS EXTRACTION START =========================")
            
            # Stats are in nested structures, let's check each level
            stats = stats_data.get('stats', {})
            logger.info(f"Stats object: {stats}")
            
            cs2_stats = stats.get('cs2', {})
            logger.info(f"CS2 stats object: {cs2_stats}")
            
            competitive = cs2_stats.get('competitive', {})
            logger.info(f"Competitive stats: {competitive}")
            
            # Extract only the needed stats
            logger.info(f"Full stats_data: {stats_data}")
            
            # Get premier rating number with validation and type conversion
            ranks = stats_data.get('ranks', {})
            logger.info(f"Ranks data: {ranks}")
            premier_rating = ranks.get('premier')
            logger.info(f"Raw premier rating: {premier_rating} (type: {type(premier_rating)})")
            
            # Handle the premier rating value
            if premier_rating is None:
                premier_rating = '-'
            elif isinstance(premier_rating, (int, float)):
                premier_rating = str(int(premier_rating))  # Convert to integer before string
            else:
                premier_rating = str(premier_rating)
            
            # Determine a numeric premier rating for color classification.
            # `premier_rating` was converted to a string above for display purposes,
            # so extract a numeric value from the original ranks payload if possible.
            premier_numeric = None
            raw_premier = ranks.get('premier')
            try:
                if isinstance(raw_premier, (int, float)):
                    premier_numeric = int(raw_premier)
                else:
                    # try parsing the string (if it was converted earlier)
                    premier_numeric = int(str(raw_premier))
            except Exception:
                premier_numeric = None

            if premier_numeric is None:
                premier_color = "#fafafa"
            elif premier_numeric >= 29999:
                premier_color = "#ff5e5e"
            elif premier_numeric >= 24999:
                premier_color = "#d250d6"
            elif premier_numeric >= 19999:
                premier_color = "#8559ff"
            elif premier_numeric >= 14999:
                premier_color = "#2e5eff"
            elif premier_numeric >= 9999:
                premier_color = "#5b9ac4"
            elif premier_numeric >= 4999:
                premier_color = "#a5a5a5"
            else:
                premier_color = "#ffd20c"
                
            logger.info(f"Final premier rating: {premier_rating}")

            # Calculate total K/D ratio from all matches
            kd_ratio = "-"  # Default value
            total_kills = 0
            total_deaths = 0
            
            if matches_data:
                logger.info(f"Processing {len(matches_data)} matches")
                
                # Calculate total kills and deaths across all matches
                for idx, match in enumerate(matches_data):
                    match_stats = match.get('stats', [])
                    if not match_stats:
                        continue
                        
                    for player_stats in match_stats:
                        if player_stats.get('steam64_id') == config.STEAM_ID:
                            kills = int(player_stats.get('total_kills', 0))
                            deaths = int(player_stats.get('total_deaths', 0))
                            
                            total_kills += kills
                            total_deaths += deaths
                            
                            if deaths > 0:
                                current_kd = kills / deaths
                            else:
                                current_kd = kills
                                
                            logger.info(f"Match {idx + 1}: Kills={kills}, Deaths={deaths}, Current K/D={current_kd:.2f}")
                            break
                
                # Calculate overall K/D ratio
                if total_deaths > 0:
                    kd = total_kills / total_deaths
                    kd_ratio = f"{kd:.2f}"
                    logger.info(f"Total K/D calculation - Kills: {total_kills}, Deaths: {total_deaths}, K/D: {kd_ratio}")
                elif total_kills > 0:
                    kd_ratio = f"{total_kills}.00"  # Perfect K/D - no deaths
                    logger.info(f"Perfect K/D - Kills: {total_kills}, Deaths: 0")
                else:
                    logger.info("No kills or deaths recorded, leaving K/D as '-'")
            
            logger.info(f"Final values - Premier: {premier_rating}, KD: {kd_ratio}")
            logger.info("========================= STATS EXTRACTION END =========================")
            
            # Get current map and match outcome from matches
            current_map = "-"
            match_outcome = "-"
            
            # Matches data is now directly an array
            if isinstance(matches_data, list) and len(matches_data) > 0:
                current_match = matches_data[0]
                current_map = current_match.get('map_name', '-')
                
                # Get match outcome from team scores
                team_scores = current_match.get('team_scores', [])
                match_stats = current_match.get('stats', [])
                
                if team_scores and match_stats:
                    # Find player's team
                    player_team = None
                    for stat in match_stats:
                        if stat.get('steam64_id') == config.STEAM_ID:
                            player_team = stat.get('initial_team_number')
                            break
                            
                    if player_team:
                        team1_score = None
                        team2_score = None
                        for score in team_scores:
                            if score['team_number'] == player_team:
                                team1_score = score['score']
                            else:
                                team2_score = score['score']
                                
                        if team1_score is not None and team2_score is not None:
                            if team1_score > team2_score:
                                match_outcome = "Win"
                            elif team1_score < team2_score:
                                match_outcome = "Loss"
                            else:
                                match_outcome = "Tie"
                
                logger.info(f"Extracted current map: {current_map} with outcome: {match_outcome}")
            
            # Format map with outcome and color coding
            if match_outcome == "Win":
                color = "#00ff00"  # Green
            elif match_outcome == "Loss":
                color = "#ff0000"  # Red
            else:
                color = "#ffffff"  # White
            
            # Only show the map name itself; color it based on match outcome
            map_display = f'<span style="color: {color}">{current_map}</span>' if match_outcome != "-" else current_map
            
            # Build display for premier rating with color
            if premier_rating != '-':
                premier_display = f'<span style="color: {premier_color}">{premier_rating}</span>'
            else:
                premier_display = premier_rating

            # Compute Elo gain for today: difference from before first match today to after last match today
            elo_gained = None
            elo_display = "-"

            try:
                # Build sorted list of matches with parsed finished_at datetimes (local timezone)
                sorted_matches = []
                for m in matches_data:
                    finished_at = m.get('finished_at')
                    if not finished_at:
                        continue
                    ts = finished_at
                    try:
                        # Normalize ISO Z format by stripping trailing Z and parsing, then attach UTC tzinfo
                        if ts.endswith('Z'):
                            ts_clean = ts[:-1]
                            dt = datetime.fromisoformat(ts_clean)
                            dt = dt.replace(tzinfo=timezone.utc).astimezone()
                        else:
                            dt = datetime.fromisoformat(ts)
                            if dt.tzinfo is None:
                                dt = dt.replace(tzinfo=timezone.utc).astimezone()
                    except Exception:
                        # Fallback to common format parser
                        try:
                            dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ")
                            dt = dt.replace(tzinfo=timezone.utc).astimezone()
                        except Exception:
                            # Can't parse this match time, skip
                            continue
                    sorted_matches.append((dt, m))

                # Sort chronologically (oldest first)
                sorted_matches.sort(key=lambda x: x[0])

                today = datetime.now().date()
                todays = [(dt, m) for dt, m in sorted_matches if dt.date() == today]

                if todays:
                    first_dt, first_match = todays[0]
                    last_dt, last_match = todays[-1]

                    # find index of first match in the full sorted list
                    idx = None
                    for i, (dt, m) in enumerate(sorted_matches):
                        if m is first_match and dt == first_dt:
                            idx = i
                            break

                    # after_rank = rating after the last match of today
                    after_rank = last_match.get('rank')
                    try:
                        after_rank = int(after_rank) if after_rank is not None else None
                    except Exception:
                        after_rank = None

                    before_rank = None
                    if idx is not None and idx > 0:
                        prev_match = sorted_matches[idx-1][1]
                        before_rank = prev_match.get('rank')
                        try:
                            before_rank = int(before_rank) if before_rank is not None else None
                        except Exception:
                            before_rank = None

                    if before_rank is not None and after_rank is not None:
                        elo_gained = after_rank - before_rank
                        if elo_gained > 0:
                            elo_color = "#00ff00"
                            elo_display = f'<span style="color: {elo_color}">+{elo_gained}</span>'
                        elif elo_gained < 0:
                            elo_color = "#ff0000"
                            elo_display = f'<span style="color: {elo_color}">{elo_gained}</span>'
                        else:
                            elo_color = "#ffffff"
                            elo_display = f'<span style="color: {elo_color}">0</span>'
                    else:
                        # Unable to determine before-first-match rating (no prior match in dataset)
                        # We intentionally do not guess; show '-' to indicate unavailable
                        elo_gained = None
                        elo_display = '-'
                else:
                    # No matches today
                    elo_gained = 0
                    elo_display = '<span style="color: #ffffff">±0</span>'
            except Exception as e:
                logger.error(f"Elo calculation failed: {e}")
                elo_gained = None
                elo_display = '-'

            data = {
                "current_map": map_display,
                "premier_rating": premier_display,
                "kd_ratio": kd_ratio,
                "elo": elo_display,
                "elo_numeric": elo_gained,
                "last_updated": datetime.now().strftime("%H:%M:%S"),
                "timestamp": time.time()
            }
            
            logger.info("========================= FINAL DATA START =========================")
            logger.info(f"Data being sent to frontend: {data}")
            logger.info("========================= FINAL DATA END =========================")
            
        except Exception as e:
            logger.error(f"Fehler bei der Datenextraktion: {str(e)}")
            logger.error(f"Stats Data: {stats_data}")
            logger.error(f"Matches Data: {matches_data}")
            raise
        
        logger.info(f"Extrahierte Daten: {data}")
        
        logger.info(f"Daten erfolgreich von Leetify abgerufen: {data}")
        return data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Fehler beim Abrufen der Leetify-Daten: {str(e)}")
        logger.error(f"Response Status: {e.response.status_code if hasattr(e, 'response') else 'No response'}")
        logger.error(f"Response Text: {e.response.text if hasattr(e, 'response') else 'No response'}")
        raise

@app.route("/data")
@app.route("/api/data")
def data():
    """API Endpunkt für Overlay-Daten"""
    now = time.time()
    try:
        if _cache["data"] is None or now - _cache["last_fetch"] > config.REFRESH_INTERVAL:
            _cache["data"] = fetch_data_from_leetify()
            _cache["last_fetch"] = now
        # Prevent HTML escaping by marking the response as safe
        response = jsonify(_cache["data"])
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response
    except Exception as e:
        logger.error(f"Fehler beim Datenabruf: {str(e)}")
        logger.error(f"Exception type: {type(e)}")
        logger.error(f"Exception traceback: ", exc_info=True)
        return jsonify({
            "error": f"Fehler beim Datenabruf: {str(e)}",
            "current_map": "-",
            "premier_rating": "-",
            "kd_ratio": "-",
            "last_updated": "-"
        }), 500

@app.route("/test")
def test():
    """Test-Route für direkte API-Antworten"""
    try:
        headers = {
            "_leetify_key": config.API_KEY,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        logger.info(f"Testing with headers: {headers}")

        session = requests.Session()
        session.verify = True
        session.headers.update(headers)

        # Use configured API_BASE and documented v3 profile endpoints (query params)
        stats_url = f"{config.API_BASE}/v3/profile?steam64_id={config.STEAM_ID}"
        matches_url = f"{config.API_BASE}/v3/profile/matches?steam64_id={config.STEAM_ID}"

        logger.info(f"Trying stats URL: {stats_url}")
        try:
            stats_resp = session.get(stats_url)
            logger.info(f"Stats response code: {stats_resp.status_code}")
            logger.info(f"Stats headers: {dict(stats_resp.headers)}")
            logger.info(f"Stats text: {stats_resp.text[:200]}")
        except Exception as e:
            logger.error(f"Stats request failed: {str(e)}")
            stats_resp = type('Response', (), {'status_code': 500, 'text': str(e), 'headers': {}})()

        logger.info(f"Trying matches URL: {matches_url}")
        try:
            matches_resp = session.get(matches_url)
            logger.info(f"Matches response code: {matches_resp.status_code}")
            logger.info(f"Matches headers: {dict(matches_resp.headers)}")
            logger.info(f"Matches text: {matches_resp.text[:200]}")
        except Exception as e:
            logger.error(f"Matches request failed: {str(e)}")
            matches_resp = type('Response', (), {'status_code': 500, 'text': str(e), 'headers': {}})()

        return jsonify({
            "stats_status": stats_resp.status_code,
            "stats_headers": dict(stats_resp.headers),
            "stats_data": stats_resp.text,
            "matches_status": matches_resp.status_code,
            "matches_headers": dict(matches_resp.headers),
            "matches_data": matches_resp.text,
            "api_key_used": config.API_KEY,
            "steam_id_used": config.STEAM_ID
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "type": str(type(e))
        }), 500


@app.route("/validate-key")
def validate_key_route():
    """Diagnostic route: validates the configured Leetify API key and returns a simple JSON result."""
    try:
        validate_api_key()
        return jsonify({"valid": True}), 200
    except ValueError as ve:
        # invalid API key (mapped from validate_api_key)
        return jsonify({"valid": False, "error": str(ve)}), 401
    except Exception as e:
        # other errors (server/network)
        logger.error(f"Error validating API key: {str(e)}")
        return jsonify({"valid": False, "error": str(e)}), 500

@app.route("/")
def index():
    """Rendert das Overlay-Template"""
    return render_template("index.html")

if __name__ == "__main__":
    logger.info("Starting Leetify Overlay Server...")
    logger.info(f"API Key being used: {config.API_KEY}")
    logger.info(f"Steam ID being used: {config.STEAM_ID}")
    app.run(host="0.0.0.0", port=5000, debug=True)
