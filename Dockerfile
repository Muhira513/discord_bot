# ===== Python 베이스 이미지 =====
FROM python:3.10-slim

# ===== 시스템 패키지 설치 =====
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libopus0 \
    libopus-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ===== requirements 설치 =====
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ===== 봇 코드 복사 =====
COPY hira_bot.py .

# ===== 실행 =====
CMD ["python", "hira_bot.py"]
