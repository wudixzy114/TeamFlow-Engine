import requests
import time
import os

# --- Configuration ---
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"
UNIQUE_ID = int(time.time())

# --- Test User Definitions ---
OWNER_EMAIL = f"1677517496@qq.com"
OWNER_USERNAME = f"owner_{UNIQUE_ID}"
OWNER_PASSWORD = "OwnerPassword123"
NEW_EMAIL_FOR_OWNER = f"a1631632222@163.com"

# --- Helper Functions ---

def _make_request(method, endpoint, expected_status, **kwargs):
    """Generic request helper to reduce boilerplate."""
    url = f"{BASE_URL}{API_PREFIX}{endpoint}"
    try:
        res = requests.request(method, url, **kwargs)
        if res.status_code != expected_status:
            print(f"  [FAIL] Expected status {expected_status}, but got {res.status_code}.")
            print(f"  Response: {res.text}")
            res.raise_for_status()
        
        print(f"  [SUCCESS] Request to {endpoint} returned {res.status_code}.")
        return res.json()
    except requests.exceptions.RequestException as e:
        print(f"  [FAIL] Network error during request to {endpoint}: {e}")
        raise

def register_and_login(email, username, password):
    """Registers a user and logs them in to get an auth token."""
    print(f"\n[SETUP] Registering and logging in user: {username}")
    # Register
    try:
        requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/register",
            json={"email": email, "password": password, "username": username}
        )
        print(f"  [INFO] Registration request sent for {username}.")
    except requests.exceptions.RequestException as e:
        print(f"  [WARN] Registration for {username} might have failed or user exists: {e}")

    # Verify email (assuming auto-verification or manual for testing)
    # In a real test, you'd get the code from Redis or email. Here we skip it.
    # For this test, we assume the user is active.

    # Login
    login_data = _make_request(
        "POST", "/auth/login/", 200,
        json={"email": email, "password": password}
    )
    token = login_data.get("access")
    if not token:
        raise ValueError("Failed to get access token after login.")
    print(f"  [SUCCESS] Logged in as {username}.")
    return f"Bearer {token}"

def create_team(auth_token, team_name):
    """Creates a team and returns its ID."""
    print(f"\n[SETUP] Creating team: {team_name}")
    team_data = _make_request(
        "POST", "/", 201,
        headers={"Authorization": auth_token},
        json={"name": team_name, "description": "Test team"}
    )
    # The create_team endpoint in teams.py seems to return a message, not the team object.
    # We will list teams to get the ID.
    teams_list = _make_request("GET", "/", 200, headers={"Authorization": auth_token})
    new_team = next((t for t in teams_list if t['name'] == team_name), None)
    if not new_team:
        raise ValueError("Failed to find created team.")
    team_id = new_team.get("id")
    print(f"  [SUCCESS] Created team '{team_name}' with ID: {team_id}")
    return team_id

def create_highlight(auth_token, team_id, content):
    """Creates a highlight and returns its ID."""
    print("\n[SETUP] Creating a highlight.")
    _make_request(
        "POST", f"/teams/{team_id}/highlights/", 201,
        headers={"Authorization": auth_token},
        json={"content": content}
    )
    # Get the highlight ID by listing them
    highlights = _make_request("GET", f"/teams/{team_id}/highlights/", 200, headers={"Authorization": auth_token})
    new_highlight = next((h for h in highlights if h['content'] == content), None)
    if not new_highlight:
        raise ValueError("Failed to find created highlight.")
    highlight_id = new_highlight.get("id")
    print(f"  [SUCCESS] Created highlight with ID: {highlight_id}")
    return highlight_id

def create_charter(auth_token, team_id):
    """Creates a team charter to be deleted."""
    print("\n[SETUP] Creating a team charter.")
    _make_request(
        "PUT", f"/teams/{team_id}/charter/", 200,
        headers={"Authorization": auth_token},
        json={"content": "This is a test charter to be deleted."}
    )
    print("  [SUCCESS] Team charter created/updated.")

# --- Main Test Execution ---

def run_all_tests():
    """Runs the sequence of tests."""
    print("--- Starting User and Team Feature Tests ---")

    # --- 1. Initial Setup: Create User and Team ---
    owner_token = register_and_login(OWNER_EMAIL, OWNER_USERNAME, OWNER_PASSWORD)
    team_id = create_team(owner_token, f"Team_{UNIQUE_ID}")

    # --- 2. Test Highlight Modification and Deletion ---
    print("\n[TEST 1] Modify and Delete Highlight")
    highlight_content = f"Original highlight content {UNIQUE_ID}"
    highlight_id = create_highlight(owner_token, team_id, highlight_content)
    
    print("  - Modifying highlight...")
    _make_request(
        "PUT", f"/teams/{team_id}/highlights/modify/", 200,
        headers={"Authorization": owner_token},
        json={"id": highlight_id, "content": "Updated highlight content"}
    )
    
    print("  - Deleting highlight...")
    _make_request(
        "DELETE", f"/teams/{team_id}/highlights/delete/", 200,
        headers={"Authorization": owner_token},
        json={"id": highlight_id}
    )

    # --- 3. Test Team Charter Deletion ---
    print("\n[TEST 2] Delete Team Charter")
    create_charter(owner_token, team_id) # Ensure a charter exists
    print("  - Deleting team charter...")
    _make_request(
        "DELETE", f"/teams/{team_id}/delete-charter/", 200,
        headers={"Authorization": owner_token}
    )

    # --- 4. Test Email Modification (Manual Step Required) ---
    print("\n[TEST 3] Modify Email Address (Manual Intervention Needed)")
    print(f"  - Requesting email change from '{OWNER_EMAIL}' to '{NEW_EMAIL_FOR_OWNER}'...")
    _make_request(
        "PUT", "/auth/reset-email/", 200,
        headers={"Authorization": owner_token},
        json={"new_email": NEW_EMAIL_FOR_OWNER}
    )
    
    print("\n--- Manual Step Required ---")
    print(f"1. A verification code has been sent to '{NEW_EMAIL_FOR_OWNER}'.")
    print("2. Please retrieve the 6-digit code.")
    code = input("3. Enter the verification code here and press Enter: ")

    if code and len(code) == 6:
        print("  - Verifying new email address with the provided code...")
        _make_request(
            "PUT", "/auth/verify-email-reset/", 200,
            headers={"Authorization": owner_token},
            json={"code": code.strip()}
        )
    else:
        print("  [SKIP] Invalid or no code entered. Skipping email verification step.")

    print("\n--- All Tests Completed ---")


if __name__ == "__main__":
    try:
        run_all_tests()
    except Exception as e:
        print(f"\nAn error occurred, terminating tests: {e}")

