from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import asyncio

app = FastAPI()

# Разрешаем CORS для фронтенда (если нужно)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Хранилище конфигурации UI элементов
ui_config = {
    "buttons": [{"id": "btn1", "label": "Кнопка 1", "visible": True}],
    "panels": [{"id": "panel1", "title": "Панель 1", "visible": True}],
    "comboboxes": [{"id": "combo1", "options": ["Опция 1", "Опция 2"], "visible": True}],
    "dropdowns": [{"id": "dd1", "options": ["Выпад 1", "Выпад 2"], "visible": True}],
}

# Лог автотестов (в памяти)
test_logs: List[str] = []

# Модели для REST API
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

# REST API для получения текущей конфигурации UI (GET)
@app.get("/api/ui-config", response_model=UIConfig)
async def get_ui_config():
    return ui_config

# REST API для обновления конфигурации UI (PUT - полное обновление)
@app.put("/api/ui-config", response_model=UIConfig)
async def put_ui_config(config: UIConfig):
    global ui_config
    # Обновляем только те поля, что пришли
    if config.buttons is not None:
        ui_config["buttons"] = [b.dict() for b in config.buttons]
    if config.panels is not None:
        ui_config["panels"] = [p.dict() for p in config.panels]
    if config.comboboxes is not None:
        ui_config["comboboxes"] = [c.dict() for c in config.comboboxes]
    if config.dropdowns is not None:
        ui_config["dropdowns"] = [d.dict() for d in config.dropdowns]
    return ui_config

# REST API для частичного обновления (PATCH)
@app.patch("/api/ui-config", response_model=UIConfig)
async def patch_ui_config(config: UIConfig):
    global ui_config
    if config.buttons is not None:
        for b in config.buttons:
            for i, old_b in enumerate(ui_config["buttons"]):
                if old_b["id"] == b.id:
                    ui_config["buttons"][i] = b.dict()
                    break
            else:
                ui_config["buttons"].append(b.dict())
    if config.panels is not None:
        for p in config.panels:
            for i, old_p in enumerate(ui_config["panels"]):
                if old_p["id"] == p.id:
                    ui_config["panels"][i] = p.dict()
                    break
            else:
                ui_config["panels"].append(p.dict())
    if config.comboboxes is not None:
        for c in config.comboboxes:
            for i, old_c in enumerate(ui_config["comboboxes"]):
                if old_c["id"] == c.id:
                    ui_config["comboboxes"][i] = c.dict()
                    break
            else:
                ui_config["comboboxes"].append(c.dict())
    if config.dropdowns is not None:
        for d in config.dropdowns:
            for i, old_d in enumerate(ui_config["dropdowns"]):
                if old_d["id"] == d.id:
                    ui_config["dropdowns"][i] = d.dict()
                    break
            else:
                ui_config["dropdowns"].append(d.dict())
    return ui_config

# REST API для удаления UI элемента (DELETE)
@app.delete("/api/ui-config/{element_type}/{element_id}")
async def delete_ui_element(element_type: str, element_id: str):
    if element_type not in ui_config:
        raise HTTPException(status_code=404, detail="Element type not found")
    before_count = len(ui_config[element_type])
    ui_config[element_type] = [el for el in ui_config[element_type] if el["id"] != element_id]
    after_count = len(ui_config[element_type])
    if before_count == after_count:
        raise HTTPException(status_code=404, detail="Element not found")
    return {"detail": "Deleted"}

