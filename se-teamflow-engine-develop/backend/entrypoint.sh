#!/bin/sh

# 應用資料庫遷移
# 這會將資料庫更新到最新的 schema
echo "Applying database migrations..."
alembic upgrade head

# 執行傳遞給此腳本的命令 (即 Dockerfile 中的 CMD)
echo "Seeding initial data..."
python init_db.py

exec "$@"