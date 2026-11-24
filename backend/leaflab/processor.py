"""Tecnicas de segmentacion y medicion de hojas con OpenCV."""

from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image


class LeafNotFoundError(ValueError):
    """Indica que no se encontro una region con el area minima esperada."""


@dataclass(frozen=True)
class ProcessingOptions:
    """Parametros para segmentar una hoja verde en el espacio HSV.

    Attributes:
        hue_min: Tono minimo de OpenCV, en el rango 0-179.
        hue_max: Tono maximo de OpenCV, en el rango 0-179.
        saturation_min: Saturacion minima, en el rango 0-255.
        value_min: Brillo minimo, en el rango 0-255.
        kernel_size: Lado impar del kernel usado para morfologia.
        min_area_ratio: Fraccion minima de area de contorno sobre la imagen.
    """

    hue_min: int = 25
    hue_max: int = 100
    saturation_min: int = 35
    value_min: int = 30
    kernel_size: int = 5
    min_area_ratio: float = 0.01

    def __post_init__(self) -> None:
        """Valida que los umbrales y el kernel esten dentro de sus rangos.

        Raises:
            ValueError: Si un umbral, el kernel o la fraccion de area no son validos.
        """
        if not 0 <= self.hue_min <= self.hue_max <= 179:
            raise ValueError("Los limites de tono deben cumplir 0 <= min <= max <= 179.")
        if not 0 <= self.saturation_min <= 255:
            raise ValueError("La saturacion minima debe estar entre 0 y 255.")
        if not 0 <= self.value_min <= 255:
            raise ValueError("El brillo minimo debe estar entre 0 y 255.")
        if self.kernel_size < 1 or self.kernel_size % 2 == 0:
            raise ValueError("El tamano del kernel debe ser un entero positivo impar.")
        if not 0 <= self.min_area_ratio < 1:
            raise ValueError("La fraccion minima de area debe estar entre 0 y 1.")


@dataclass(frozen=True)
class Measurements:
    """Medidas geometricas aproximadas del contorno detectado.

    Attributes:
        area_px: Area del contorno en pixeles cuadrados.
        perimeter_px: Longitud del contorno en pixeles.
        width_px: Ancho de la caja delimitadora en pixeles.
        height_px: Alto de la caja delimitadora en pixeles.
        aspect_ratio: Cociente entre ancho y alto de la caja delimitadora.
        area_ratio: Fraccion del area total ocupada por el contorno.
    """

    area_px: float
    perimeter_px: float
    width_px: int
    height_px: int
    aspect_ratio: float
    area_ratio: float


@dataclass(frozen=True)
class AnalysisResult:
    """Resultados visuales y geometricos de procesar una imagen.

    Attributes:
        stages: Arreglos NumPy con las etapas del procesamiento.
        measurements: Medidas aproximadas de la hoja mas grande.
    """

    stages: dict[str, np.ndarray]
    measurements: Measurements


