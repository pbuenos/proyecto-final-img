"""Pruebas de los endpoints web del analizador."""

from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from backend.app import main as api


def image_bytes(is_leaf: bool = True) -> bytes:
    """Codifica una imagen PNG verde o una imagen sin region verde.

    Args:
        is_leaf: Si es verdadero, dibuja una region que debe detectarse.

    Returns:
        Contenido PNG adecuado para enviarlo a la API de pruebas.
    """
    image = Image.new("RGB", (240, 180), (235, 230, 215))
    if is_leaf:
        ImageDraw.Draw(image).ellipse((65, 35, 175, 145), fill=(40, 145, 55))
    else:
        image = Image.new("RGB", (240, 180), (180, 90, 35))
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def test_health_and_frontend_are_available() -> None:
    """Confirma que el estado de API y la pagina principal respondan."""
    client = TestClient(api.app)

    assert client.get("/api/health").json() == {"status": "ok"}
    assert "Herbario visual" in client.get("/").text


def test_analyze_upload_saves_named_stages(
    tmp_path: Path, monkeypatch
) -> None:
    """Devuelve las cinco etapas y guarda sus archivos PNG descriptivos."""
    monkeypatch.setattr(api, "RESULTS_DIR", tmp_path)
    client = TestClient(api.app)

    response = client.post(
        "/api/analyze",
        files=[
            ("files", ("hoja.png", image_bytes(), "image/png")),
            ("files", ("sin_hoja.png", image_bytes(False), "image/png")),
        ],
    )

    assert response.status_code == 200
    results = response.json()["results"]
    assert [result["status"] for result in results] == ["ok", "error"]
    result = results[0]
    assert result["status"] == "ok"
    assert result["measurements"]["area_px"] > 0
    assert [stage["key"] for stage in result["stages"]] == [
        "original",
        "mascara_hsv",
        "mascara_limpia",
        "contorno",
        "hoja_aislada",
    ]
    assert len(list(tmp_path.rglob("*.png"))) == 5


def test_analyze_reports_an_image_without_leaf() -> None:
    """Devuelve un error por archivo sin impedir la respuesta de la API."""
    client = TestClient(api.app)

    response = client.post(
        "/api/analyze",
        files=[("files", ("sin_hoja.png", image_bytes(False), "image/png"))],
    )

    assert response.status_code == 200
    assert response.json()["results"][0]["status"] == "error"
    assert "No se detecto" in response.json()["results"][0]["error"]
