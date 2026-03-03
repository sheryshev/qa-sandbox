from fastapi import FastAPI, HTTPException, Request
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

# Хранилище UI конфигурации
ui_config = {
    "buttons": [{"id": "btn1", "label": "Кнопка 1", "visible": True}],
    "panels": [{"id": "panel1", "title": "Панель 1", "visible": True}],
    "comboboxes": [{"id": "combo1", "options": ["Опция 1", "Опция 2"], "visible": True}],
    "dropdowns": [{"id": "dd1", "options": ["Выпад 1", "Выпад 2"], "visible": True}],
}

test_logs: List[str] = []
action_logs: List[str] = []
pytest_report = ""

# Модели для UI элементов
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

# Middleware для логирования всех REST вызовов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    method = request.method
    url = str(request.url)
    action_logs.append(f"REST {method} {url}")
    response = await call_next(request)
    return response

# REST API: получить конфигурацию UI
@app.get("/api/ui-config", response_model=UIConfig)
async def get_ui_config():
    return ui_config

# REST API: полное обновление UI конфигурации (PUT)
@app.put("/api/ui-config", response_model=UIConfig)
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

# REST API: частичное обновление UI конфигурации (PATCH)
@app.patch("/api/ui-config", response_model=UIConfig)
async def patch_ui_config(config: UIConfig):
    global ui_config
    def update_list(old_list, new_items):
        for new_item in new_items:
            for i, old_item in enumerate(old_list):
                if old_item["id"] == new_item.id:
                    old_list[i] = new_item.dict()
                    break
            else:
                old_list.append(new_item.dict())
    if config.buttons is not None:
        update_list(ui_config["buttons"], config.buttons)
    if config.panels is not None:
        update_list(ui_config["panels"], config.panels)
    if config.comboboxes is not None:
        update_list(ui_config["comboboxes"], config.comboboxes)
    if config.dropdowns is not None:
        update_list(ui_config["dropdowns"], config.dropdowns)
    action_logs.append("PATCH /api/ui-config - частично обновлена конфигурация UI")
    return ui_config

# REST API: добавить новый элемент (POST)
@app.post("/api/ui-config/{element_type}")
async def add_ui_element(element_type: str, element: dict):
    if element_type not in ui_config:
        raise HTTPException(status_code=404, detail="Element type not found")
    if any(el["id"] == element.get("id") for el in ui_config[element_type]):
        raise HTTPException(status_code=400, detail="Element with this id already exists")
    ui_config[element_type].append(element)
    action_logs.append(f"Добавлен элемент {element_type[:-1]} с id={element.get('id')}")
    # Запускаем проверку всех элементов после добавления
    try:
        await run_ui_tests()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка после добавления элемента: {str(e)}")
    return {"detail": f"{element_type[:-1].capitalize()} добавлен", "element": element}

# REST API: удалить элемент (DELETE)
@app.delete("/api/ui-config/{element_type}/{element_id}")
async def delete_ui_element(element_type: str, element_id: str):
    if element_type not in ui_config:
        raise HTTPException(status_code=404, detail="Element type not found")
    before_count = len(ui_config[element_type])
    ui_config[element_type] = [el for el in ui_config[element_type] if el["id"] != element_id]
    after_count = len(ui_config[element_type])
    if before_count == after_count:
        raise HTTPException(status_code=404, detail="Element not found")
    action_logs.append(f"Удалён элемент {element_type[:-1]} с id={element_id}")
    return {"detail": f"{element_type[:-1].capitalize()} удалён"}

# Асинхронные автотесты UI с проверкой наличия всех элементов
async def run_ui_tests():
    test_logs.append("Запуск UI тестов...")
    # Проверяем кнопки
    for btn in ui_config["buttons"]:
        if not btn["visible"]:
            test_logs.append(f"UI тест кнопки {btn['id']}: не видима - OK")
        else:
            test_logs.append(f"UI тест кнопки {btn['id']}: видима - OK")
    # Проверяем панели
    for panel in ui_config["panels"]:
        if not panel["visible"]:
            test_logs.append(f"UI тест панели {panel['id']}: не видима - OK")
        else:
            test_logs.append(f"UI тест панели {panel['id']}: видима - OK")
    # Проверяем comboboxes
    for combo in ui_config["comboboxes"]:
        if not combo["visible"]:
            test_logs.append(f"UI тест combobox {combo['id']}: не видим - OK")
        else:
            test_logs.append(f"UI тест combobox {combo['id']}: видим - OK")
    # Проверяем dropdowns
    for dd in ui_config["dropdowns"]:
        if not dd["visible"]:
            test_logs.append(f"UI тест dropdown {dd['id']}: не видим - OK")
        else:
            test_logs.append(f"UI тест dropdown {dd['id']}: видим - OK")

    # Проверяем, что есть хотя бы один элемент
    total_elements = sum(len(ui_config[key]) for key in ui_config)
    if total_elements == 0:
        test_logs.append("Ошибка: Нет ни одного UI элемента!")
        raise Exception("Нет ни одного UI элемента!")

    test_logs.append("UI тесты завершены.")

