import pytest
from main import ui_config, run_ui_tests

@pytest.mark.asyncio
async def test_reset_config():
    # Обнуляем конфигурацию
    ui_config["buttons"].clear()
    ui_config["panels"].clear()
    ui_config["comboboxes"].clear()
    ui_config["dropdowns"].clear()
    # Проверяем, что пусто
    total = sum(len(ui_config[key]) for key in ui_config)
    assert total == 0, "Конфигурация не пуста после обнуления"

@pytest.mark.asyncio
async def test_update_element():
    # Добавляем кнопку
    ui_config["buttons"].append({"id": "btn_test", "label": "Старая", "visible": True})
    # Изменяем кнопку
    for i, el in enumerate(ui_config["buttons"]):
        if el["id"] == "btn_test":
            ui_config["buttons"][i] = {"id": "btn_test", "label": "Новая", "visible": False}
            break
    # Проверяем изменения
    el = next((e for e in ui_config["buttons"] if e["id"] == "btn_test"), None)
    assert el is not None
    assert el["label"] == "Новая"
    assert el["visible"] is False

@pytest.mark.asyncio
async def test_ui_tests_run():
    # Добавим видимый элемент
    ui_config["buttons"] = [{"id": "btn1", "label": "Кнопка", "visible": True}]
    await run_ui_tests()
