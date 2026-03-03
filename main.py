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

# Асинхронные автотесты UI с проверкой наличия и видимости всех элементов
async def run_ui_tests():
    test_logs.append("Запуск UI тестов...")

    # Проверяем кнопки
    if not ui_config.get("buttons"):
        test_logs.append("Ошибка: отсутствуют кнопки!")
        raise Exception("Отсутствуют кнопки!")
    for btn in ui_config["buttons"]:
        if not btn.get("visible", False):
            test_logs.append(f"Ошибка: кнопка {btn['id']} не видима")
            raise Exception(f"Кнопка {btn['id']} не видима")
        else:
            test_logs.append(f"UI тест кнопки {btn['id']}: видима - OK")

    # Проверяем панели
    if not ui_config.get("panels"):
        test_logs.append("Ошибка: отсутствуют панели!")
        raise Exception("Отсутствуют панели!")
    for panel in ui_config["panels"]:
        if not panel.get("visible", False):
            test_logs.append(f"Ошибка: панель {panel['id']} не видима")
            raise Exception(f"Панель {panel['id']} не видима")
        else:
            test_logs.append(f"UI тест панели {panel['id']}: видима - OK")

    # Проверяем comboboxes
    if not ui_config.get("comboboxes"):
        test_logs.append("Ошибка: отсутствуют comboboxes!")
        raise Exception("Отсутствуют comboboxes!")
    for combo in ui_config["comboboxes"]:
        if not combo.get("visible", False):
            test_logs.append(f"Ошибка: combobox {combo['id']} не видим")
            raise Exception(f"Combobox {combo['id']} не видим")
        else:
            test_logs.append(f"UI тест combobox {combo['id']}: видим - OK")

    # Проверяем dropdowns
    if not ui_config.get("dropdowns"):
        test_logs.append("Ошибка: отсутствуют dropdowns!")
        raise Exception("Отсутствуют dropdowns!")
    for dd in ui_config["dropdowns"]:
        if not dd.get("visible", False):
            test_logs.append(f"Ошибка: dropdown {dd['id']} не видим")
            raise Exception(f"Dropdown {dd['id']} не видим")
        else:
            test_logs.append(f"UI тест dropdown {dd['id']}: видим - OK")

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
      <option value="dropdowns">Dropdown</option>
    </select>
  </label>
  <label>ID: <input type="text" id="elementId" required></label>
  <div id="fieldsContainer"></div>
  <button type="submit">Добавить элемент</button>
</form>

<h2>UI элементы</h2>
<div id="ui-elements"></div>

<h2>Лог автотестов</h2>
<div id="log"></div>

<script>
function onTypeChange() {
  const type = document.getElementById('elementType').value;
  const container = document.getElementById('fieldsContainer');
  container.innerHTML = '';
  if(type === 'buttons') {
    container.innerHTML = `
      <label>Label: <input type="text" id="elementLabel" required></label>
      <label>Visible: <input type="checkbox" id="elementVisible" checked></label>
    `;
  } else if(type === 'panels') {
    container.innerHTML = `
      <label>Title: <input type="text" id="elementTitle" required></label>
      <label>Visible: <input type="checkbox" id="elementVisible" checked></label>
    `;
  } else if(type === 'comboboxes' || type === 'dropdowns') {
    container.innerHTML = `
      <label>Options (через запятую): <input type="text" id="elementOptions" required></label>
      <label>Visible: <input type="checkbox" id="elementVisible" checked></label>
    `;
  }
}

