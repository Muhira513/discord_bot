FROM python:3.10-slim

# 1. 필수 패키지 (ffmpeg: 소리 재생, nodejs: 유튜브 우회, libopus0: 오디오 코덱) 설치
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libopus0 \
    nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. 파이썬 라이브러리 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. 프로젝트 파일 복사 (로컬에 있는 최신 cookies.txt가 이때 복사됨)
COPY . .

# 4. 실행
CMD ["python", "hira_bot.py"]]
