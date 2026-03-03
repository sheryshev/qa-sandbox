FROM mcr.microsoft.com

WORKDIR /app

# Остальное оставляем как есть
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium
COPY . .

# Настройка порта для Railway
ENV PORT=8501
EXPOSE 8501
EXPOSE 8000

CMD streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
