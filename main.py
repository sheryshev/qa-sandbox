from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse
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

DEFAULT_UI_CONFIG = {
    "buttons": [{"id": "btn1", "label": "Кнопка 1", "visible": True}],
    "panels": [{"id": "panel1", "title": "Панель 1", "visible": True}],
    "comboboxes": [{"id": "combo1", "options": ["Опция 1", "Опция 2"], "visible": True}],
    "dropdowns": [{"id": "dd1", "options": ["Выпад 1", "Выпад 2"], "visible": True}],
}

ui_config = {k: [dict(item) for item in v] for k, v in DEFAULT_UI_CONFIG.items()}

test_logs: List[str] = []
action_logs: List[str] = []
http_status_code = 200  # Глобальный HTTP код для тестов

class UIConfig(BaseModel):
    buttons: Optional[List[dict]] = None
    panels: Optional[List[dict]] = None
    comboboxes: Optional[List[dict]] = None
    dropdowns: Optional[List[dict]] = None

@app.get("/api/ui-config", response_model=UIConfig)
async def get_ui_config():
    return ui_config

@app.put("/api/ui-config/reset")
async def reset_ui_config():
    global ui_config
    ui_config = {k: [dict(item) for item in v] for k, v in DEFAULT_UI_CONFIG.items()}
    action_logs.append("Конфигурация UI обнулена до дефолтной")
    return {"detail": "Конфигурация UI обнулена"}

@app.put("/api/http-status")
async def set_http_status(code: int):
    global http_status_code
    if code < 100 or code > 599:
        raise HTTPException(status_code=400, detail="Некорректный HTTP код")
    http_status_code = code
    action_logs.append(f"HTTP код ответа изменён на {code}")
    return {"detail": f"HTTP код изменён на {code}"}

@app.get("/api/http-status")
async def get_http_status():
    return {"http_status": http_status_code}

@app.post("/api/ui-config/{element_type}")
async def add_ui_element(element_type: str, element: dict):
    if element_type not in ui_config:
        raise HTTPException(status_code=404, detail="Тип элемента не найден")
    if any(el["id"] == element.get("id") for el in ui_config[element_type]):
        raise HTTPException(status_code=400, detail="Элемент с таким id уже существует")
    ui_config[element_type].append(element)
    action_logs.append(f"Добавлен элемент {element_type[:-1]} с id={element.get('id')}")
    return {"detail": f"{element_type[:-1].capitalize()} добавлен", "element": element}

@app.put("/api/ui-config/{element_type}/{element_id}")
async def update_ui_element(element_type: str, element_id: str, element: dict):
    if element_type not in ui_config:
        raise HTTPException(status_code=404, detail="Тип элемента не найден")
    for i, el in enumerate(ui_config[element_type]):
        if el["id"] == element_id:
            updated = element.copy()
            updated["id"] = element_id
            ui_config[element_type][i] = updated
            action_logs.append(f"Элемент {element_type[:-1]} с id={element_id} обновлён")
            return {"detail": f"{element_type[:-1].capitalize()} обновлён", "element": updated}
    raise HTTPException(status_code=404, detail="Элемент не найден")

@app.delete("/api/ui-config/{element_type}/{element_id}")
async def delete_ui_element(element_type: str, element_id: str):
    if element_type not in ui_config:
        raise HTTPException(status_code=404, detail="Тип элемента не найден")
    before = len(ui_config[element_type])
    ui_config[element_type] = [el for el in ui_config[element_type] if el["id"] != element_id]
    after = len(ui_config[element_type])
    if before == after:
        raise HTTPException(status_code=404, detail="Элемент не найден")
    action_logs.append(f"Удалён элемент {element_type[:-1]} с id={element_id}")
    return {"detail": f"{element_type[:-1].capitalize()} удалён"}

@app.post("/api/run-tests")
async def run_tests():
    test_logs.clear()
    test_logs.append(f"Запуск автотестов с HTTP кодом {http_status_code}...")
    if http_status_code != 200:
        test_logs.append(f"Ошибка: HTTP код {http_status_code} не равен 200!")
        return {"detail": "Тесты завершены с ошибкой", "http_status": http_status_code}
    for etype in ["buttons", "panels", "comboboxes", "dropdowns"]:
        if not ui_config.get(etype):
            test_logs.append(f"Ошибка: отсутствуют элементы типа {etype}")
            return {"detail": f"Ошибка: отсутствуют элементы типа {etype}"}
        for el in ui_config[etype]:
            if not el.get("visible", False):
                test_logs.append(f"Ошибка: элемент {etype[:-1]} {el['id']} не видим")
                return {"detail": f"Ошибка: элемент {etype[:-1]} {el['id']} не видим"}
            test_logs.append(f"UI тест {etype[:-1]} {el['id']}: видим - OK")
    test_logs.append("Все тесты пройдены успешно.")
    return {"detail": "Тесты успешно завершены"}

@app.get("/api/test-logs")
async def get_test_logs():
    return {"logs": test_logs}

@app.get("/api/action-logs")
async def get_action_logs():
    return {"logs": action_logs}

