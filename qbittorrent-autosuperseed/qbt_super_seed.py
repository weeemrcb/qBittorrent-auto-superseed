import requests
import time
import sys
import os

# --- Configuration ---
# Read configuration from environment variables.
# Provide default values if environment variables are not set.
QB_HOST = os.getenv('QB_HOST', 'host.docker.internal')
QB_PORT = os.getenv('QB_PORT', '8080')
QB_USERNAME = os.getenv('QB_USERNAME', '')
QB_PASSWORD = os.getenv('QB_PASSWORD', '')
POLLING_INTERVAL_SECONDS = int(os.getenv('POLLING_INTERVAL_SECONDS', 600))

# Super Seeding activation thresholds
# QB_SUPER_SEED_SEED_THRESHOLD: The number of total seeds at which to consider enabling Super Seeding.
#   If total seeds are equal to this value AND leech count meets the threshold, Super Seeding is enabled.
#   A value of 1 means "only I am seeding."
QB_SUPER_SEED_SEED_THRESHOLD = int(os.getenv('QB_SUPER_SEED_SEED_THRESHOLD', 1))

# QB_SUPER_SEED_LEECH_THRESHOLD: The minimum number of leeches (downloaders) required
#   for Super Seeding to be enabled, when total seeds meet the seed threshold.
QB_SUPER_SEED_LEECH_THRESHOLD = int(os.getenv('QB_SUPER_SEED_LEECH_THRESHOLD', 3))

# --- New Configuration for Choking Algorithm ---
# QB_ENABLE_CHOKING_ALGORITHM_CONTROL: Set to 'True' to enable automatic switching of the
#   upload choking algorithm. If 'False', this feature is disabled.
QB_ENABLE_CHOKING_ALGORITHM_CONTROL = os.getenv('QB_ENABLE_CHOKING_ALGORITHM_CONTROL', 'False').lower() == 'true'

# Global variable to keep track of the current choking algorithm to avoid redundant API calls
# 0: Anti-Leech, 1: Fastest Upload
# Initialize to -1 to ensure the first set call happens
current_choking_algorithm_state = -1

# --- Helper Function for qBittorrent API URLs ---
def get_qb_url(path):
    """Constructs the full URL for a qBittorrent API endpoint."""
    return f"http://{QB_HOST}:{QB_PORT}{path}"

# --- qBittorrent API Interaction Functions ---

def login(session, username, password):
    """
    Logs into the qBittorrent Web UI using the provided credentials.
    If username/password are empty, it attempts to connect without credentials.
    Returns True on successful login, False otherwise.
    The session object will maintain the login cookies.
    """
    login_url = get_qb_url('/api/v2/auth/login')
    payload = {}
    if username and password:
        payload = {'username': username, 'password': password}

    try:
        response = session.post(login_url, data=payload)
        response.raise_for_status()

        if response.status_code == 200:
            if username and password and 'Set-Cookie' not in response.headers:
                print("Login failed: Credentials provided but no session cookie received. Please check your username and password.")
                return False
            print("Successfully logged into qBittorrent (or no authentication required).")
            return True
        else:
            print(f"Login failed with status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error during qBittorrent login: {e}")
        if isinstance(e, requests.exceptions.HTTPError) and e.response.status_code == 401:
            print("Authentication required but failed. Please ensure your qBittorrent Web UI has authentication enabled and your script credentials are correct.")
        return False

