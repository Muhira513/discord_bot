# ===== Python 베이스 이미지 =====
FROM python:3.10-slim

# ===== 시스템 패키지 설치 (nodejs 추가됨) =====
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libopus0 \
    libopus-dev \
    nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리
WORKDIR /app

# requirements 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 봇 코드 및 쿠키 파일 복사
# (프로젝트 폴더에 cookies.txt가 있다고 가정합니다)
COPY . .

# ===== 봇 실행 =====
CMD ["python", "hira_bot.py"]
