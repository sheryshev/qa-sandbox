# Используем официальный образ Python 3.11 slim
FROM python:3.11-slim

# Устанавливаем системные зависимости для Playwright и Chromium
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

# Рабочая директория внутри контейнера
WORKDIR /app

# Копируем файл с зависимостями и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем Playwright и браузеры
RUN pip install playwright
RUN playwright install chromium
RUN playwright install-deps chromium

# Копируем весь код проекта
COPY . .

# Открываем порты (необязательно, но полезно для локального теста)
EXPOSE 8501
EXPOSE 8000

# Запускаем Streamlit, используя порт из переменной окружения PORT (важно для Railway)
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]
