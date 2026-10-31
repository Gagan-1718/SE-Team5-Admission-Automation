from pathlib import Path


CONTROLLER = Path("static/js/choices.js").read_text(encoding="utf-8")


def test_controller_uses_all_choice_api_operations():
    assert "method: \"POST\"" in CONTROLLER
    assert "method: \"DELETE\"" in CONTROLLER
    assert "method: \"PUT\"" in CONTROLLER
    assert "orderedChoiceIds" in CONTROLLER
    assert "data-lock-url" in Path("templates/choices/index.html").read_text(encoding="utf-8")


def test_controller_has_accessible_reorder_and_lock_behaviour():
    assert "aria-label=\"Move " in CONTROLLER
    assert "aria-live=\"polite\"" in Path("templates/choices/index.html").read_text(encoding="utf-8")
    assert "showModal" in CONTROLLER
    assert "dialog.close" in CONTROLLER
    assert "state.choices = previous" in CONTROLLER


def test_controller_handles_lock_and_backend_failures_without_raw_errors():
    assert "payload.message" in CONTROLLER
    assert "Network error" in CONTROLLER
    assert "Choices locked on" in CONTROLLER
    assert "unlock" not in CONTROLLER.lower()
