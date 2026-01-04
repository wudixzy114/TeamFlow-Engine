# --- 檔案: alembic/env.py ---
# 功能: 為 Alembic 提供資料庫連接和模型元數據 (Metadata)

import sys
from pathlib import Path
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# --- 關鍵修改 1: 讓 Alembic 能夠找到你的 'app' 模組 ---
# 將專案根目錄 (alembic 文件夾的上一層) 加入到 Python 的搜索路徑中
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# 從你的應用程式中導入核心組件
from app.core.config import settings  # 導入你的 Pydantic 設定
from app.core.database import Base      # 導入你的 SQLAlchemy Base
from app.core import models             # 確保所有模型都被加載

# 這是 Alembic 的設定對象，它能讓我們讀取 .ini 檔案中的值
config = context.config

# --- 關鍵修改 2: 將資料庫 URL 指向你的應用設定 ---
# 不再使用 alembic.ini 中的 sqlalchemy.url，而是直接使用 Pydantic settings
# 這樣可以確保 Alembic 和你的 FastAPI 應用使用完全相同的資料庫配置
config.set_main_option('sqlalchemy.url', settings.SYNC_DATABASE_URL)

# 從 config 檔案中解釋日誌設定
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- 關鍵修改 3: 設定模型的元數據 ---
# 將 target_metadata 指向你所有 SQLAlchemy 模型的元數據集合 (Base.metadata)
# Alembic 會比對這個 target_metadata 和資料庫的當前狀態，來自動生成遷移腳本
target_metadata = Base.metadata

# 其他來自 .ini 檔案的選項可以像這樣被讀取:
# my_important_option = config.get_main_option("my_important_option")
# ... 等等。


def run_migrations_offline() -> None:
    """在 'offline' 模式下運行遷移。

    這個腳本只配置一個 URL，
    而不創建 Engine。雖然推薦使用 'online' 模式，
    但我們保留了這個函數以保持完整性。
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """在 'online' 模式下運行遷移。

    在這個設定中，我們會創建一個 Engine
    並將其與一個 Connection 關聯起來，然後在這個事務中
    執行遷移。
    """
    # connectable = engine_from_config(
    #     config.get_section(config.config_main_section, {}),
    #     prefix="sqlalchemy.",
    #     poolclass=pool.NullPool,
    # )
    
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}), # 將 config_main_section 改為 config_ini_section
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()