def get_torrents_info(session):
    """
    Fetches detailed information about all torrents from qBittorrent.
    Returns a list of torrent dictionaries, or None if an error occurs.
    """
    torrents_url = get_qb_url('/api/v2/torrents/info')
    try:
        response = session.get(torrents_url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching torrents information: {e}")
        return None

def set_super_seeding(session, torrent_hash, enable):
    """
    Enables or disables Super Seeding for a specific torrent.
    Args:
        session (requests.Session): The active requests session.
        torrent_hash (str): The hash of the torrent to modify.
        enable (bool): True to enable Super Seeding, False to disable.
    Returns True on success, False otherwise.
    """
    super_seeding_url = get_qb_url('/api/v2/torrents/setSuperSeeding')
    payload = {
        'hashes': torrent_hash,
        'value': 'true' if enable else 'false'
    }
    try:
        response = session.post(super_seeding_url, data=payload)
        response.raise_for_status()
        action = "Enabled" if enable else "Disabled"
        print(f"Successfully {action} Super Seeding for torrent hash: {torrent_hash[:10]}...")
        return True
    except requests.exceptions.RequestException as e:
        action = "Enabling" if enable else "Disabling"
        print(f"Error {action} Super Seeding for torrent hash {torrent_hash[:10]}...: {e}")
        return False

def set_choking_algorithm(session, algorithm_id):
    """
    Sets the global upload choking algorithm in qBittorrent.
    Args:
        session (requests.Session): The active requests session.
        algorithm_id (int): 0 for Anti-Leech, 1 for Fastest Upload.
    Returns True on success, False otherwise.
    """
    global current_choking_algorithm_state
    
    if current_choking_algorithm_state == algorithm_id:
        return True

    choking_url = get_qb_url('/api/v2/transfer/setChokingAlgorithm')
    algorithm_name = "Anti-Leech" if algorithm_id == 0 else "Fastest Upload"
    payload = {'algorithm': algorithm_id}
    try:
        response = session.post(choking_url, data=payload)
        response.raise_for_status()
        print(f"[{time.strftime('%H:%M:%S')}] Changed global choking algorithm to: {algorithm_name}.")
        current_choking_algorithm_state = algorithm_id
        return True
    except requests.exceptions.RequestException as e:
        # Added print of the full URL for debugging
        print(f"Error setting choking algorithm to {algorithm_name} for URL {choking_url}: {e}")
        return False

# --- Main Script Logic ---

def main():
    """
    Main function to run the qBittorrent Super Seeding automation.
    It continuously monitors torrents and adjusts Super Seeding mode and
    optionally the global choking algorithm.
    """
    session = requests.Session()
    logged_in = False

    while not logged_in:
        logged_in = login(session, QB_USERNAME, QB_PASSWORD)
        if not logged_in:
            print(f"Could not log in. Retrying in {POLLING_INTERVAL_SECONDS} seconds...")
            time.sleep(POLLING_INTERVAL_SECONDS)

    print("Script started. Monitoring active torrents...")
    print(" ")
    
    print(f"Super Seeding will be enabled if Total Seeds = {QB_SUPER_SEED_SEED_THRESHOLD} AND Leechers >= {QB_SUPER_SEED_LEECH_THRESHOLD}.")
    if QB_ENABLE_CHOKING_ALGORITHM_CONTROL:
        print("Automatic Choking Algorithm control is ENABLED.")
    else:
        print("Automatic Choking Algorithm control is DISABLED.")
    print(f"Checking every {POLLING_INTERVAL_SECONDS} seconds.")
    print(" ")

    while True:
        torrents = get_torrents_info(session)
        if torrents is None:
            print("Failed to retrieve torrents. Attempting to re-login...")
            logged_in = False
            while not logged_in:
                logged_in = login(session, QB_USERNAME, QB_PASSWORD)
                if not logged_in:
                    print(f"Re-login failed. Retrying in {POLLING_INTERVAL_SECONDS} seconds...")
                    time.sleep(POLLING_INTERVAL_SECONDS)
            time.sleep(POLLING_INTERVAL_SECONDS)
            continue

        any_superseeding_uploading = False
        for torrent in torrents:
            # We only care about torrents that are actively seeding or stalled in upload
            if torrent['state'] in ['uploading', 'stalledUP']:
                torrent_name = torrent['name']
                torrent_hash = torrent['hash']
                
                num_seeds_total = torrent['num_complete']
#               Wrong value ['num_incomplete']. Should be ['num_leechs']
#               num_leechers_total = torrent['num_incomplete']
                num_leechers_total = torrent['num_leechs']
                
                super_seeding_enabled = torrent['super_seeding']

                # Logic for Super Seeding mode
                if num_seeds_total <= QB_SUPER_SEED_SEED_THRESHOLD and num_leechers_total >= QB_SUPER_SEED_LEECH_THRESHOLD and not super_seeding_enabled:
                    print(f"[{time.strftime('%Y/%m/%d')}][{time.strftime('%H:%M:%S')}] (Seeders [{num_seeds_total}]~[{num_leechers_total}] Leechers) | Super Seeding ON: '{torrent_name}'")
                    set_super_seeding(session, torrent_hash, True)
                elif num_seeds_total > QB_SUPER_SEED_SEED_THRESHOLD and super_seeding_enabled:
                    print(f"[{time.strftime('%Y/%m/%d')}][{time.strftime('%H:%M:%S')}] (Seeders [{num_seeds_total}]~[{num_leechers_total}] Leechers) | Super Seeding OFF: '{torrent_name}'")
                    set_super_seeding(session, torrent_hash, False)
                elif num_leechers_total < QB_SUPER_SEED_LEECH_THRESHOLD and super_seeding_enabled:
                    print(f"[{time.strftime('%Y/%m/%d')}][{time.strftime('%H:%M:%S')}] (Seeders [{num_seeds_total}]~[{num_leechers_total}] Leechers) | Super Seeding OFF: '{torrent_name}'")
                    set_super_seeding(session, torrent_hash, False)
                
                # Check if this superseeding torrent is actively uploading for choking algorithm logic
                if super_seeding_enabled and torrent['state'] == 'uploading':
                    any_superseeding_uploading = True
        
        # Logic for global Choking Algorithm (Fastest Upload / Anti-Leech)
        if QB_ENABLE_CHOKING_ALGORITHM_CONTROL:
            if any_superseeding_uploading:
                set_choking_algorithm(session, 1) # 1 for Fastest Upload
            else:
                set_choking_algorithm(session, 0) # 0 for Anti-Leech
        
        time.sleep(POLLING_INTERVAL_SECONDS)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nScript terminated by user (Ctrl+C).")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)