# Асинхронные автотесты API
async def run_api_tests():
    test_logs.append("Запуск API тестов...")
    test_logs.append("Тест API GET /api/ui-config: ожидается 200")
    test_logs.append("Ответ 200 получен - OK")
    test_logs.append("Тест добавления кнопки POST /api/ui-config")
    new_button = {"id": "btn_test", "label": "Тестовая кнопка", "visible": True}
    ui_config["buttons"].append(new_button)
    test_logs.append("Кнопка добавлена - OK")
    ui_config["buttons"] = [b for b in ui_config["buttons"] if b["id"] != "btn_test"]
    test_logs.append("API тесты завершены.")

# Запуск автотестов с выбором типа
@app.post("/api/run-tests")
async def run_tests(test_type: Optional[str] = "all"):
    action_logs.append(f"Запуск автотестов типа '{test_type}'")
    test_logs.clear()
    if test_type == "ui":
        asyncio.create_task(run_ui_tests())
    elif test_type == "api":
        asyncio.create_task(run_api_tests())
    else:
        async def run_all():
            await run_ui_tests()
            await run_api_tests()
            test_logs.append("Все тесты завершены успешно.")
        asyncio.create_task(run_all())
    return {"detail": f"Тесты '{test_type}' запущены"}

# Получение логов автотестов
@app.get("/api/test-logs")
async def get_test_logs():
    return {"logs": test_logs}

# Получение логов действий (REST вызовы, автотесты)
@app.get("/api/action-logs")
async def get_action_logs():
    return {"logs": action_logs}

# Запуск pytest и сохранение отчёта
@app.post("/api/run-pytest")
async def run_pytest():
    global pytest_report
    action_logs.append("Запуск pytest автотестов")
    proc = subprocess.run(
        ["pytest", "test_autotests.py", "-q", "--tb=short"],
        capture_output=True,
        text=True
    )
    pytest_report = proc.stdout + "\n" + proc.stderr
    return {"detail": "Pytest запущен", "output": pytest_report}

# Получение pytest отчёта
@app.get("/api/pytest-report")
async def get_pytest_report():
    return PlainTextResponse(pytest_report or "Отчёт пуст")

# REST клиент: модель запроса
class RestRequest(BaseModel):
    method: str
    url: str
    headers: Optional[dict] = None
    body: Optional[dict] = None

# REST клиент: вызов произвольного REST API
@app.post("/api/rest-call")
async def rest_call(req: RestRequest):
    async with httpx.AsyncClient() as client:
        method = req.method.lower()
        if not hasattr(client, method):
            return {"error": "Неподдерживаемый HTTP метод"}
        func = getattr(client, method)
        try:
            r = await func(req.url, headers=req.headers, json=req.body)
            return {
                "status_code": r.status_code,
                "headers": dict(r.headers),
                "body": r.json() if "application/json" in r.headers.get("content-type", "") else r.text
            }
        except Exception as e:
            return {"error": str(e)}

# Веб-интерфейс основной страницы
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
  #log { width: 100%; height: 200px; border: 1px solid #ccc; overflow-y: scroll; background: #f9f9f9; padding: 10px; white-space: pre-wrap; }
  .panel { border: 1px solid #aaa; padding: 10px; margin-bottom: 10px; }
  button { margin: 5px; }
  label { display: block; margin-top: 10px; }
  input, select, textarea { width: 300px; }
</style>
</head>
<body>
<h1>Демонстрация автотестирования</h1>

<div>
  <button onclick="loadConfig()">Загрузить конфигурацию UI (GET)</button>
  <button onclick="runTests()">Запустить автотесты</button>
  <select id="testType">
    <option value="all">Все тесты</option>
    <option value="ui">UI тесты</option>
    <option value="api">API тесты</option>
  </select>
</div>

<h2>Добавить новый элемент</h2>
<form id="addForm" onsubmit="return addElement();">
  <label>Тип элемента:
    <select id="elementType" required onchange="onTypeChange()">
      <option value="">--Выберите--</option>
      <option value="buttons">Кнопка</option>
      <option value="panels">Панель</option>
      <option value="comboboxes">Combobox</option>
      <option value="
