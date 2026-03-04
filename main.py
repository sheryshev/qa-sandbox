from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import subprocess
import httpx

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULT_UI_CONFIG = {
    "buttons": [{"id": "btn1", "label": "Кнопка 1", "visible": True}],
    "panels": [{"id": "panel1", "title": "Панель 1", "visible": True}],
    "comboboxes": [{"id": "combo1", "options": ["Опция 1", "Опция 2"], "visible": True}],
    "dropdowns": [{"id": "dd1", "options": ["Выпад 1", "Выпад 2"], "visible": True}],
}

ui_config = {k: [dict(item) for item in v] for k, v in DEFAULT_UI_CONFIG.items()}
http_status_codes = {"default": 200}  # Хранилище для HTTP-кодов

test_logs: List[str] = []
action_logs: List[str] = []
pytest_report = ""

class Button(BaseModel):
    id: str
    label: str
    visible: bool

class Panel(BaseModel):
    id: str
    title: str
    visible: bool

class ComboBox(BaseModel):
    id: str
    options: List[str]
    visible: bool

class Dropdown(BaseModel):
    id: str
    options: List[str]
    visible: bool

class UIConfig(BaseModel):
    buttons: Optional[List[Button]] = None
    panels: Optional[List[Panel]] = None
    comboboxes: Optional[List[ComboBox]] = None
    dropdowns: Optional[List[Dropdown]] = None

@app.middleware("http")
async def log_requests(request: Request, call_next):
    method = request.method
    url = str(request.url)
    action_logs.append(f"REST {method} {url}")
    response = await call_next(request)
    return response

@app.get("/api/ui-config", response_model=UIConfig, status_code=status.HTTP_200_OK)
async def get_ui_config():
    return ui_config

@app.put("/api/ui-config", response_model=UIConfig, status_code=status.HTTP_200_OK)
async def put_ui_config(config: UIConfig):
    global ui_config
    if config.buttons is not None:
        ui_config["buttons"] = [b.dict() for b in config.buttons]
    if config.panels is not None:
        ui_config["panels"] = [p.dict() for p in config.panels]
    if config.comboboxes is not None:
        ui_config["comboboxes"] = [c.dict() for c in config.comboboxes]
    if config.dropdowns is not None:
        ui_config["dropdowns"] = [d.dict() for d in config.dropdowns]
    action_logs.append("PUT /api/ui-config - обновлена конфигурация UI")
    return ui_config

@app.put("/api/http-status", status_code=status.HTTP_200_OK)
async def update_http_status(code: int):
    if code < 100 or code > 599:
        raise HTTPException(status_code=400, detail="Некорректный HTTP-код")
    http_status_codes["default"] = code
    action_logs.append(f"HTTP-код по умолчанию изменён на {code}")
    return {"detail": f"HTTP-код изменён на {code}"}

@app.get("/api/http-status", status_code=status.HTTP_200_OK)
async def get_http_status():
    return {"http_status": http_status_codes["default"]}

@app.post("/api/run-tests")
async def run_tests():
    test_logs.clear()
    test_logs.append("Запуск автотестов...")
    current_status = http_status_codes["default"]
    if current_status != 200:
        test_logs.append(f"Ошибка: HTTP-код {current_status} не равен 200!")
        return {"detail": "Тест завершён с ошибкой", "http_status": current_status}
    test_logs.append("Все тесты завершены успешно.")
    return {"detail": "Тесты завершены успешно"}

@app.get("/api/test-logs")
async def get_test_logs():
    return {"logs": test_logs}

@app.get("/logs", response_class=HTMLResponse)
async def logs_page():
    return """
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Логи автотестов</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet" />
</head>
<body>
<div class="container">
  <h1>Логи автотестов</h1>
  <pre id="testLogs">Загрузка...</pre>
  <a href="/" class="btn btn-primary mt-3">Вернуться на главную</a>
</div>
<script>
async function updateLogs() {
  const res = await fetch('/api/test-logs');
  const data = await res.json();
  document.getElementById('testLogs').textContent = data.logs.join('\\n');
}
setInterval(updateLogs, 2000);
updateLogs();
</script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def index():
    return """
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Демонстрация автотестирования</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet" />
</head>
<body>
<div class="container">
  <h1>Демонстрация автотестирования</h1>
  <div class="mb-3">
    <label for="httpStatus" class="form-label">Изменить HTTP-код ответа:</label>
    <input type="number" id="httpStatus" class="form-control" placeholder="Введите HTTP-код (например, 200)" />
    <button id="updateHttpStatus" class="btn btn-primary mt-2">Обновить HTTP-код</button>
  </div>
  <button id="runTests" class="btn btn-success">Запустить автотесты</button>
  <h2 class="mt-4">Логи автотестов</h2>
  <pre id="testLogs">Загрузка...</pre>
</div>
<script>
document.getElementById('updateHttpStatus').addEventListener('click', async () => {
  const code = document.getElementById('httpStatus').value;
  if (!code) {
    alert('Введите HTTP-код');
    return;
  }
  const res = await fetch('/api/http-status', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code: parseInt(code) })
  });
  if (res.ok) {
    alert('HTTP-код обновлён');
  } else {
    const err = await res.json();
    alert('Ошибка: ' + err.detail);
  }
});

document.getElementById('runTests').addEventListener('click', async () => {
  const res = await fetch('/api/run-tests', { method: 'POST' });
  const data = await res.json();
  alert(data.detail);
  updateLogs();
});

async function updateLogs() {
  const res = await fetch('/api/test-logs');
  const data = await res.json();
  document.getElementById('testLogs').textContent = data.logs.join('\\n');
}
updateLogs();
</script>
</body>
</html>
"""
