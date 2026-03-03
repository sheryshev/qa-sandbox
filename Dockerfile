# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем системные зависимости для Playwright (браузеры требуют библиотек)
RUN apt-get update && apt-get install -y \
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
    librandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем браузер Chromium внутри контейнера
RUN playwright install chromium
RUN playwright install-deps chromium

# Копируем код проекта
COPY . .

# Открываем порты для Streamlit и FastAPI
EXPOSE 8501
EXPOSE 8000

# Запуск приложения
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]
