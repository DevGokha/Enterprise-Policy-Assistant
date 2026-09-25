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


def test_get_document_pdf_endpoint():
    """Verify GET /api/documents/{filename} serves valid PDF files."""
    res = client.get("/api/documents/leave_policy.pdf")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert len(res.content) > 1000

    # Test non-existent file
    res_404 = client.get("/api/documents/non_existent_policy.pdf")
    assert res_404.status_code == 404


def test_streamlit_language_toggle():
    """Verify Streamlit UI switches Quick Prompts dynamically between EN, HI, and MR."""
    from streamlit.testing.v1 import AppTest
    from pathlib import Path
    app_path = Path(__file__).parent.parent / "streamlit_app.py"
    at = AppTest.from_file(str(app_path))
    at.run()

    # Initial state should be English
    assert at.session_state["app_language"] == "en"
    en_buttons = [b.label for b in at.button if b.key in ("qp_1", "qp_2", "qp_3", "qp_4")]
    assert "How many casual leaves allowed?" in en_buttons

    # Click Hindi button
    hi_btn = [b for b in at.button if b.key == "top_l_hi"][0]
    hi_btn.click().run()
    assert at.session_state["app_language"] == "hi"
    hi_buttons = [b.label for b in at.button if b.key in ("qp_1", "qp_2", "qp_3", "qp_4")]
    assert "कैजुअल लीव कितने मिलते हैं?" in hi_buttons

    # Click Marathi button
    mr_btn = [b for b in at.button if b.key == "top_l_mr"][0]
    mr_btn.click().run()
    assert at.session_state["app_language"] == "mr"
    mr_buttons = [b.label for b in at.button if b.key in ("qp_1", "qp_2", "qp_3", "qp_4")]
    assert "किती कॅज्युअल रजा मिळतात?" in mr_buttons
