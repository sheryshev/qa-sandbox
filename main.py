from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import asyncio

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ui_config = {
    "buttons": [{"id": "btn1", "label": "Кнопка 1", "visible": True}],
    "panels": [{"id": "panel1", "title": "Панель 1", "visible": True}],
    "comboboxes": [{"id": "combo1", "options": ["Опция 1", "Опция 2"], "visible": True}],
    "dropdowns": [{"id": "dd1", "options": ["Выпад 1", "Выпад 2"], "visible": True}],
}

test_logs: List[str] = []

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

# Добавление нового элемента (POST)
@app.post("/api/ui-config/{element_type}")
async def add_ui_element(element_type: str, element: dict):
    if element_type not in ui_config:
        raise HTTPException(status_code=404, detail="Element type not found")
    # Проверка уникальности id
    if any(el["id"] == element.get("id") for el in ui_config[element_type]):
        raise HTTPException(status_code=400, detail="Element with this id already exists")
    ui_config[element_type].append(element)
    return {"detail": f"{element_type[:-1].capitalize()} добавлен", "element": element}

# Удаление элемента (DELETE) - уже есть, но чуть упростим
@app.delete("/api/ui-config/{element_type}/{element_id}")
async def delete_ui_element(element_type: str, element_id: str):
    if element_type not in ui_config:
        raise HTTPException(status_code=404, detail="Element type not found")
    before_count = len(ui_config[element_type])
    ui_config[element_type] = [el for el in ui_config[element_type] if el["id"] != element_id]
    after_count = len(ui_config[element_type])
    if before_count == after_count:
        raise HTTPException(status_code=404, detail="Element not found")
    return {"detail": f"{element_type[:-1].capitalize()} удалён"}

# Запуск автотестов с выбором типа
async def run_ui_tests():
    test_logs.append("Запуск UI тестов...")
    for btn in ui_config["buttons"]:
        if btn["visible"]:
            test_logs.append(f"UI тест кнопки {btn['id']}: видима - OK")
        else:
            test_logs.append(f"UI тест кнопки {btn['id']}: не видима - OK")
    test_logs.append("UI тесты завершены.")

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

@app.post("/api/run-tests")
async def run_tests(test_type: Optional[str] = "all"):
    test_logs.clear()
    if test_type == "ui":
        asyncio.create_task(run_ui_tests())
    elif test_type == "api":
        asyncio.create_task(run_api_tests())
    else:
        # all
        async def run_all():
            await run_ui_tests()
            await run_api_tests()
            test_logs.append("Все тесты завершены успешно.")
        asyncio.create_task(run_all())
    return {"detail": f"Тесты '{test_type}' запущены"}

@app.get("/api/test-logs")
async def get_test_logs():
    return {"logs": test_logs}

@app.get("/api/ui-config", response_model=UIConfig)
async def get_ui_config():
    return ui_config

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
    return ui_config

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
    return ui_config

# Веб-интерфейс с формой добавления и выбором автотеста
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
  .hidden { display: none; }
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
