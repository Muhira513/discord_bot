# 1. 파이썬 베이스 이미지
FROM python:3.10-slim

# 2. 시스템 필수 패키지 설치 (ffmpeg, libopus, nodejs)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libopus0 \
    nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 3. 라이브러리 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 전체 파일 복사 (이때 cookies.txt가 프로젝트 폴더에 있어야 함)
COPY . .

# 5. 실행
CMD ["python", "hira_bot.py"]
