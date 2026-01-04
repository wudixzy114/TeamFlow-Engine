FROM python:3.10 as builder

WORKDIR /app

# 更換為速度更快的 APT 來源
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

# 安裝編譯 Python 套件所需的系統依賴
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# 複製並安裝 Python 依賴
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install --no-cache-dir -r requirements.txt

# --- 第二階段：正式運行階段 (Final Stage) ---
FROM python:3.10-slim

WORKDIR /app

# 更換 APT 來源
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

# [!! 關鍵 !!] 安裝 "運行時" 需要的依賴，而不是 "編譯時" 的
# libpq5 是 psycopg2 運行時需要的函式庫，比 libpq-dev 小很多
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/*

# 從建構階段複製已經安裝好的 Python 函式庫
COPY --from=builder /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# 複製你的應用程式碼
COPY ./app /app/app
COPY alembic.ini .
COPY alembic ./alembic
COPY entrypoint.sh .

RUN chmod +x ./entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--loop", "uvloop", "--http", "httptools", "--no-access-log"]