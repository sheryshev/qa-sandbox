import streamlit as st
import requests
import time
import os
from fastapi import FastAPI
import uvicorn
from threading import Thread
from playwright.sync_api import sync_playwright
from pydantic import BaseModel, Field, ValidationError
from typing import Dict

# --- 1. ВАЛИДАЦИЯ СХЕМЫ (CONTRACT TESTING) ---
class ButtonModel(BaseModel):
    id: str
    label: str = Field(min_length=1)
    visible: bool
    color: str

class ApiResponseModel(BaseModel):
    main_button: ButtonModel
    category_box: Dict

# --- 2. BACKEND СЕРВИС (FastAPI) ---
app = FastAPI()

if 'db' not in st.session_state:
    st.session_state.db = {
        "main_button": {"id": "main_button", "label": "Купить", "visible": True, "color": "blue"},
        "category_box": {"id": "category_box", "options": ["Техника", "Одежда"], "selected": "Техника"}
    }

@app.get("/items")
def get_items(): return st.session_state.db

@app.put("/items/{item_id}")
def update_item(item_id: str, data: dict):
    if item_id in st.session_state.db:
        st.session_state.db[item_id].update(data)
        return st.session_state.db[item_id]
    return {"error": "Not found"}

def run_api():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

if 'api_started' not in st.session_state:
    Thread(target=run_api, daemon=True).start()
    st.session_state.api_started = True

# --- 3. ИНТЕРФЕЙС (Streamlit) ---
st.set_page_config(page_title="QA Auto Sandbox", layout="wide")
st.title("🛠 QA Sandbox: Full-Stack Testing Dashboard")

col_admin, col_preview = st.columns(2)

with col_admin:
    st.header("⚙️ API Control (PUT)")
    new_label = st.text_input("Label", st.session_state.db["main_button"]["label"])
    is_visible = st.checkbox("Visible", st.session_state.db["main_button"]["visible"])
    
    if st.button("Update via REST"):
        requests.put(f"http://127.0.0.1", json={"label": new_label, "visible": is_visible})
        st.success("API State Updated")

with col_preview:
    st.header("🖥 UI Preview")
    if st.session_state.db["main_button"]["visible"]:
        st.button(st.session_state.db["main_button"]["label"], key="preview_btn", use_container_width=True)
    else:
        st.warning("Button is HIDDEN")

st.divider()

# --- 4. ПАНЕЛЬ АВТОТЕСТОВ ---
st.header("🚀 Test Runner (Playwright + Pydantic)")
test_btn = st.button("RUN SUITE", type="primary")

if test_btn:
    with st.spinner('Running Tests...'):
        log_content = f"[INFO] {time.strftime('%H:%M:%S')} - Start Session\n"
        
        # Шаг 1: Проверка API + Контракт Pydantic
        try:
            api_res = requests.get("http://127.0.0.1").json()
            valid_data = ApiResponseModel(**api_res)
            log_content += "[SUCCESS] API Schema Validation (Pydantic) PASSED\n"
        except ValidationError as e:
            st.error("Schema Error!")
            st.code(e.json())
            st.stop()

        # Шаг 2: UI Автоматизация
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                page.goto("http://localhost:8501", timeout=10000)
                time.sleep(2) # Ожидание рендеринга Streamlit
                
                shot_path = "report.png"
                page.screenshot(path=shot_path)
                
                btn_exists = page.get_by_text(valid_data.main_button.label).is_visible()
                expected = valid_data.main_button.visible
                
                log_content += f"[INFO] UI Search for '{valid_data.main_button.label}': Found={btn_exists}\n"
                
                if btn_exists == expected:
                    st.success("✅ TEST PASSED: UI matches API state")
                    st.image(shot_path, caption="Automated Screenshot")
                else:
                    st.error("❌ TEST FAILED: UI/API Mismatch")
                
                browser.close()
            except Exception as e:
                st.error(f"UI Test Error: {e}")
        
        st.subheader("📜 Execution Logs")
        st.code(log_content)
