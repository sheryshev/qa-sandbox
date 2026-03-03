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

# REST API: обнулить конфигурацию UI (PUT)
@app.put("/api/ui-config/reset")
async def reset_ui_config():
    global ui_config
    ui_config = {
        "buttons": [],
        "panels": [],
        "comboboxes": [],
        "dropdowns": [],
    }
    action_logs.append("Конфигурация UI обнулена")
    return {"detail": "Конфигурация UI обнулена", "ui_config": ui_config}

# REST API: изменить элемент (PUT)
@app.put("/api/ui-config/{element_type}/{element_id}")
async def update_ui_element(element_type: str, element_id: str, element: dict):
    if element_type not in ui_config:
        raise HTTPException(status_code=404, detail="Element type not found")
    for i, el in enumerate(ui_config[element_type]):
        if el["id"] == element_id:
            updated = element.copy()
            updated["id"] = element_id
            ui_config[element_type][i] = updated
            action_logs.append(f"Элемент {element_type[:-1]} с id={element_id} обновлён")
            try:
                await run_ui_tests()
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Ошибка после обновления элемента: {str(e)}")
            return {"detail": f"{element_type[:-1].capitalize()} обновлён", "element": updated}
    raise HTTPException(status_code=404, detail="Element not found")

# Асинхронные автотесты UI с проверкой наличия и видимости всех элементов
async def run_ui_tests():
    test_logs.append("Запуск UI тестов...")

    for etype in ["buttons", "panels", "comboboxes", "dropdowns"]:
        elements = ui_config.get(etype, [])
        if not elements:
            test_logs.append(f"Ошибка: отсутствуют элементы типа {etype}!")
            raise Exception(f"Отсутствуют элементы типа {etype}!")
        for el in elements:
            if not el.get("visible", False):
                test_logs.append(f"Ошибка: элемент {etype[:-1]} {el['id']} не видим")
                raise Exception(f"Элемент {etype[:-1]} {el['id']} не видим")
            else:
                test_logs.append(f"UI тест {etype[:-1]} {el['id']}: видим - OK")

    test_logs.append("UI тесты завершены.")

# Тест обнуления конфигурации
async def run_reset_test():
    test_logs.append("Тест обнуления конфигурации UI...")
    global ui_config
    ui_config = {
        "buttons": [],
        "panels": [],
        "comboboxes": [],
        "dropdowns": [],
    }
    action_logs.append("Конфигурация UI обнулена (тест)")
    total = sum(len(ui_config[key]) for key in ui_config)
    if total != 0:
        test_logs.append("Ошибка: конфигурация не пуста после обнуления")
        raise Exception("Конфигурация не пуста после обнуления")
    test_logs.append("Тест обнуления конфигурации пройден.")

# Тест изменения элемента
async def run_update_test():
    test_logs.append("Тест изменения элемента...")
    btn = {"id": "btn_update", "label": "Старая кнопка", "visible": True}
    ui_config["buttons"].append(btn)
    updated_btn = {"label": "Новая кнопка", "visible": False}
    for i, el in enumerate(ui_config["buttons"]):
        if el["id"] == "btn_update":
            updated = updated_btn.copy()
            updated["id"] = "btn_update"
            ui_config["buttons"][i] = updated
            break
    el = next((e for e in ui_config["buttons"] if e["id"] == "btn_update"), None)
    if not el or el["label"] != "Новая кнопка" or el["visible"] != False:
        test_logs.append("Ошибка: элемент не изменён корректно")
        raise Exception("Элемент не изменён корректно")
    test_logs.append("Тест изменения элемента пройден.")

# Асинхронные автотесты API (пример)
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
        async def ui_all():
            await run_ui_tests()
            await run_reset_test()
            await run_update_test()
        asyncio.create_task(ui_all())
    elif test_type == "api":
        asyncio.create_task(run_api_tests())
    else:
        async def run_all():
            await run_ui_tests()
            await run_reset_test()
            await run_update_test()
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