@app.post("/api/ui-config/{element_type}", status_code=status.HTTP_201_CREATED)
async def add_ui_element(element_type: str, element: dict):
    if element_type not in ui_config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Element type not found")
    if any(el["id"] == element.get("id") for el in ui_config[element_type]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Element with this id already exists")
    ui_config[element_type].append(element)
    action_logs.append(f"Добавлен элемент {element_type[:-1]} с id={element.get('id')}")
    return {"detail": f"{element_type[:-1].capitalize()} добавлен", "element": element}

@app.delete("/api/ui-config/{element_type}/{element_id}", status_code=status.HTTP_200_OK)
async def delete_ui_element(element_type: str, element_id: str):
    if element_type not in ui_config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Element type not found")
    before_count = len(ui_config[element_type])
    ui_config[element_type] = [el for el in ui_config[element_type] if el["id"] != element_id]
    after_count = len(ui_config[element_type])
    if before_count == after_count:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Element not found")
    action_logs.append(f"Удалён элемент {element_type[:-1]} с id={element_id}")
    return {"detail": f"{element_type[:-1].capitalize()} удалён"}

@app.put("/api/ui-config/{element_type}/{element_id}", status_code=status.HTTP_200_OK)
async def update_ui_element(element_type: str, element_id: str, element: dict):
    if element_type not in ui_config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Element type not found")
    for i, el in enumerate(ui_config[element_type]):
        if el["id"] == element_id:
            updated = element.copy()
            updated["id"] = element_id
            ui_config[element_type][i] = updated
            action_logs.append(f"Элемент {element_type[:-1]} с id={element_id} обновлён")
            return {"detail": f"{element_type[:-1].capitalize()} обновлён", "element": updated}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Element not found")

@app.get("/logs", response_class=HTMLResponse)
async def logs_page():
    return """
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8" />
<title>Логи автотестов и действий</title>
<style>
  body { font-family: monospace; padding: 20px; }
  pre { background: #f0f0f0; padding: 10px; height: 300px; overflow-y: scroll; }
</style>
</head>
<body>
<h1>Логи действий</h1>
<pre id="actionLogs">Загрузка...</pre>
<h1>Логи автотестов</h1>
<pre id="testLogs">Загрузка...</pre>
<script>
async function updateLogs() {
  const resActions = await fetch('/api/action-logs');
  const dataActions = await resActions.json();
  document.getElementById('actionLogs').textContent = dataActions.logs.join('\\n');

  const resTests = await fetch('/api/test-logs');
  const dataTests = await resTests.json();
  document.getElementById('testLogs').textContent = dataTests.logs.join('\\n');
}
setInterval(updateLogs, 2000);
updateLogs();
</script>
</body>
</html>
"""
    
@app.post("/api/run-tests")
async def run_tests():
    test_logs.clear()
    test_logs.append(f"Запуск автотестов с HTTP кодом {http_status_code}...")
    if http_status_code != 200:
        test_logs.append(f"Ошибка: HTTP код {http_status_code} не равен 200!")
        return {"detail": "Тесты завершены с ошибкой", "http_status": http_status_code}
    for etype in ["buttons", "panels", "comboboxes", "dropdowns"]:
        if not ui_config.get(etype):
            test_logs.append(f"Ошибка: отсутствуют элементы типа {etype}")
            return {"detail": f"Ошибка: отсутствуют элементы типа {etype}"}
        for el in ui_config[etype]:
            if not el.get("visible", False):
                test_logs.append(f"Ошибка: элемент {etype[:-1]} {el['id']} не видим")
                return {"detail": f"Ошибка: элемент {etype[:-1]} {el['id']} не видим"}
            test_logs.append(f"UI тест {etype[:-1]} {el['id']}: видим - OK")
    test_logs.append("Все тесты пройдены успешно.")
    return {"detail": "Тесты успешно завершены"}

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

  <div class="mb-3 d-flex gap-2 align-items-center flex-wrap">
    <label for="httpStatus" class="form-label mb-0 me-2">HTTP код ответа:</label>
    <input type="number" id="httpStatus" class="form-control w-auto" value="200" min="100" max="599" />
    <button id="updateHttpStatus" class="btn btn-primary">Обновить HTTP код</button>
    <button id="resetConfigBtn" class="btn btn-warning ms-3">Обнулить конфигурацию UI</button>
    <button id="runTestsBtn" class="btn btn-success ms-auto">Запустить автотесты</button>
    <a href="/logs" class="btn btn-info ms-2">Перейти к логам</a>
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
      alert('Ошибка: ' + (err.detail || JSON.stringify(err)));
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
      alert('Ошибка: ' + (err.detail || JSON.stringify(err)));
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
    alert('Ошибка: ' + (err.detail || JSON.stringify(err)));
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
  const testType = document.getElementById('testType') ? document.getElementById('testType').value : 'all';
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

  document.getElementById('updateHttpStatus').addEventListener('click', async () => {
    const code = parseInt(document.getElementById('httpStatus').value);
    if (isNaN(code) || code < 100 || code > 599) {
      alert('Введите корректный HTTP код (100-599)');
      return;
    }
    const res = await fetch('/api/http-status?code=' + code, { method: 'PUT' });
    if (res.ok) {
      alert('HTTP код обновлён');
    } else {
      const err = await res.json();
      alert('Ошибка: ' + (err.detail || JSON.stringify(err)));
    }
  });

  document.getElementById('runTestsBtn').addEventListener('click', runTests);
});
</script>

</body>
</html>
"""
