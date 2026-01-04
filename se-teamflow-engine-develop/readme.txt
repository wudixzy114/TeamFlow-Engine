(teamflow-env) walla@DESKTOP-N3FCRDF:/mnt/d/desktop/軟工大作業/backend$

(記得再虛擬環境裡面並且開啟docker-compose，然後在 /backend 目錄下啟動:



chmod +x ./entrypoint.sh

sudo docker compose up --build    (啟動)

sudo docker compose down -v   (訂正代碼前需要先compose down)   會把數據庫清空

sudo docker compose exec db psql -U teamflow_user -d teamflow_db    (查看數據庫，請用ai查詢想要的搜索語法)


sudo docker exec -it backend-db-1 psql -U teamflow_user -d teamflow_db      也可以用這個

sudo docker compose logs -f


修改數據庫:
在backen目錄下，開啟docker:
docker compose exec backend alembic upgrade head

docker compose exec backend alembic revision --autogenerate -m "update teamchat"





curl -X POST "http://localhost/api/v1/auth/token/refresh/" \
     -H "Content-Type: application/json" \
     -d '{
           "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZTBlYjZlNi1lOTM5LTRhMGYtODAxNy0wYTUyZTI0NDRjMWUiLCJleHAiOjE3NjEyODk3OTMsInR5cGUiOiJyZWZyZXNoIn0.cUYYV-Ws8W_iysED2jZHmw2l2KThEbOjW3d2B7_zvhg"
         }' | jq


curl -X GET "http://localhost/api/v1/auth/me" -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzMDVhMTU5Yi1hODRhLTRhZDktYjI5Ny0yY2ZhYTkxMTIwYTgiLCJleHAiOjE3NjAxNzA2Nzl9.KxkWHXrcViZ3HWdiCxui2k44wlGzDm4Yr2MDdihOJBc" | jq


curl -X POST "http://localhost/api/v1/auth/register"      -H "Content-Type: application/json"      -d '{
           "email": "ww.doe@example.com",
           "password": "Password123",
           "username": "sssssss"
         }' | jq


curl -X POST "http://82.157.172.36:8000/api/v1/auth/login/" \
     -H "Content-Type: application/json" \
     -d '{"email": "test1@gmail.com", "password": "test1"}' | jq


     http://82.157.172.36:8000/api/v1/download/tokens.txt   訪問這個路徑


     curl -X GET "http://localhost/api/v1/auth/me" -H "Authorization: Bearer  ...