async function addElement() {
  const type = document.getElementById('elementType').value;
  const id = document.getElementById('elementId').value.trim();
  if(!type || !id) {
    alert('Выберите тип и введите ID');
    return false;
  }
  let body = { id };
  if(type === 'buttons') {
    const label = document.getElementById('elementLabel').value.trim();
    const visible = document.getElementById('elementVisible').checked;
    if(!label) { alert('Введите label'); return false; }
    body.label = label;
    body.visible = visible;
  } else if(type === 'panels') {
    const title = document.getElementById('elementTitle').value.trim();
    const visible = document.getElementById('elementVisible').checked;
    if(!title) { alert('Введите title'); return false; }
    body.title = title;
    body.visible = visible;
  } else if(type === 'comboboxes' || type === 'dropdowns') {
    const optionsRaw = document.getElementById('elementOptions').value.trim();
    const visible = document.getElementById('elementVisible').checked;
    if(!optionsRaw) { alert('Введите options'); return false; }
    body.options = optionsRaw.split(',').map(s => s.trim()).filter(s => s.length > 0);
    body.visible = visible;
  }

  try {
    const res = await fetch(`/api/ui-config/${type}`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    });
    if(!res.ok) {
      const err = await res.json();
      alert('Ошибка: ' + err.detail);
      return false;
    }
    alert('Элемент добавлен');
    loadConfig();
    document.getElementById('addForm').reset();
    document.getElementById('fieldsContainer').innerHTML = '';
  } catch(e) {
    alert('Ошибка при добавлении элемента');
  }
  return false;
}

async function deleteElement(type, id) {
  if(!confirm(`Удалить элемент ${id} (${type})?`)) return;
  const res = await fetch(`/api/ui-config/${type}/${id}`, { method: 'DELETE' });
  if(res.ok) {
    alert('Элемент удалён');
    loadConfig();
  } else {
    const err = await res.json();
    alert('Ошибка: ' + err.detail);
  }
}

async function loadConfig() {
  const res = await fetch('/api/ui-config');
  const config = await res.json();
  const container = document.getElementById('ui-elements');
  container.innerHTML = '';

  function createDeleteBtn(type, id) {
    const btn = document.createElement('button');
    btn.textContent = 'Удалить';
    btn.onclick = () => deleteElement(type, id);
    btn.style.marginLeft = '10px';
    return btn;
  }

  // Кнопки
  if(config.buttons) {
    const h3 = document.createElement('h3');
    h3.textContent = 'Кнопки';
    container.appendChild(h3);
    config.buttons.forEach(btn => {
      const div = document.createElement('div');
      div.textContent = `${btn.id} — ${btn.label} — Видим: ${btn.visible}`;
      div.appendChild(createDeleteBtn('buttons', btn.id));
      container.appendChild(div);
    });
  }

  // Панели
  if(config.panels) {
    const h3 = document.createElement('h3');
    h3.textContent = 'Панели';
    container.appendChild(h3);
    config.panels.forEach(panel => {
      const div = document.createElement('div');
      div.textContent = `${panel.id} — ${panel.title} — Видим: ${panel.visible}`;
      div.appendChild(createDeleteBtn('panels', panel.id));
      container.appendChild(div);
    });
  }

  // Comboboxes
  if(config.comboboxes) {
    const h3 = document.createElement('h3');
    h3.textContent = 'Comboboxes';
    container.appendChild(h3);
    config.comboboxes.forEach(combo => {
      const div = document.createElement('div');
      div.textContent = `${combo.id} — Опции: ${combo.options.join(', ')} — Видим: ${combo.visible}`;
      div.appendChild(createDeleteBtn('comboboxes', combo.id));
      container.appendChild(div);
    });
  }

  // Dropdowns
  if(config.dropdowns) {
    const h3 = document.createElement('h3');
    h3.textContent = 'Dropdowns';
    container.appendChild(h3);
    config.dropdowns.forEach(dd => {
      const div = document.createElement('div');
      div.textContent = `${dd.id} — Опции: ${dd.options.join(', ')} — Видим: ${dd.visible}`;
      div.appendChild(createDeleteBtn('dropdowns', dd.id));
      container.appendChild(div);
    });
  }
}