class LeafAnalyzer:
    """Aplica segmentacion HSV, morfologia y medicion de contornos.

    Attributes:
        options: Umbrales de color y parametros de limpieza del analisis.
    """

    def __init__(self, options: ProcessingOptions | None = None) -> None:
        """Inicializa el analizador con opciones por defecto o personalizadas.

        Args:
            options: Umbrales y parametros; si se omite, se usan valores por defecto.
        """
        self.options = options or ProcessingOptions()

    def analyze(self, image: Image.Image) -> AnalysisResult:
        """Procesa una imagen RGB y calcula las medidas de su mayor hoja.

        Args:
            image: Imagen Pillow que contiene una hoja sobre un fondo contrastante.

        Returns:
            Etapas intermedias y mediciones de la region detectada.

        Raises:
            LeafNotFoundError: Si no hay contorno suficientemente grande.
        """
        rgb_image = np.asarray(image.convert("RGB"))
        hsv_image = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2HSV)
        mask = self._create_hsv_mask(hsv_image)
        cleaned_mask = self._clean_mask(mask)
        contour = self._find_leaf_contour(cleaned_mask)
        measurements = self._measure(contour, cleaned_mask.shape)
        contour_image = self._draw_contour(rgb_image, contour)
        isolated = cv2.bitwise_and(rgb_image, rgb_image, mask=cleaned_mask)
        isolated[cleaned_mask == 0] = (255, 255, 255)
        return AnalysisResult(
            stages={
                "original": rgb_image,
                "mascara_hsv": mask,
                "mascara_limpia": cleaned_mask,
                "contorno": contour_image,
                "hoja_aislada": isolated,
            },
            measurements=measurements,
        )

    def _create_hsv_mask(self, hsv_image: np.ndarray) -> np.ndarray:
        """Genera una mascara binaria a partir de los umbrales HSV configurados.

        Args:
            hsv_image: Imagen convertida al espacio HSV de OpenCV.

        Returns:
            Mascara uint8 con pixeles que cumplen tono, saturacion y brillo.
        """
        lower = np.array(
            [
                self.options.hue_min,
                self.options.saturation_min,
                self.options.value_min,
            ],
            dtype=np.uint8,
        )
        upper = np.array([self.options.hue_max, 255, 255], dtype=np.uint8)
        return cv2.inRange(hsv_image, lower, upper)

    def _clean_mask(self, mask: np.ndarray) -> np.ndarray:
        """Elimina puntos aislados y cierra huecos pequenos con morfologia.

        Args:
            mask: Mascara binaria uint8 generada por el umbral HSV.

        Returns:
            Mascara binaria despues de apertura y cierre morfologicos.
        """
        kernel = np.ones(
            (self.options.kernel_size, self.options.kernel_size), dtype=np.uint8
        )
        opened = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        return cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)

    def _find_leaf_contour(self, mask: np.ndarray) -> np.ndarray:
        """Selecciona el contorno externo de mayor area que supere el minimo.

        Args:
            mask: Mascara binaria limpia.

        Returns:
            Contorno de la region mas grande, como arreglo de puntos OpenCV.

        Raises:
            LeafNotFoundError: Si no hay una region que supere el area minima.
        """
        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        if not contours:
            raise LeafNotFoundError(
                "No se detecto una hoja: revisa los umbrales HSV y el fondo."
            )
        largest = max(contours, key=cv2.contourArea)
        image_area = mask.shape[0] * mask.shape[1]
        if cv2.contourArea(largest) < image_area * self.options.min_area_ratio:
            raise LeafNotFoundError(
                "La region detectada es demasiado pequena; revisa HSV o area minima."
            )
        return largest

    def _measure(
        self, contour: np.ndarray, image_shape: tuple[int, ...]
    ) -> Measurements:
        """Calcula area, perimetro y proporcion de la caja del contorno.

        Args:
            contour: Contorno externo seleccionado.
            image_shape: Forma alto-ancho de la imagen que contiene el contorno.

        Returns:
            Medidas geometricas aproximadas en pixeles y fraccion de imagen.
        """
        area = float(cv2.contourArea(contour))
        perimeter = float(cv2.arcLength(contour, True))
        _, _, width, height = cv2.boundingRect(contour)
        total_pixels = image_shape[0] * image_shape[1]
        return Measurements(
            area_px=area,
            perimeter_px=perimeter,
            width_px=width,
            height_px=height,
            aspect_ratio=width / height,
            area_ratio=area / total_pixels,
        )

    def _draw_contour(self, image: np.ndarray, contour: np.ndarray) -> np.ndarray:
        """Dibuja el contorno y su caja delimitadora sobre una copia RGB.

        Args:
            image: Imagen RGB original.
            contour: Contorno de la hoja detectada.

        Returns:
            Copia RGB con el contorno verde y la caja azul dibujados.
        """
        result = image.copy()
        cv2.drawContours(result, [contour], -1, (20, 120, 35), 3)
        x, y, width, height = cv2.boundingRect(contour)
        cv2.rectangle(result, (x, y), (x + width, y + height), (30, 90, 220), 2)
        return result
