# Используем готовый образ от авторов Playwright (в нем уже есть все либы)
FROM ://mcr.microsoft.com

# Рабочая директория
WORKDIR /app

# Копируем только requirements сначала (для кэширования)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальной код
COPY . .

# Открываем порты
EXPOSE 8501
EXPOSE 8000

# Запуск (0.0.0.0 обязателен для Docker)
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]
