import requests
import time 

url = "http://localhost:8000"
test1_access, test1_refresh, test1_userid = None, None, None
test2_access, test2_refresh, test2_userid = None, None, None
test3_access, test3_refresh, test3_userid = None, None, None

if __name__ == "__main__":
    #test0: alive
    response = requests.get(url)
    # print(response.json())
    
    if response.json()["message"] != "Welcome to TeamFlow Engine API":
        raise Exception("API is not alive")
    
    #test1: login
    response = requests.post(url + "/api/v1/auth/login/", json={"email": "test1@gmail.com", "password": "test1"})   
    # print(response.json())
    
    if not response.json()["access"] or not response.json()["refresh"]:
        raise Exception("Login failed")
    test1_access = response.json()["access"]
    test1_refresh = response.json()["refresh"]
    
    # print(test1_access, test1_refresh)

    #test2: userinfo 獲取userid
    response = requests.get(url + "/api/v1/auth/me/", headers={"Authorization": "Bearer " + test1_access})
    #print(response.json())
    
    if response.json()["email"] != "test1@gmail.com" or response.json()["username"] != "test1" or response.json()["id"] == None:
        raise Exception("Userinfo failed")
    test1_userid = response.json()["id"]
    #print(test1_userid)
    
    #test3: 修改個人信息並驗證:
    response = requests.put(url + "/api/v1/auth/modify_selfinfo/", headers={"Authorization": "Bearer " + test1_access}, json={"nickname": "testtest", "gender": "man", "age": "18", "profession": "student"})
    #print(response.json())
    response = requests.get(url + "/api/v1/auth/me/", headers={"Authorization": "Bearer " + test1_access})
    # print(response.json())
    
    if response.json()["nickname"] != "testtest" or response.json()["gender"] != "man" or response.json()["age"] != "18" or response.json()["profession"] != "student":
        raise Exception("Modify userinfo failed")
    
    #test4: logout:
    response = requests.post(url + "/api/v1/auth/logout/", headers={"Authorization": "Bearer " + test1_access})
    #print(response.json())
    if response.json()["message"] != "Successfully logged out":
        raise Exception("Logout failed")
    response = requests.get(url + "/api/v1/auth/me/", headers={"Authorization": "Bearer " + test1_access})
    if response.json()["detail"] != "Could not validate credentials":
        raise Exception("Logout failed")
    #print(response.json()) 
    
    #test5: refresh and login:
    time.sleep(2)  #不然生成的簽名也會跟被封的token相同
    response = requests.post(url + "/api/v1/auth/token/refresh/", json={"refresh": test1_refresh})
    # print(response.json())
    if not response.json()["access"]:
        raise Exception("Refresh failed")
    test1_access = response.json()["access"]
    response = requests.get(url + "/api/v1/auth/me/", headers={"Authorization": "Bearer " + test1_access})
    #print(response.json())
    if response.json()["email"] != "test1@gmail.com" or response.json()["username"] != "test1" or response.json()["id"] == None:
        raise Exception("Refresh failed")
    
    #test6: create 1 team:
    response = requests.post(url + "/api/v1/teams/", headers={"Authorization": "Bearer " + test1_access}, json={"name": "team1"})
    # print(response.json())
    if response.json()["message"] != "Team created successfully":
       raise Exception("Create team failed")
    
    #test7: get team list:
    response = requests.get(url + "/api/v1/teams/", headers={"Authorization": "Bearer " + test1_access})
    if response.json()[0]["owner"]["username"]!= "test1":
        raise Exception("Get team list failed")
    
    team1_id = response.json()[0]["id"]
    # print(team1_id)
    
    # test8: invite: 先拒絕後傳一次再接受
    response = requests.post(url + "/api/v1/teams/" + team1_id + "/invitations/", headers={"Authorization": "Bearer " + test1_access}, json={"email_username": "test2@gmail.com"})
    # print(response.json())
    if response.json()["message"] != "The invitation has been sent successfully.":
        raise Exception("Invite failed")
    
    response = requests.post(url + "/api/v1/auth/login/", json={"email": "test2@gmail.com", "password": "test2"})
    test2_access = response.json()["access"]
    response = requests.get(url + "/api/v1/auth/me/", headers={"Authorization": "Bearer " + test2_access})
    test2_userid = response.json()["id"]
    
    response = requests.get(url + "/api/v1/me/all_invite/", headers={"Authorization": "Bearer " + test2_access})
    # print(response.json())
    invite_code = response.json()[0]["invite_code"]
    response = requests.delete(url + "/api/v1/teams/invitations/decline/", headers={"Authorization": "Bearer " + test2_access}, json={"code": invite_code})
    #print(response.json())
    if response.json()["message"] != "Team invitation declined successfully.":
        raise Exception("Decline invite failed")
    
    response = requests.post(url + "/api/v1/teams/" + team1_id + "/invitations/", headers={"Authorization": "Bearer " + test1_access}, json={"email_username": "test2@gmail.com"})
    response = requests.get(url + "/api/v1/me/all_invite/", headers={"Authorization": "Bearer " + test2_access})
    invite_code = response.json()[0]["invite_code"]
    response = requests.post(url + "/api/v1/teams/invitations/accept/", headers={"Authorization": "Bearer " + test2_access}, json={"code": invite_code})
    # print(response.json())
    response = requests.get(url + "/api/v1/teams/", headers={"Authorization": "Bearer " + test2_access})
    if response.json()[0]["owner"]["username"] != "test1":
        raise Exception("Accept invite failed")
    
    #test9: 獲取團隊成員:
    response = requests.get(url + "/api/v1/teams/" + team1_id + "/members/", headers={"Authorization": "Bearer " + test1_access})
    if response.json()["members"][1]["username"] != "test2" :
        raise Exception("Get team members failed")
    
    #test10: 修改群組信息:
    response = requests.put(url + "/api/v1/teams/" + team1_id + "/modify/", headers={"Authorization": "Bearer " + test1_access}, json={"name": "team5"})
    # print(response.json())
    if response.json()["message"] != "Team modified successfully.":
       raise Exception("Modify team failed")
    
    #test11: 更換群組管理者:
    response = requests.post(url + "/api/v1/auth/login/", json={"email": "test3@gmail.com", "password": "test3"})
    test3_access = response.json()["access"]
    response = requests.get(url + "/api/v1/auth/me/", headers={"Authorization": "Bearer " + test3_access})
    test3_userid = response.json()["id"]   #邀請user3
    response = requests.post(url + "/api/v1/teams/" + team1_id + "/invitations/", headers={"Authorization": "Bearer " + test1_access}, json={"email_username": "test3@gmail.com"})
    response = requests.get(url + "/api/v1/me/all_invite/", headers={"Authorization": "Bearer " + test3_access})
    invite_code = response.json()[0]["invite_code"]
    response = requests.post(url + "/api/v1/teams/invitations/accept/", headers={"Authorization": "Bearer " + test3_access}, json={"code": invite_code})
    response = requests.put(url + "/api/v1/teams/" + team1_id + "/modify_owner/", headers={"Authorization": "Bearer " + test1_access}, json={"id": test3_userid})
    #讓user3便成群主
    response = requests.get(url + "/api/v1/teams/" + team1_id + "/members/", headers={"Authorization": "Bearer " + test3_access})
    #print(response.json())
    
    response = requests.delete(url + "/api/v1/teams/" + team1_id + "/leave/", headers={"Authorization": "Bearer " + test1_access}) #user1退出
    response = requests.delete(url + "/api/v1/teams/" + team1_id + "/kick/", headers={"Authorization": "Bearer " + test3_access}, json = {"id": test2_userid}) #踢出user2
    response = requests.get(url + "/api/v1/teams/" + team1_id + "/members/", headers={"Authorization": "Bearer " + test3_access})
    #print(response.json())

    #test12: 解散群組:
    response = requests.delete(url + "/api/v1/teams/" + team1_id + "/delete/", headers={"Authorization": "Bearer " + test3_access})  #user3解散群組
    #print(response.json())
    
    #以上是群組跟身分的測試，接下來填充數據:
    response = requests.post(url + "/api/v1/teams/", headers={"Authorization": "Bearer " + test1_access}, json={"name": "team1"})
    response = requests.get(url + "/api/v1/teams/", headers={"Authorization": "Bearer " + test1_access})
    team1_id = response.json()[0]["id"]
    response = requests.post(url + "/api/v1/teams/" + team1_id + "/invitations/", headers={"Authorization": "Bearer " + test1_access}, json={"email_username": "test2@gmail.com"})
    response = requests.post(url + "/api/v1/teams/" + team1_id + "/invitations/", headers={"Authorization": "Bearer " + test1_access}, json={"email_username": "test3@gmail.com"})
    response = requests.get(url + "/api/v1/me/all_invite/", headers={"Authorization": "Bearer " + test2_access})
    invite_code = response.json()[0]["invite_code"]
    response = requests.post(url + "/api/v1/teams/invitations/accept/", headers={"Authorization": "Bearer " + test2_access}, json={"code": invite_code})   # user2接受邀請 user3 pending
    
    # checkin測試:
    response = requests.post(url + "/api/v1/teams/"+ team1_id +"/checkins/", headers={"Authorization": "Bearer " + test1_access}, json={"challenge_level": 0.8, "skill_level":0.8,"achievement_text": "wowowow", "obstacle_text": "thanks"})
    response = requests.get(url + "/api/v1/teams/"+ team1_id +"/checkins/today/", headers={"Authorization": "Bearer " + test1_access})
    #應該可以加個修改?
    # print(response.json())
    
    #flow session測試:
    response = requests.post(url + "/api/v1/teams/" + team1_id +"/flow-sessions/", headers={"Authorization": "Bearer " + test1_access}, json={"start_time": "2025-10-29T11:00:00", "duration_minutes": 100, "task_description" : "test"})
    #print(response.json())
    response = requests.get(url + "/api/v1/teams/" + team1_id +"/flow-sessions/", headers={"Authorization": "Bearer " + test1_access})
    #print(response.json())
    flow_id = response.json()[0]["id"]
    response = requests.put(url + "/api/v1/teams/" + team1_id +"/flow-sessions/modify/", headers={"Authorization": "Bearer " + test1_access}, json={"id" : flow_id, "description": "hahaha"})
    #print(response.json())
    response = requests.delete(url + "/api/v1/teams/" + team1_id +"/flow-sessions/delete/", headers={"Authorization": "Bearer " + test1_access}, json={"id" : flow_id})
    response = requests.get(url + "/api/v1/teams/" + team1_id +"/flow-sessions/", headers={"Authorization": "Bearer " + test1_access})
    #print(response.json())
    response = requests.post(url + "/api/v1/teams/" + team1_id +"/flow-sessions/", headers={"Authorization": "Bearer " + test1_access}, json={"start_time": "2025-10-29T11:00:00", "duration_minutes": 50, "task_description" : "test111"})
    response = requests.get(url + "/api/v1/teams/" + team1_id +"/flow-sessions/", headers={"Authorization": "Bearer " + test1_access})
    #print(response.json())
    
    
    #charter:
    response = requests.put(url + "/api/v1/teams/" + team1_id +"/charter/", headers={"Authorization": "Bearer " + test1_access}, json={"content": "charter_test"})
    # print(response.json())
    
    #highlight:
    response = requests.post(url + "/api/v1/teams/" + team1_id +"/highlights/", headers={"Authorization": "Bearer " + test1_access}, json={"content": "highlight_test"})
    print(response.json())
    response = requests.get(url + "/api/v1/teams/" + team1_id +"/highlights/", headers={"Authorization": "Bearer " + test1_access})
    print(response.json())
    highlight_id = response.json()[0]["id"]
    response = requests.post( url + "/api/v1/highlights/" + highlight_id +"/like/", headers={"Authorization": "Bearer " + test2_access})
    print(response.json())
    response = requests.get(url + "/api/v1/teams/" + team1_id +"/highlights/", headers={"Authorization": "Bearer " + test1_access})
    print(response.json())
    response = requests.post( url + "/api/v1/highlights/" + highlight_id +"/dislike/", headers={"Authorization": "Bearer " + test2_access})
    print(response.json())
    response = requests.get(url + "/api/v1/teams/" + team1_id +"/highlights/", headers={"Authorization": "Bearer " + test1_access})
    print(response.json())
    response = requests.post( url + "/api/v1/highlights/" + highlight_id +"/like/", headers={"Authorization": "Bearer " + test2_access})
    print(response.json())
    

    
    
    