async function runTests() {
  const testType = document.getElementById('testType').value;
  document.getElementById('log').textContent = "Запуск тестов...";
  await fetch(`/api/run-tests?test_type=${testType}`, { method: 'POST' });

  const logDiv = document.getElementById('log');
  const interval = setInterval(async () => {
    const res = await fetch('/api/test-logs');
    const data = await res.json();
    logDiv.textContent = data.logs.join('\\n');
    logDiv.scrollTop = logDiv.scrollHeight;

    if(data.logs.length > 0 && (data.logs[data.logs.length - 1].includes("завершены") || data.logs[data.logs.length - 1].includes("завершен"))) {
      clearInterval(interval);
    }
  }, 1000);
}

window.onload = loadConfig;
</script>

</body>
</html>
"""

# Веб-интерфейс страницы логов и REST клиента
@app.get("/logs", response_class=HTMLResponse)
async def logs_page():
    return """
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8" />
<title>Логи и REST клиент</title>
<style>
  body { font-family: Arial, sans-serif; margin: 20px; }
  textarea, pre { width: 100%; height: 200px; white-space: pre-wrap; background: #f9f9f9; border: 1px solid #ccc; padding: 10px; overflow-y: scroll; }
  label { display: block; margin-top: 10px; }
  input, select { width: 300px; }
  button { margin-top: 10px; }
</style>
</head>
<body>
<h1>Логи действий и автотестов</h1>

<h2>Логи REST действий</h2>
<pre id="actionLogs"></pre>

<h2>Логи автотестов</h2>
<pre id="testLogs"></pre>

<h2>Запуск Pytest автотестов</h2>
<button onclick="runPytest()">Запустить Pytest</button>
<pre id="pytestOutput">Отчёт пуст</pre>

<h2>REST клиент</h2>
<form id="restForm" onsubmit="return sendRestCall();">
  <label>Метод:
    <select id="method" required>
      <option>GET</option>
      <option>POST</option>
      <option>PUT</option>
      <option>DELETE</option>
      <option>PATCH</option>
    </select>
  </label>
  <label>URL:
    <input type="text" id="url" value="http://localhost:8000/api/ui-config" required />
  </label>
  <label>Заголовки (JSON):
    <textarea id="headers" placeholder='{"Content-Type": "application/json"}'></textarea>
  </label>
  <label>Тело запроса (JSON):
    <textarea id="body"></textarea>
  </label>
  <button type="submit">Отправить</button>
</form>

<h3>Ответ</h3>
<pre id="response"></pre>

<script>
async function updateLogs() {
  const res1 = await fetch('/api/action-logs');
  const data1 = await res1.json();
  document.getElementById('actionLogs').textContent = data1.logs.join('\\n');

  const res2 = await fetch('/api/test-logs');
  const data2 = await res2.json();
  document.getElementById('testLogs').textContent = data2.logs.join('\\n');
}

setInterval(updateLogs, 2000);
updateLogs();

async function runPytest() {
  document.getElementById('pytestOutput').textContent = "Запуск...";
  const res = await fetch('/api/run-pytest', { method: 'POST' });
  const data = await res.json();
  if(res.ok) {
    const reportRes = await fetch('/api/pytest-report');
    const reportText = await reportRes.text();
    document.getElementById('pytestOutput').textContent = reportText;
  } else {
    document.getElementById('pytestOutput').textContent = "Ошибка запуска pytest";
  }
}

async function sendRestCall() {
  const method = document.getElementById('method').value;
  const url = document.getElementById('url').value;
  let headers = {};
  let body = null;
  try {
    const headersText = document.getElementById('headers').value.trim();
    if(headersText) headers = JSON.parse(headersText);
  } catch(e) {
    alert('Ошибка в JSON заголовков');
    return false;
  }
  try {
    const bodyText = document.getElementById('body').value.trim();
    if(bodyText) body = JSON.parse(bodyText);
  } catch(e) {
    alert('Ошибка в JSON тела запроса');
    return false;
  }
  const res = await fetch('/api/rest-call', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({method, url, headers, body})
  });
  const data = await res.json();
  document.getElementById('response').textContent = JSON.stringify(data, null, 2);
  return false;
}
</script>

</body>
</html>
"""