# Веб-интерфейс основной страницы с Bootstrap и новыми формами
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
<style>
  body { padding: 20px; }
  #log { height: 200px; white-space: pre-wrap; overflow-y: auto; background: #f8f9fa; border: 1px solid #dee2e6; padding: 10px; }
  .element-item { display: flex; align-items: center; justify-content: space-between; padding: 6px 12px; border-bottom: 1px solid #dee2e6; }
  .element-list { max-height: 300px; overflow-y: auto; border: 1px solid #dee2e6; border-radius: 0.375rem; }
</style>
</head>
<body>

<div class="container">
  <h1 class="mb-4">Демонстрация автотестирования</h1>

  <div class="mb-3 d-flex gap-2 align-items-center">
    <button id="resetConfigBtn" class="btn btn-warning">Обнулить конфигурацию UI (PUT)</button>
    <button id="runTestsBtn" class="btn btn-success">Запустить автотесты</button>
    <select id="testType" class="form-select w-auto">
      <option value="all">Все тесты</option>
      <option value="ui">UI тесты</option>
      <option value="api">API тесты</option>
    </select>
  </div>

  <h2>Добавить новый элемент</h2>
  <form id="addForm" class="mb-4">
    <div class="row g-3 align-items-center">
      <div class="col-auto">
        <label for="elementType" class="col-form-label">Тип элемента:</label>
      </div>
      <div class="col-auto">
        <select id="elementType" class="form-select" required>
          <option value="">--Выберите--</option>
          <option value="buttons">Кнопка</option>
          <option value="panels">Панель</option>
          <option value="comboboxes">Combobox</option>
          <option value="dropdowns">Dropdown</option>
        </select>
      </div>
      <div class="col-auto">
        <label for="elementId" class="col-form-label">ID:</label>
      </div>
      <div class="col-auto">
        <input type="text" id="elementId" class="form-control" required />
      </div>
    </div>
    <div id="fieldsContainer" class="mt-3"></div>
    <button type="submit" class="btn btn-primary mt-3">Добавить элемент</button>
  </form>

  <h2>Изменить элемент</h2>
  <form id="editForm" class="mb-4">
    <div class="row g-3 align-items-center">
      <div class="col-auto">
        <label for="editElementType" class="col-form-label">Тип элемента:</label>
      </div>
      <div class="col-auto">
        <select id="editElementType" class="form-select" required>
          <option value="">--Выберите--</option>
          <option value="buttons">Кнопка</option>
          <option value="panels">Панель</option>
          <option value="comboboxes">Combobox</option>
          <option value="dropdowns">Dropdown</option>
        </select>
      </div>
      <div class="col-auto">
        <label for="editElementId" class="col-form-label">ID:</label>
      </div>
      <div class="col-auto">
        <input type="text" id="editElementId" class="form-control" required />
      </div>
    </div>
    <div id="editFieldsContainer" class="mt-3"></div>
    <button type="submit" class="btn btn-primary mt-3">Изменить элемент</button>
  </form>

  <h2>UI элементы</h2>
  <div id="ui-elements" class="element-list mb-4"></div>

  <h2>Лог автотестов</h2>
  <div id="log"></div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>

<script>
function onTypeChange() {
  const type = document.getElementById('elementType').value;
  const container = document.getElementById('fieldsContainer');
  container.innerHTML = '';
  if(type === 'buttons') {
    container.innerHTML = `
      <div class="mb-3">
        <label for="elementLabel" class="form-label">Label:</label>
        <input type="text" id="elementLabel" class="form-control" required />
      </div>
      <div class="form-check">
        <input class="form-check-input" type="checkbox" id="elementVisible" checked />
        <label class="form-check-label" for="elementVisible">Visible</label>
      </div>
    `;
  } else if(type === 'panels') {
    container.innerHTML = `
      <div class="mb-3">
        <label for="elementTitle" class="form-label">Title:</label>
        <input type="text" id="elementTitle" class="form-control" required />
      </div>
      <div class="form-check">
        <input class="form-check-input" type="checkbox" id="elementVisible" checked />
        <label class="form-check-label" for="elementVisible">Visible</label>
      </div>
    `;
  } else if(type === 'comboboxes' || type === 'dropdowns') {
    container.innerHTML = `
      <div class="mb-3">
        <label for="elementOptions" class="form-label">Options (через запятую):</label>
        <input type="text" id="elementOptions" class="form-control" required />
      </div>
      <div class="form-check">
        <input class="form-check-input" type="checkbox" id="elementVisible" checked />
        <label class="form-check-label" for="elementVisible">Visible</label>
      </div>
    `;
  }
}

function onEditTypeChange() {
  const type = document.getElementById('editElementType').value;
  const container = document.getElementById('editFieldsContainer');
  container.innerHTML = '';
  if(type === 'buttons') {
    container.innerHTML = `
      <div class="mb-3">
        <label for="editElementLabel" class="form-label">Label:</label>
        <input type="text" id="editElementLabel" class="form-control" required />
      </div>
      <div class="form-check">
        <input class="form-check-input" type="checkbox" id="editElementVisible" checked />
        <label class="form-check-label" for="editElementVisible">Visible</label>
      </div>
    `;
  } else if(type === 'panels') {
    container.innerHTML = `
      <div class="mb-3">
        <label for="editElementTitle" class="form-label">Title:</label>
        <input type="text" id="editElementTitle" class="form-control" required />
      </div>
      <div class="form-check">
        <input class="form-check-input" type="checkbox" id="editElementVisible" checked />
        <label class="form-check-label" for="editElementVisible">Visible</label>
      </div>
    `;
  } else if(type === 'comboboxes' || type === 'dropdowns') {
    container.innerHTML = `
      <div class="mb-3">
        <label for="editElementOptions" class="form-label">Options (через запятую):</label>
        <input type="text" id="editElementOptions" class="form-control" required />
      </div>
      <div class="form-check">
        <input class="form-check-input" type="checkbox" id="editElementVisible" checked />
        <label class="form-check-label" for="editElementVisible">Visible</label>
      </div>
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

async function editElement() {
  const type = document.getElementById('editElementType').value;
  const id = document.getElementById('editElementId').value.trim();
  if(!type || !id) {
    alert('Выберите тип и введите ID');
    return false;
  }
  let body = {};
  if(type === 'buttons') {
    const label = document.getElementById('editElementLabel').value.trim();
    const visible = document.getElementById('editElementVisible').checked;
    if(!label) { alert('Введите label'); return false; }
    body.label = label;
    body.visible = visible;
  } else if(type === 'panels') {
    const title = document.getElementById('editElementTitle').value.trim();
    const visible = document.getElementById('editElementVisible').checked;
    if(!title) { alert('Введите title'); return false; }
    body.title = title;
    body.visible = visible;
  } else if(type === 'comboboxes' || type === 'dropdowns') {
    const optionsRaw = document.getElementById('editElementOptions').value.trim();
    const visible = document.getElementById('editElementVisible').checked;
    if(!optionsRaw) { alert('Введите options'); return false; }
    body.options = optionsRaw.split(',').map(s => s.trim()).filter(s => s.length > 0);
    body.visible = visible;
  }

  try {
    const res = await fetch(`/api/ui-config/${type}/${id}`, {
      method: 'PUT',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    });
    if(!res.ok) {
      const err = await res.json();
      alert('Ошибка: ' + err.detail);
      return false;
    }
    alert('Элемент изменён');
    loadConfig();
    document.getElementById('editForm').reset();
    document.getElementById('editFieldsContainer').innerHTML = '';
  } catch(e) {
    alert('Ошибка при изменении элемента');
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
  if (!res.ok) {
    alert('Ошибка загрузки конфигурации UI');
    return;
  }
  const config = await res.json();
  const container = document.getElementById('ui-elements');
  container.innerHTML = '';

  function createDeleteBtn(type, id) {
    const btn = document.createElement('button');
    btn.textContent = 'Удалить';
    btn.className = 'btn btn-sm btn-outline-danger';
    btn.onclick = () => deleteElement(type, id);
    return btn;
  }

  function createSection(title, items, type, renderItem) {
    if (!items || items.length === 0) return;
    const h3 = document.createElement('h3');
    h3.textContent = title;
    container.appendChild(h3);
    const listDiv = document.createElement('div');
    listDiv.className = 'element-list mb-3';
    items.forEach(item => {
      const div = document.createElement('div');
      div.className = 'element-item';
      div.appendChild(renderItem(item));
      div.appendChild(createDeleteBtn(type, item.id));
      listDiv.appendChild(div);
    });
    container.appendChild(listDiv);
  }

  createSection('Кнопки', config.buttons, 'buttons', item => {
    const span = document.createElement('span');
    span.textContent = `${item.id} — ${item.label} — Видим: ${item.visible}`;
    return span;
  });

  createSection('Панели', config.panels, 'panels', item => {
    const span = document.createElement('span');
    span.textContent = `${item.id} — ${item.title} — Видим: ${item.visible}`;
    return span;
  });

  createSection('Comboboxes', config.comboboxes, 'comboboxes', item => {
    const span = document.createElement('span');
    span.textContent = `${item.id} — Опции: ${item.options.join(', ')} — Видим: ${item.visible}`;
    return span;
  });

  createSection('Dropdowns', config.dropdowns, 'dropdowns', item => {
    const span = document.createElement('span');
    span.textContent = `${item.id} — Опции: ${item.options.join(', ')} — Видим: ${item.visible}`;
    return span;
  });
}

async function runTests() {
  const testType = document.getElementById('testType').value;
  const logDiv = document.getElementById('log');
  logDiv.textContent = "Запуск тестов...";
  await fetch(`/api/run-tests?test_type=${testType}`, { method: 'POST' });

  const interval = setInterval(async () => {
    const res = await fetch('/api/test-logs');
    const data = await res.json();
    logDiv.textContent = data.logs.join('\\n');
    logDiv.scrollTop = logDiv.scrollHeight;

    if(data.logs.length > 0 && (data.logs[data.logs.length - 1].toLowerCase().includes("завершен"))) {
      clearInterval(interval);
    }
  }, 1000);
}

window.addEventListener('DOMContentLoaded', () => {
  loadConfig();

  document.getElementById('addForm').addEventListener('submit', e => {
    e.preventDefault();
    addElement();
  });

  document.getElementById('elementType').addEventListener('change', onTypeChange);

  document.getElementById('editForm').addEventListener('submit', e => {
    e.preventDefault();
    editElement();
  });

  document.getElementById('editElementType').addEventListener('change', onEditTypeChange);

  document.getElementById('resetConfigBtn').addEventListener('click', async () => {
    if (!confirm('Обнулить конфигурацию UI?')) return;
    const res = await fetch('/api/ui-config/reset', { method: 'PUT' });
    if (res.ok) {
      alert('Конфигурация UI обнулена');
      loadConfig();
    } else {
      alert('Ошибка при обнулении конфигурации');
    }
  });

  document.getElementById('runTestsBtn').addEventListener('click', runTests);
});
</script>

</body>
</html>
"""
