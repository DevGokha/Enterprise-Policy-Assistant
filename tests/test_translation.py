"""Tests for translation functionality (Hindi and Marathi)."""

from fastapi.testclient import TestClient
from app.main import app
from app.agent.llm import translate_text

client = TestClient(app)


def test_translate_text_function():
    """Verify translate_text helper function for Hindi and Marathi."""
    text = "You have 10 casual leaves remaining."
    
    # Test English returns original
    en_result = translate_text(text, "en")
    assert en_result == text
    
    # Test Hindi
    hi_result = translate_text(text, "hi")
    assert hi_result != ""
    assert isinstance(hi_result, str)
    
    # Test Marathi
    mr_result = translate_text(text, "mr")
    assert mr_result != ""
    assert isinstance(mr_result, str)


def test_translate_api_endpoint():
    """Verify POST /api/translate endpoint works as expected."""
    # Test Hindi translation
    res_hi = client.post("/api/translate", json={
        "text": "Your leave request has been submitted successfully.",
        "target_lang": "hi"
    })
    assert res_hi.status_code == 200
    data_hi = res_hi.json()
    assert "translated_text" in data_hi
    assert data_hi["target_lang"] == "hi"
    assert len(data_hi["translated_text"]) > 0

    # Test Marathi translation
    res_mr = client.post("/api/translate", json={
        "text": "Your leave request has been submitted successfully.",
        "target_lang": "mr"
    })
    assert res_mr.status_code == 200
    data_mr = res_mr.json()
    assert "translated_text" in data_mr
    assert data_mr["target_lang"] == "mr"
    assert len(data_mr["translated_text"]) > 0

    # Test empty text edge case
    res_empty = client.post("/api/translate", json={
        "text": "",
        "target_lang": "hi"
    })
    assert res_empty.status_code == 200
    assert res_empty.json()["translated_text"] == ""
