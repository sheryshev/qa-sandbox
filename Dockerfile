FROM ://mcr.microsoft.com

WORKDIR /app

# Копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем браузер внутри контейнера
RUN playwright install chromium

# Копируем код
COPY . .

# Railway автоматически назначает порт через переменную среды PORT
# Если её нет, используем 8501
ENV PORT=8501

EXPOSE 8501
EXPOSE 8000

# Запуск с привязкой к порту Railway
CMD streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
