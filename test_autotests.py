import pytest
import httpx

BASE_URL = "http://localhost:8000"

@pytest.mark.asyncio
async def test_get_ui_config():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/api/ui-config")
        assert r.status_code == 200
        data = r.json()
        assert "buttons" in data

@pytest.mark.asyncio
async def test_add_and_delete_button():
    new_button = {"id": "pytest_btn", "label": "Pytest Button", "visible": True}
    async with httpx.AsyncClient() as client:
        # Добавляем кнопку
        r = await client.post(f"{BASE_URL}/api/ui-config/buttons", json=new_button)
        assert r.status_code == 200

        # Проверяем, что кнопка появилась
        r = await client.get(f"{BASE_URL}/api/ui-config")
        data = r.json()
        assert any(b["id"] == "pytest_btn" for b in data["buttons"])

        # Удаляем кнопку
        r = await client.delete(f"{BASE_URL}/api/ui-config/buttons/pytest_btn")
        assert r.status_code == 200

        # Проверяем, что кнопка удалена
        r = await client.get(f"{BASE_URL}/api/ui-config")
        data = r.json()
        assert not any(b["id"] == "pytest_btn" for b in data["buttons"])
