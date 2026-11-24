"""Pruebas unitarias del procesamiento de hojas."""

import numpy as np
import pytest
from PIL import Image, ImageDraw

from backend.leaflab.processor import (
    LeafAnalyzer,
    LeafNotFoundError,
    ProcessingOptions,
)


def make_leaf_image() -> Image.Image:
    """Crea una hoja verde sintetica sobre un fondo claro para pruebas.

    Returns:
        Imagen RGB determinista con una region verde suficientemente grande.
    """
    image = Image.new("RGB", (240, 180), (235, 230, 215))
    draw = ImageDraw.Draw(image)
    draw.ellipse((65, 35, 175, 145), fill=(40, 145, 55))
    draw.line((75, 135, 165, 45), fill=(220, 235, 210), width=4)
    return image


def test_pipeline_returns_named_stages_and_measurements() -> None:
    """Comprueba que se produzcan las etapas y medidas geometricas esperadas."""
    result = LeafAnalyzer().analyze(make_leaf_image())

    assert set(result.stages) == {
        "original",
        "mascara_hsv",
        "mascara_limpia",
        "contorno",
        "hoja_aislada",
    }
    assert result.measurements.area_px > 0
    assert result.measurements.perimeter_px > 0
    assert result.measurements.width_px > 0
    assert result.measurements.height_px > 0
    assert result.stages["mascara_limpia"].dtype == np.uint8


def test_pipeline_rejects_an_image_without_a_green_region() -> None:
    """Informa con un error claro cuando no se detecta una hoja suficiente."""
    image = Image.new("RGB", (160, 120), (180, 90, 35))

    with pytest.raises(LeafNotFoundError, match="No se detecto|demasiado pequena"):
        LeafAnalyzer().analyze(image)


@pytest.mark.parametrize(
    "options",
    [
        {"hue_min": 101, "hue_max": 100},
        {"kernel_size": 4},
        {"min_area_ratio": 1.0},
    ],
)
def test_options_reject_invalid_thresholds(options: dict[str, int | float]) -> None:
    """Evita aceptar combinaciones de umbrales o kernel sin sentido."""
    with pytest.raises(ValueError):
        ProcessingOptions(**options)
