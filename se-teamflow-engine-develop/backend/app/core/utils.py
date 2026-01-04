from datetime import datetime, timedelta, date, timezone
from typing import List, Dict, Any, Set, Optional
from collections import Counter
from pathlib import Path
import os
import uuid
import aiofiles
import jieba
import logging
import secrets  
import string   
from fastapi.concurrency import run_in_threadpool
from fastapi import UploadFile, HTTPException

logger = logging.getLogger(__name__)
MAX_FILE_SIZE = 10 * 1024 * 1024
BASE_UPLOAD_DIR = Path("static/uploads")

PeriodLiteral = ("day", "week", "month")

# Config: 簡單的時區設定 (預設 UTC+8)，解決趨勢圖日期偏差問題
DEFAULT_TIMEZONE_OFFSET = 8

def generate_invite_code(length: int = 64) -> str:
    """生成一個隨機的邀請碼"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))

def get_start_date(period: str) -> datetime:
    """根据周期计算查询的起始日期（纯 Python，无 DB 依赖）。"""
    now = datetime.utcnow()
    if period == "day":
        return now - timedelta(days=1)
    if period == "week":
        return now - timedelta(weeks=1)
    if period == "month":
        return now - timedelta(days=30)
    return now - timedelta(weeks=1)

def classify_emotion(checkin) -> str:
    """
    将单条 checkin 数据分类为 positive/neutral/negative。
    【優化】：增加了 `or 0` 處理，防止 DB 數值為 None 時 float() 報錯。
    """
    try:
        # getattr 取出可能是 None，使用 or 0 轉為浮點數 0.0
        c = float(getattr(checkin, "challenge_level", 0) or 0)
        s = float(getattr(checkin, "skill_level", 0) or 0)
    except Exception:
        return "neutral"
        
    if c > 3.5 and s > 3.5:
        return "positive"
    if (c > 3.5 and s < 2.5) or (c < 2.5 and s < 2.5):
        return "negative"
    return "neutral"

def aggregate_trend_by_date(checkins: List[Any], timezone_offset: int = DEFAULT_TIMEZONE_OFFSET) -> List[Dict[str, Any]]:
    """
    从 checkin 列表生成按日趋势数据。
    【優化】：加入時區偏移，將 UTC 時間轉換為當地時間 (如 UTC+8) 後再取日期。
    """
    trend_data_points: Dict[date, Dict[str, List[float]]] = {}
    
    for c in checkins:
        dt = getattr(c, "created_at", None)
        if not dt:
            continue
            
        # 手動調整時區：UTC + Offset
        local_dt = dt + timedelta(hours=timezone_offset)
        date_key = local_dt.date()
        
        trend_data_points.setdefault(date_key, {"challenges": [], "skills": []})
        
        # 安全轉型
        c_val = float(getattr(c, "challenge_level", 0) or 0)
        s_val = float(getattr(c, "skill_level", 0) or 0)
        
        trend_data_points[date_key]["challenges"].append(c_val)
        trend_data_points[date_key]["skills"].append(s_val)

    trend_list = []
    for date_key in sorted(trend_data_points.keys()):
        vals = trend_data_points[date_key]
        # 防止除以零錯誤
        avg_c = sum(vals["challenges"]) / len(vals["challenges"]) if vals["challenges"] else 0
        avg_s = sum(vals["skills"]) / len(vals["skills"]) if vals["skills"] else 0
        
        trend_list.append({
            "date": date_key,
            "avg_challenge": round(avg_c, 2),
            "avg_skill": round(avg_s, 2),
        })
    return trend_list

def load_stopwords(file_path: Path) -> Set[str]:
    """从文件加载停用词列表（纯 IO 逻辑）。"""
    if not file_path.is_file():
        logger.warning(f"停用词文件未找到: {file_path}。将使用空停用词列表。")
        return set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            stopwords = {line.strip() for line in f if line.strip()}
        logger.info(f"成功从 {file_path} 加载 {len(stopwords)} 个停用词。")
        return stopwords
    except Exception as e:
        logger.error(f"加载停用词文件 {file_path} 时出错: {e}")
        return set()

# 初始化 STOPWORDS（调用者 import 时会执行）
# 使用 __file__ 確保路徑相對於當前 utils.py
STOPWORDS_PATH = Path(__file__).parent / 'assets' / 'stopwords.txt'
STOPWORDS = load_stopwords(STOPWORDS_PATH)

def _perform_word_cut(texts: List[str]) -> List[str]:
    """
    【優化重點】：
    1. 接收字符串列表 List[str]。
    2. 在子線程中執行大字符串合併 (" ".join)，避免阻塞主線程。
    3. 執行同步的 jieba 分詞。
    """
    # 耗時操作移至此處
    all_text = " ".join(texts)
    
    words = jieba.cut(all_text)
    return [word for word in words if word not in STOPWORDS and len(word) > 1]

async def generate_wordcloud(texts: List[str]) -> List[Dict[str, Any]]:
    """
    异步地从文本列表生成词频数组。
    """
    if not texts:
        return []
    
    # 【優化】：直接傳遞 List 給子線程函數，不要在主線程做 join
    meaningful_words = await run_in_threadpool(_perform_word_cut, texts)
    
    # Counter 即使在主線程也非常快，無需優化
    word_counts = Counter(meaningful_words)
    return [{"name": name, "value": value} for name, value in word_counts.most_common(30)]


def to_china_naive(dt: datetime) -> datetime:
    """
    將任何帶時區的時間 (Aware) 轉為 中國時間 (UTC+8) 的無時區時間 (Naive)。
    如果傳入原本就是 Naive，則假設它已經是中國時間，不做更動。
    """
    china_tz = timezone(timedelta(hours=8))
    
    if dt.tzinfo is None:
        # 修改邏輯：如果收到 Naive 時間，假設它是 UTC (系統時間)，並強制加上 UTC 時區
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(china_tz).replace(tzinfo=None)

async def save_raw_file(file: UploadFile, team_id: str) -> str: 
    """
    保存任意文件，不做任何處理，只做安全檢查。
    返回: 文件在服務器上的相對路徑 (用於存入數據庫)
    """
    filename = file.filename
    forbidden_chars = {"..", "/", "\\", "%", "'", "\"", "{", "}", "[", "]", "<", ">", "?", "*", "(", ")", " "}
    if any(char in filename for char in forbidden_chars):
        raise HTTPException(status_code=400, detail="Filename contains illegal characters")
    
    if len(filename) > 50:
        raise HTTPException(status_code=400, detail="Filename is too long (max 30 characters)")
    
    team_dir = BASE_UPLOAD_DIR / team_id
    team_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = team_dir / filename   #沒事 就直接存這樣之後取用也好拿，前面的過濾已經足夠安全

    # --- 3. 流式寫入 + 大小限制檢查 ---
    total_size = 0
    
    try:
        async with aiofiles.open(file_path, 'wb') as out_file:
            # 每次讀取 64KB，避免佔用過多內存
            while chunk := await file.read(65536): 
                total_size += len(chunk)
                
                if total_size > MAX_FILE_SIZE:
                    # 超過大小，拋出異常，並在 finally 區塊或下面刪除殘餘文件
                    raise HTTPException(status_code=413, detail="File size exceeds the 10MB limit.")
                
                await out_file.write(chunk)
                
    except Exception as e:
        # 發生錯誤時清理殘餘文件
        # 因為 os.remove 是阻塞的，這裡我們把它丟到線程池裡，避免影響本次請求的響應速度
        if file_path.exists():
            await run_in_threadpool(os.remove, file_path)
            
        # 如果是我們主動拋出的 (如大小超限)，繼續往上拋
        if isinstance(e, HTTPException):
            raise e
        # 其他 IO 錯誤
        print(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail="File upload failed.")

    # 返回路徑 (符合 Nginx 讀取路徑)
    return f"/static/uploads/{team_id}/{filename}"

async def delete_file_from_disk(file_path_str: str):
    """
    從硬盤刪除文件
    os.remove 是阻塞 IO，必須放入線程池，否則會卡住整個 API
    """
    try:
        # 路徑轉換：把 URL (/static/...) 轉為 相對路徑 (static/...)
        if file_path_str.startswith("/"):
            # lstrip("/") 會把 /static/uploads/... 變成 static/uploads/...
            # 這樣 Path() 才會把它當作相對路徑處理
            clean_path = file_path_str.lstrip("/")
        else:
            clean_path = file_path_str
            
        file_path = Path(clean_path)
        
        if file_path.exists():
            await run_in_threadpool(os.remove, file_path)
            
    except Exception as e:
        # 刪除失敗通常只記錄日誌，不中斷 API
        print(f"Error deleting file {file_path_str}: {e}")
    