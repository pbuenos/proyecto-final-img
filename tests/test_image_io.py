"""Pruebas de carga y guardado de imagenes."""

from pathlib import Path

import pytest
import numpy as np
from PIL import Image

from backend.leaflab.image_io import (
    InvalidImageError,
    load_image,
    safe_stem,
    save_stages,
)


def test_load_image_converts_to_rgb() -> None:
    """Normaliza imagenes de entrada al formato RGB usado por el pipeline."""
    image = Image.new("L", (20, 10), 120)
    from io import BytesIO

    buffer = BytesIO()
    image.save(buffer, format="PNG")

    loaded = load_image(buffer.getvalue())

    assert loaded.mode == "RGB"
    assert loaded.size == (20, 10)


def test_load_image_rejects_invalid_bytes() -> None:
    """Convierte errores de Pillow en una excepcion de entrada entendible."""
    with pytest.raises(InvalidImageError, match="imagen valida"):
        load_image(b"no es una imagen")


def test_safe_stem_removes_paths_and_unsafe_characters() -> None:
    """Impide que rutas o simbolos del nombre se filtren a los nombres de salida."""
    assert safe_stem(r"..\fotos\hoja verde!.jpg") == "hoja_verde"


def test_save_stages_creates_descriptive_png_files(tmp_path: Path) -> None:
    """Guarda cada etapa en PNG con un nombre que describe el procesamiento."""
    stages = {"mascara_hsv": np.zeros((4, 4), dtype=np.uint8)}

    saved = save_stages(stages, tmp_path, "prueba")

    assert saved == [tmp_path / "prueba_mascara_hsv.png"]
    assert Image.open(saved[0]).size == (4, 4)
