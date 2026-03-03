FROM python:3.11-slim

# Обновляем списки пакетов и устанавливаем необходимые зависимости для Playwright и Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    ca-certificates \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libx11-xcb1 \
    libxss1 \
    libxtst6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем Playwright и браузер Chromium
RUN pip install playwright
RUN playwright install chromium
RUN playwright install-deps chromium

COPY . .

EXPOSE 8501
EXPOSE 8000

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]
