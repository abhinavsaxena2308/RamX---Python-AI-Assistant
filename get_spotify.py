from livekit.agents import function_tool, RunContext

@function_tool()
async def spotify_control(
    context: RunContext,
    action: str,
    track_name: str = None,
    open_in_browser: bool = True
) -> str:
    """
    Control Spotify playback for Premium users, or provide links for Free users.

    Parameters:
    - action: The action to perform (play, pause, resume, next, previous, current)
    - track_name: Name of the track to play (required for 'play' action)
    - open_in_browser: For Free users, whether to open track URL in the browser

    Returns:
    - A string indicating the result
    """
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth
    import os
    import webbrowser

    # Set up cache folder
    CACHE_DIR = os.path.join(os.path.expanduser("~"), "spotify_cache")
    os.makedirs(CACHE_DIR, exist_ok=True)
    CACHE_PATH = os.path.join(CACHE_DIR, ".cache")

    # Load environment variables
    SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
    SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
    SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:8888/callback")

    # Initialize Spotipy
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope="user-read-playback-state,user-modify-playback-state,user-read-currently-playing",
        cache_path=CACHE_PATH,
        open_browser=True
    ))

    # Normalize action
    action = action.lower()

    try:
        # Search for track if needed
        track_uri = None
        track_url = None
        if action == "play" and track_name:
            results = sp.search(q=track_name, type='track', limit=1)
            if results['tracks']['items']:
                track = results['tracks']['items'][0]
                track_uri = track['uri']
                track_url = track['external_urls']['spotify']
            else:
                return f"Sorry, I couldn't find the track '{track_name}'."

        # Get active device
        devices = sp.devices()
        if devices['devices']:
            device_id = devices['devices'][0]['id']
            is_premium = True
        else:
            device_id = None
            is_premium = False

        # PREMIUM USER PLAYBACK
        if is_premium:
            if action == "play":
                sp.start_playback(device_id=device_id, uris=[track_uri])
                return f"🎶 Playing '{track['name']}' by {track['artists'][0]['name']} on Spotify Premium."
            elif action == "pause":
                sp.pause_playback(device_id=device_id)
                return "⏸️ Music paused."
            elif action == "resume":
                sp.start_playback(device_id=device_id)
                return "▶️ Music resumed."
            elif action == "next":
                sp.next_track(device_id=device_id)
                return "⏭️ Skipped to the next track."
            elif action == "previous":
                sp.previous_track(device_id=device_id)
                return "⏮️ Went back to the previous track."
            elif action == "current":
                current = sp.currently_playing()
                if current and current['item']:
                    track = current['item']
                    return f"🎧 Currently playing '{track['name']}' by {track['artists'][0]['name']}."
                return "No track is currently playing."
            else:
                return "Invalid action. Use play, pause, resume, next, previous, or current."

        # FREE USER: provide link only
        else:
            if action == "play":
                if track_url:
                    if open_in_browser:
                        webbrowser.open(track_url)
                    return f"⚠️ Spotify Free account detected. Cannot play directly.\nYou can listen here: {track_url}"
                return "⚠️ Track not found."
            else:
                return "⚠️ Spotify Free account detected. Only 'play' action with track links is supported."

    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 403:
            return "⚠️ Playback failed: your Spotify account may not be Premium or no active device is available."
        return f"An error occurred while controlling Spotify: {str(e)}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"
