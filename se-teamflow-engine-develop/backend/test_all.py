import requests
import time

# --- Global Variables ---
url = "http://localhost:8000"
test1_access, test1_refresh, test1_userid = None, None, None
test2_access, test2_refresh, test2_userid = None, None, None
test3_access, test3_refresh, test3_userid = None, None, None

# --- Main Execution Block ---
if __name__ == "__main__":
    # Test 0: Check if the API is alive
    
    response = requests.get(url+"/api/v1/health/")
    # print(response.json())
    assert response.json()["message"] == "Welcome to TeamFlow Engine API", "API is not alive"

    # Test 1: Login for test1
    
    response = requests.post(url + "/api/v1/auth/login/", json={"email": "test1@gmail.com", "password": "test1"})
    # print(response.json())
    assert "access" in response.json() and "refresh" in response.json(), "Login failed"
    test1_access = response.json()["access"]
    test1_refresh = response.json()["refresh"]
    # print(test1_access, test1_refresh)

    # Test 2: Get user info for test1 to get userid
    response = requests.get(url + "/api/v1/auth/me/", headers={"Authorization": "Bearer " + test1_access})
    # print(response.json())
    assert response.json()["email"] == "test1@gmail.com", "Userinfo failed: email mismatch"
    assert response.json()["username"] == "test1", "Userinfo failed: username mismatch"
    assert response.json()["id"] is not None, "Userinfo failed: id is None"
    test1_userid = response.json()["id"]
    # print(test1_userid)

    # Test 3: Modify personal info and verify
    response = requests.put(
        url + "/api/v1/auth/modify_selfinfo/",
        headers={"Authorization": "Bearer " + test1_access},
        json={"nickname": "testtest", "gender": "man", "age": "18", "profession": "student"}
    )
    # print(response.json())
    response = requests.get(url + "/api/v1/auth/me/", headers={"Authorization": "Bearer " + test1_access})
    # print(response.json())
    assert response.json()["nickname"] == "testtest", "Modify userinfo failed: nickname mismatch"
    assert response.json()["gender"] == "man", "Modify userinfo failed: gender mismatch"
    assert response.json()["age"] == "18", "Modify userinfo failed: age mismatch"
    assert response.json()["profession"] == "student", "Modify userinfo failed: profession mismatch"

    # Test 4: Logout
    response = requests.post(url + "/api/v1/auth/logout/", json={"refresh": test1_refresh, "access": test1_access})
    print(response.json())
    assert response.json()["message"] == "Successfully logged out", "Logout failed: incorrect message"
    response = requests.get(url + "/api/v1/auth/me/", headers={"Authorization": "Bearer " + test1_access})
    assert response.json()["detail"] == "Could not validate credentials", "Logout failed: token still valid"
    # print(response.json())

    
    response = requests.post(url + "/api/v1/auth/login/", json={"email": "test1@gmail.com", "password": "test1"})
    test1_access = response.json()["access"]
    test1_refresh = response.json()["refresh"]
    # Test 5: Refresh token and login again
    #time.sleep(2)  # Wait to ensure the new token signature is different
    response = requests.post(url + "/api/v1/auth/token/refresh/", json={"refresh": test1_refresh})
    # print(response.json())
    assert "access" in response.json(), "Refresh failed"
    test1_access = response.json()["access"]
    response = requests.get(url + "/api/v1/auth/me/", headers={"Authorization": "Bearer " + test1_access})
    # print(response.json())
    assert response.json()["email"] == "test1@gmail.com", "Refresh failed: email mismatch"
    assert response.json()["username"] == "test1", "Refresh failed: username mismatch"
    assert response.json()["id"] is not None, "Refresh failed: id is None"

    # Test 6: Create 1 team
    response = requests.post(url + "/api/v1/teams/", headers={"Authorization": "Bearer " + test1_access}, json={"name": "team1"})
    # print(response.json())
    assert response.json()["message"] == "Team created successfully", "Create team failed"

    # Test 7: Get team list
    response = requests.get(url + "/api/v1/teams/", headers={"Authorization": "Bearer " + test1_access})
    assert response.json()[0]["owner"]["username"] == "test1", "Get team list failed"
    team1_id = response.json()[0]["id"]
    # print(team1_id)

    # Test 8: Invite process (decline first, then accept)
    response = requests.post(
        url + f"/api/v1/teams/{team1_id}/invitations/",
        headers={"Authorization": "Bearer " + test1_access},
        json={"email_username": "test2@gmail.com"}
    )
    # print(response.json())
    assert response.json()["message"] == "The invitation has been sent successfully.", "Invite failed"

    response = requests.post(url + "/api/v1/auth/login/", json={"email": "test2@gmail.com", "password": "test2"})
    test2_access = response.json()["access"]
    response = requests.get(url + "/api/v1/auth/me/", headers={"Authorization": "Bearer " + test2_access})
    print(response.json())
    test2_userid = response.json()["id"]

    response = requests.get(url + "/api/v1/me/all_invite/", headers={"Authorization": "Bearer " + test2_access})
    # print(response.json())
    invite_code = response.json()[0]["invite_code"]
    response = requests.delete(url + "/api/v1/teams/invitations/decline/", headers={"Authorization": "Bearer " + test2_access}, json={"code": invite_code})
    # print(response.json())
    assert response.json()["message"] == "Team invitation declined successfully.", "Decline invite failed"

    # Send invitation again
    response = requests.post(
        url + f"/api/v1/teams/{team1_id}/invitations/",
        headers={"Authorization": "Bearer " + test1_access},
        json={"email_username": "test2@gmail.com"}
    )
    response = requests.get(url + "/api/v1/me/all_invite/", headers={"Authorization": "Bearer " + test2_access})
    invite_code = response.json()[0]["invite_code"]
    response = requests.post(url + "/api/v1/teams/invitations/accept/", headers={"Authorization": "Bearer " + test2_access}, json={"code": invite_code})
    # print(response.json())
    response = requests.get(url + "/api/v1/teams/", headers={"Authorization": "Bearer " + test2_access})
    assert response.json()[0]["owner"]["username"] == "test1", "Accept invite failed"

    # Test 9: Get team members
    response = requests.get(url + f"/api/v1/teams/{team1_id}/members/", headers={"Authorization": "Bearer " + test1_access})
    assert any(member['username'] == 'test2' for member in response.json()["members"]), "Get team members failed"

    # Test 10: Modify team info
    response = requests.put(
        url + f"/api/v1/teams/{team1_id}/modify/",
        headers={"Authorization": "Bearer " + test1_access},
        json={"name": "team5"}
    )
    # print(response.json())
    assert response.json()["message"] == "Team modified successfully.", "Modify team failed"

    # Test 11: Change team owner
    response = requests.post(url + "/api/v1/auth/login/", json={"email": "test3@gmail.com", "password": "test3"})
    test3_access = response.json()["access"]
    response = requests.get(url + "/api/v1/auth/me/", headers={"Authorization": "Bearer " + test3_access})
    test3_userid = response.json()["id"]  # Invite user3
    response = requests.post(
        url + f"/api/v1/teams/{team1_id}/invitations/",
        headers={"Authorization": "Bearer " + test1_access},
        json={"email_username": "test3@gmail.com"}
    )
    response = requests.get(url + "/api/v1/me/all_invite/", headers={"Authorization": "Bearer " + test3_access})
    invite_code = response.json()[0]["invite_code"]
    response = requests.post(url + "/api/v1/teams/invitations/accept/", headers={"Authorization": "Bearer " + test3_access}, json={"code": invite_code})

    # Make user3 the new owner
    response = requests.put(
        url + f"/api/v1/teams/{team1_id}/modify_owner/",
        headers={"Authorization": "Bearer " + test1_access},
        json={"id": test3_userid}
    )
    response = requests.get(url + f"/api/v1/teams/{team1_id}/members/", headers={"Authorization": "Bearer " + test3_access})
    # print(response.json())

    response = requests.delete(url + f"/api/v1/teams/{team1_id}/leave/", headers={"Authorization": "Bearer " + test1_access})  # user1 leaves
    response = requests.delete(url + f"/api/v1/teams/{team1_id}/kick/", headers={"Authorization": "Bearer " + test3_access}, json={"id": test2_userid})  # user3 kicks user2
    response = requests.get(url + f"/api/v1/teams/{team1_id}/members/", headers={"Authorization": "Bearer " + test3_access})
    # print(response.json())

    # Test 12: Disband the team
    response = requests.delete(url + f"/api/v1/teams/{team1_id}/delete/", headers={"Authorization": "Bearer " + test3_access})  # user3 disbands the team
    # print(response.json())

    # --- Setup data for further tests ---
    response = requests.post(url + "/api/v1/teams/", headers={"Authorization": "Bearer " + test1_access}, json={"name": "team1"})
    response = requests.get(url + "/api/v1/teams/", headers={"Authorization": "Bearer " + test1_access})
    team1_id = response.json()[0]["id"]
    response = requests.post(
        url + f"/api/v1/teams/{team1_id}/invitations/",
        headers={"Authorization": "Bearer " + test1_access},
        json={"email_username": "test2@gmail.com"}
    )
    response = requests.post(
        url + f"/api/v1/teams/{team1_id}/invitations/",
        headers={"Authorization": "Bearer " + test1_access},
        json={"email_username": "test3@gmail.com"}
    )
    response = requests.get(url + "/api/v1/me/all_invite/", headers={"Authorization": "Bearer " + test2_access})
    invite_code = response.json()[0]["invite_code"]
    response = requests.post(url + "/api/v1/teams/invitations/accept/", headers={"Authorization": "Bearer " + test2_access}, json={"code": invite_code})  # user2 accepts, user3 is pending

    # --- Check-in tests ---
    response = requests.post(
        url + f"/api/v1/teams/{team1_id}/checkins/",
        headers={"Authorization": "Bearer " + test1_access},
        json={"challenge_level": 0.8, "skill_level": 0.8, "achievement_text": "wowowow", "obstacle_text": "thanks"}
    )
    response = requests.get(url + f"/api/v1/teams/{team1_id}/checkins/today/", headers={"Authorization": "Bearer " + test1_access})
    # A modification test could be added here
    # print(response.json())

    # --- Flow Session tests ---
    response = requests.post(
        url + f"/api/v1/teams/{team1_id}/flow-sessions/",
        headers={"Authorization": "Bearer " + test1_access},
        json={"start_time": "2025-10-29T11:00:00", "duration_minutes": 100, "task_description": "test"}
    )
    # print(response.json())
    response = requests.get(url + f"/api/v1/teams/{team1_id}/flow-sessions/", headers={"Authorization": "Bearer " + test1_access})
    # print(response.json())
    flow_id = response.json()[0]["id"]
    response = requests.put(
        url + f"/api/v1/teams/{team1_id}/flow-sessions/modify/",
        headers={"Authorization": "Bearer " + test1_access},
        json={"id": flow_id, "task_description": "hahaha"}
    )
    #print(response.json())
    
    response = requests.delete(
        url + f"/api/v1/teams/{team1_id}/flow-sessions/delete/",
        headers={"Authorization": "Bearer " + test1_access},
        json={"id": flow_id}
    )
    response = requests.get(url + f"/api/v1/teams/{team1_id}/flow-sessions/", headers={"Authorization": "Bearer " + test1_access})
    # print(response.json())
    response = requests.post(
        url + f"/api/v1/teams/{team1_id}/flow-sessions/",
        headers={"Authorization": "Bearer " + test1_access},
        json={"start_time": "2025-10-29T11:00:00", "duration_minutes": 50, "task_description": "test111"}
    )
    response = requests.get(url + f"/api/v1/teams/{team1_id}/flow-sessions/", headers={"Authorization": "Bearer " + test1_access})
    # print(response.json())

    # --- Charter tests ---
    response = requests.put(
        url + f"/api/v1/teams/{team1_id}/charter/",
        headers={"Authorization": "Bearer " + test1_access},
        json={"content": "charter_test"}
    )
    response = requests.get(url + f"/api/v1/teams/{team1_id}/charter/", headers={"Authorization": "Bearer " + test1_access})
    # print(response.json())

    # --- Highlight tests ---
    response = requests.post(
        url + f"/api/v1/teams/{team1_id}/highlights/",
        headers={"Authorization": "Bearer " + test1_access},
        json={"content": "highlight_test"}
    )
    #print(response.json())
    response = requests.get(url + f"/api/v1/teams/{team1_id}/highlights/", headers={"Authorization": "Bearer " + test1_access})
    print(response.json())
    highlight_id = response.json()[0]["id"]

    # Like
    response = requests.put(url + f"/api/v1/highlights/{highlight_id}/like/", headers={"Authorization": "Bearer " + test2_access})
    # print(response.json())
    response = requests.get(url + f"/api/v1/teams/{team1_id}/highlights/", headers={"Authorization": "Bearer " + test1_access})
    print(response.json())

    # Dislike (undo like)
    response = requests.delete(url + f"/api/v1/highlights/{highlight_id}/dislike/", headers={"Authorization": "Bearer " + test2_access})
    # print(response.json())
    response = requests.get(url + f"/api/v1/teams/{team1_id}/highlights/", headers={"Authorization": "Bearer " + test1_access})
    print(response.json())

    # Like again
    response = requests.put(url + f"/api/v1/highlights/{highlight_id}/like/", headers={"Authorization": "Bearer " + test2_access})
    # print(response.json())
    
    response = requests.get(url + f"/api/v1/me/message/", headers={"Authorization": "Bearer " + test3_access})
    print(response.json())
    
    id = response.json()[0]["id"]
    response = requests.delete(url + f"/api/v1/me/message/delete/", headers={"Authorization": "Bearer " + test3_access}, json={"message_id": id})
    
    response = requests.get(url + f"/api/v1/me/message/", headers={"Authorization": "Bearer " + test3_access})
    print(response.json())
    
    response = requests.get(url + f"/api/v1/me/{team1_id}/message/", headers={"Authorization": "Bearer " + test1_access})
    print(response.json()),
    
    message_id= response.json()[0]["id"]
    response = requests.delete(url + f"/api/v1/me/{team1_id}/message/delete/", headers={"Authorization": "Bearer " + test1_access}, json={"message_id": message_id})
    print(response.json())
    response = requests.get(url + f"/api/v1/me/{team1_id}/message/", headers={"Authorization": "Bearer " + test1_access})
    print(response.json())
    

    # --- Team tests ---
    