# Функция для имитации автотестов UI и API
async def run_autotests():
    test_logs.clear()
    test_logs.append("Запуск автотестов...")

    # Тест 1: Проверка видимости кнопок
    for btn in ui_config["buttons"]:
        if btn["visible"]:
            test_logs.append(f"Тест кнопки {btn['id']}: видима - OK")
        else:
            test_logs.append(f"Тест кнопки {btn['id']}: не видима - OK")

    # Тест 2: Проверка API доступности (имитация)
    test_logs.append("Тест API GET /api/ui-config: ожидается 200")
    # Здесь можно добавить реальные проверки, сейчас просто имитация
    test_logs.append("Ответ 200 получен - OK")

    # Тест 3: Проверка добавления элемента (POST)
    test_logs.append("Тест добавления кнопки POST /api/ui-config")
    new_button = {"id": "btn_test", "label": "Тестовая кнопка", "visible": True}
    ui_config["buttons"].append(new_button)
    test_logs.append("Кнопка добавлена - OK")
    # Удаляем тестовую кнопку
    ui_config["buttons"] = [b for b in ui_config["buttons"] if b["id"] != "btn_test"]

    test_logs.append("Все тесты завершены успешно.")

# REST API для запуска автотестов (POST)
@app.post("/api/run-tests")
async def run_tests():
    # Запускаем автотесты асинхронно
    asyncio.create_task(run_autotests())
    return {"detail": "Тесты запущены"}

# REST API для получения логов автотестов (GET)
@app.get("/api/test-logs")
async def get_test_logs():
    return {"logs": test_logs}

# Веб-страница с UI и кнопками для управления
@app.get("/", response_class=HTMLResponse)
async def index():
    return """
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8" />
<title>Демонстрация автотестирования</title>
<style>
  body { font-family: Arial, sans-serif; margin: 20px; }
  #log { width: 100%; height: 200px; border: 1px solid #ccc; overflow-y: scroll; background: #f9f9f9; padding: 10px; }
  .hidden { display: none; }
  .panel { border: 1px solid #aaa; padding: 10px; margin-bottom: 10px; }
  button { margin: 5px; }
</style>
</head>
<body>
<h1>Демонстрация автотестирования</h1>

<div>
  <button onclick="loadConfig()">Загрузить конфигурацию UI (GET)</button>
  <button onclick="runTests()">Запустить автотесты</button>
</div>

<div id="ui-elements"></div>

<h2>Лог автотестов</h2>
<div id="log"></div>

<script>
async function loadConfig() {
  const res = await fetch('/api/ui-config');
  const config = await res.json();
  const container = document.getElementById('ui-elements');
  container.innerHTML = '';

  // Отображаем кнопки
  if(config.buttons) {
    config.buttons.forEach(btn => {
      if(btn.visible) {
        const b = document.createElement('button');
        b.textContent = btn.label;
        container.appendChild(b);
      }
    });
  }

  // Отображаем панели
  if(config.panels) {
    config.panels.forEach(panel => {
      if(panel.visible) {
        const div = document.createElement('div');
        div.className = 'panel';
        div.textContent = panel.title;
        container.appendChild(div);
      }
    });
  }

  // Отображаем comboboxes
  if(config.comboboxes) {
    config.comboboxes.forEach(combo => {
      if(combo.visible) {
        const select = document.createElement('select');
        combo.options.forEach(opt => {
          const option = document.createElement('option');
          option.textContent = opt;
          select.appendChild(option);
        });
        container.appendChild(select);
      }
    });
  }

  // Отображаем dropdowns (аналогично combobox)
  if(config.dropdowns) {
    config.dropdowns.forEach(dd => {
      if(dd.visible) {
        const select = document.createElement('select');
        dd.options.forEach(opt => {
          const option = document.createElement('option');
          option.textContent = opt;
          select.appendChild(option);
        });
        container.appendChild(select);
      }
    });
  }
}

async function runTests() {
  document.getElementById('log').textContent = "Запуск тестов...";
  await fetch('/api/run-tests', { method: 'POST' });

  // Периодически обновляем логи
  const logDiv = document.getElementById('log');
  const interval = setInterval(async () => {
    const res = await fetch('/api/test-logs');
    const data = await res.json();
    logDiv.textContent = data.logs.join('\\n');
    logDiv.scrollTop = logDiv.scrollHeight;

    if(data.logs.length > 0 && data.logs[data.logs.length - 1].includes("завершены")) {
      clearInterval(interval);
    }
  }, 1000);
}

// Загружаем конфигурацию при загрузке страницы
window.onload = loadConfig;
</script>

</body>
</html>
"""
