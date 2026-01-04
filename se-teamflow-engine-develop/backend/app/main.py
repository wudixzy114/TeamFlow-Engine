from fastapi import FastAPI,Response
from fastapi.middleware.cors import CORSMiddleware # 導入
from .core.database import async_engine
from .routes import auth, teams, me, highlights, dashboard, forum
from .core.dependencies import get_current_user
from .core import models
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse
from fastapi import UploadFile, HTTPException, Depends
from fastapi.responses import FileResponse
from pathlib import Path
import urllib.parse
import mimetypes

# 創建資料庫表格 (對於生產環境，推薦使用 Alembic 進行遷移)
#models.Base.metadata.create_all(bind=engine)   #還要改

app = FastAPI(
    default_response_class=ORJSONResponse,  #加速response kson效率
    title="團隊心流引擎 (TeamFlow Engine) API",
    version="1.1.0"
)

#app.add_middleware(GZipMiddleware, minimum_size=1000)

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
app.include_router(forum.router, prefix="/api/v1")

@app.get("/api/v1/health/")
def read_root():
    return {"message": "Welcome to TeamFlow Engine API"}

BASE_DIR = Path("/var/www/static/downloads").resolve()

@app.get("/api/v1/download/{filename}")
async def download_file(filename: str , user = Depends(get_current_user)):
    forbidden_chars = {"..", "/", "\\", "%", "'", "\"", "{", "}", "[", "]", "<", ">", "?", "*", "(", ")", " "}
    if any(char in forbidden_chars for char in filename):
        raise HTTPException(status_code=400, detail="Filename contains illegal characters")
    
    target_path = (BASE_DIR / filename).resolve()
    if not target_path.is_relative_to(BASE_DIR) or not target_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    # 2. 準備給 Nginx 的路徑
    encoded_filename = urllib.parse.quote(filename)
    nginx_uri = f"/protected_files/{encoded_filename}"
    
    # 3. 判斷 MIME Type (讓瀏覽器知道是什麼檔案)
    media_type, _ = mimetypes.guess_type(target_path)
    if media_type is None:
        media_type = "application/octet-stream"

    # 4. 建立回應 (重點在這裡)
    response = Response()
    
    # 告訴 Nginx 內部轉發 (前端看不到這個 Header)
    response.headers["X-Accel-Redirect"] = nginx_uri
    
    # 告訴瀏覽器：這是內容流，請用這個檔名處理
    response.headers["Content-Type"] = media_type
    
    # 關鍵： attachment 表示「下載」，filename 指定檔名
    # 如果把 attachment 改成 inline，瀏覽器會嘗試直接打開 (例如圖片或 PDF)
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'

    return response


if __name__ == "__main__":
    import uvicorn
    # 這裡的 "app.main:app" 告訴 uvicorn 去哪裡找 FastAPI 實例
    # --reload 參數會在程式碼變更時自動重啟伺服器，非常適合開發
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)