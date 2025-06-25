import requests
import time
import sys
import os # Import the os module to access environment variables

# --- Configuration ---
# Read configuration from environment variables.
# Provide default values if environment variables are not set.
# These defaults can be overridden by the .env file or -e flags in docker run.
# QB_HOST = os.getenv('QB_HOST', 'host.docker.internal') # Default for Docker Desktop
QB_HOST = os.getenv('QB_HOST', 'localhost') # Default for Docker Desktop
QB_PORT = os.getenv('QB_PORT', '8080')
QB_USERNAME = os.getenv('QB_USERNAME', 'admin') # Default username (PLEASE CHANGE)
QB_PASSWORD = os.getenv('QB_PASSWORD', 'adminadmin') # Default password (PLEASE CHANGE)
POLLING_INTERVAL_SECONDS = int(os.getenv('POLLING_INTERVAL_SECONDS', 120)) # Convert to int

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
    if username and password: # Only add credentials to payload if they are provided
        payload = {'username': username, 'password': password}

    try:
        # Send a POST request to the login endpoint. Payload is empty if no credentials.
        response = session.post(login_url, data=payload)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)

        # Check for successful login. If credentials were required and provided, a cookie is expected.
        # If no credentials were provided and no authentication is needed, a 200 OK without Set-Cookie is fine.
        if response.status_code == 200:
            if username and password and 'Set-Cookie' not in response.headers:
                print("Login failed: Credentials provided but no session cookie received. Please check your username and password.")
                return False
            print("Successfully logged into qBittorrent (or no authentication required).")
            return True
        else:
            # This case should ideally be caught by raise_for_status(), but good for clarity
            print(f"Login failed with status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error during qBittorrent login: {e}")
        # Specific check for 401 Unauthorized, which means credentials *are* required
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
        # Send a GET request to retrieve torrent information
        response = session.get(torrents_url)
        response.raise_for_status()
        return response.json() # Parse the JSON response
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
        'value': 'true' if enable else 'false' # API expects string 'true' or 'false'
    }
    try:
        # Send a POST request to set Super Seeding status
        response = session.post(super_seeding_url, data=payload)
        response.raise_for_status()
        action = "Enabled" if enable else "Disabled"
        print(f"Successfully {action} Super Seeding for torrent hash: {torrent_hash[:10]}...") # Print first 10 chars of hash
        return True
    except requests.exceptions.RequestException as e:
        action = "Enabling" if enable else "Disabling"
        print(f"Error {action} Super Seeding for torrent hash {torrent_hash[:10]}...: {e}")
        return False

# --- Main Script Logic ---

def main():
    """
    Main function to run the qBittorrent Super Seeding automation.
    It continuously monitors torrents and adjusts Super Seeding mode.
    """
    session = requests.Session() # Create a session to persist cookies for login
    logged_in = False

    # Initial login attempt, with retries if it fails
    while not logged_in:
        logged_in = login(session, QB_USERNAME, QB_PASSWORD)
        if not logged_in:
            print(f"Could not log in. Retrying in {POLLING_INTERVAL_SECONDS} seconds...")
            time.sleep(POLLING_INTERVAL_SECONDS)

    print("Script started. Monitoring active torrents...")
    print(f"Checking every {POLLING_INTERVAL_SECONDS} seconds.")

    # Main monitoring loop
    while True:
        torrents = get_torrents_info(session)
        if torrents is None:
            # If fetching torrents fails, it might be due to a lost session/login
            print("Failed to retrieve torrents. Attempting to re-login...")
            logged_in = False
            while not logged_in:
                logged_in = login(session, QB_USERNAME, QB_PASSWORD)
                if not logged_in:
                    print(f"Re-login failed. Retrying in {POLLING_INTERVAL_SECONDS} seconds...")
                    time.sleep(POLLING_INTERVAL_SECONDS)
            time.sleep(POLLING_INTERVAL_SECONDS) # Wait before trying to get torrents again
            continue # Skip to the next iteration of the main loop

        # Process each torrent
        for torrent in torrents:
            # We only care about torrents that are actively seeding or stalled in upload
            # 'uploading': Torrent is actively uploading data
            # 'stalledUP': Torrent is stalled due to no peers wanting data, but is still considered seeding
            if torrent['state'] in ['uploading', 'stalledUP']:
                torrent_name = torrent['name']
                torrent_hash = torrent['hash']
                
                # --- IMPORTANT CHANGE HERE ---
                # Using 'num_complete' which represents the total number of seeds (peers with 100% of the file).
                # This aligns with the "only I am seeding" logic, as opposed to 'num_seeds' which is
                # only the number of seeds currently connected to YOUR client.
                num_seeds_total = torrent['num_complete']
                # --- END IMPORTANT CHANGE ---

                super_seeding_enabled = torrent['super_seeding'] # Current Super Seeding status (boolean)

                # Rule 1: If the total number of seeds is 1 (meaning only you are seeding)
                # and Super Seeding is NOT currently enabled, then enable it.
                if num_seeds_total == 1 and not super_seeding_enabled:
                    print(f"[{time.strftime('%H:%M:%S')}] Enabling Super Seeding. Torrent '{torrent_name}' has only 1 seed")
                    set_super_seeding(session, torrent_hash, True)
                # Rule 2: If the total number of seeds is 2 or more,
                # and Super Seeding IS currently enabled, then disable it.
                elif num_seeds_total >= 2 and super_seeding_enabled:
                    print(f"[{time.strftime('%H:%M:%S')}] Disabling Super Seeding. Torrent '{torrent_name}' has {num_seeds_total} total seeds")
                    set_super_seeding(session, torrent_hash, False)
                # The 'else' block for "No action needed" has been removed to reduce log verbosity.
        
        # Wait for the next polling interval
        time.sleep(POLLING_INTERVAL_SECONDS)

# This ensures that main() is called only when the script is executed directly
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nScript terminated by user (Ctrl+C).")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1) # Exit with an error code
