import platform
import subprocess
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import webbrowser
from collections import deque


SPOTIFY_CLIENT_ID = "SPOTIFY_CLIENT_ID"
SPOTIFY_CLIENT_SECRET = "SPOTIFY_CLIENT_SECRET"
SPOTIFY_REDIRECT_URI = "http://localhost:8888/callback"
SCOPE = "user-read-playback-state,user-modify-playback-state"

# Initialize Spotify client with a custom cache path
cache_path = ".spotify_cache"
auth_manager = SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope=SCOPE,
    cache_path=cache_path,
    open_browser=True  # This will open the default browser
)




# Add these global variables
volume_stack = deque()
current_volume = 80  # Initial volume


# Function to handle Spotify authorization
def authorize_spotify():
    token_info = auth_manager.get_cached_token()
    if not token_info:
        auth_url = auth_manager.get_authorize_url()
        print(f"Please visit this URL to authorize the application: {auth_url}")
        webbrowser.open(auth_url)  # This will open the default browser
        response = input("Enter the URL you were redirected to: ")
        code = auth_manager.parse_response_code(response)
        token_info = auth_manager.get_access_token(code)
    return token_info


# Initialize Spotify client
try:
    token_info = authorize_spotify()
    sp = spotipy.Spotify(auth_manager=auth_manager)
    print("Successfully authenticated with Spotify!")
except Exception as e:
    print(f"Failed to initialize Spotify client: {e}")
    sp = None




def play_spotify_song(query):
    global sp, currently_playing, current_volume
    if sp is None:
        return "Sorry, Spotify is not available at the moment."
    
    try:
        print(f"Searching for song: {query}")
        results = sp.search(q=query, type="track", limit=1)
        if results["tracks"]["items"]:
            track = results["tracks"]["items"][0]
            track_uri = track["uri"]
            track_name = track["name"]
            artist_name = track["artists"][0]["name"]
            
            # Get available devices
            devices = sp.devices()
            available_devices = devices['devices']
            
            if not available_devices:
                print("No Spotify devices found. Attempting to launch Spotify client...")
                # Launch Spotify based on operating system
                if platform.system() == "Darwin":  # macOS
                    subprocess.Popen(["open", "-a", "Spotify"])
                elif platform.system() == "Windows":
                    subprocess.Popen(["start", "spotify:"], shell=True)
                elif platform.system() == "Linux":
                    subprocess.Popen(["spotify"])
                
                # Wait for Spotify to launch and register as a device
                max_attempts = 10
                for attempt in range(max_attempts):
                    time.sleep(2)  # Wait for 2 seconds between checks
                    devices = sp.devices()
                    available_devices = devices['devices']
                    if available_devices:
                        print("Spotify client launched successfully!")
                        break
                    if attempt == max_attempts - 1:
                        return "Could not find or launch Spotify. Please make sure Spotify is installed and try again."
            
            device_id = available_devices[0]['id']
            device_name = available_devices[0]['name']
            
            # Ensure the device is active
            sp.transfer_playback(device_id=device_id, force_play=True)
            time.sleep(2)  # Wait for device to activate
            
            # Set volume to current_volume before playing
            sp.volume(current_volume, device_id=device_id)
            sp.start_playback(device_id=device_id, uris=[track_uri])
            currently_playing = True
            return f"Now playing {track_name} by {artist_name} on {device_name} at {current_volume}% volume."
        else:
            return "Sorry, I couldn't find that song on Spotify."
    except Exception as e:
        print(f"An error occurred while playing the song: {e}")
        return "Sorry, an error occurred while trying to play the song."

def stop_spotify_playback():
    global sp, currently_playing
    if sp is None:
        return "Sorry, Spotify is not available at the moment."
    
    try:
        sp.pause_playback()
        currently_playing = False
        return "Playback stopped."
    except Exception as e:
        print(f"An error occurred while stopping playback: {e}")
        return "Sorry, an error occurred while trying to stop the playback."
