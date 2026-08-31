from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # 導入
from .routes import auth, teams, me, highlights, dashboard
from .core.database import engine
from .core import models

# 創建資料庫表格 (對於生產環境，推薦使用 Alembic 進行遷移)
#models.Base.metadata.create_all(bind=engine)   #還要改

app = FastAPI(
    title="團隊心流引擎 (TeamFlow Engine) API",
    version="1.1.0"
)

# --- 新增 CORS 設定 ---
# 這裡的設定比較寬鬆，生產環境中建議將 origins 設為你前端的具體域名
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # 或者 ["http://localhost:3000", "https://your-frontend.com"]
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# 掛載 API 路由
app.include_router(auth.router, prefix="/api/v1")   #訪問時需要加上api/v1前綴
app.include_router(teams.router, prefix="/api/v1")
app.include_router(me.router, prefix="/api/v1")
app.include_router(highlights.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to TeamFlow Engine API"}


if __name__ == "__main__":
    import uvicorn
    # 這裡的 "app.main:app" 告訴 uvicorn 去哪裡找 FastAPI 實例
    # --reload 參數會在程式碼變更時自動重啟伺服器，非常適合開發
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)