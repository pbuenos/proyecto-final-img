"""Punto de entrada para analizar imagenes desde la linea de comandos."""

import argparse
from pathlib import Path

from backend.leaflab.image_io import InvalidImageError, load_image, save_stages
from backend.leaflab.processor import (
    LeafAnalyzer,
    LeafNotFoundError,
    ProcessingOptions,
)


def build_parser() -> argparse.ArgumentParser:
    """Crea el analizador de argumentos de la interfaz de linea de comandos.

    Returns:
        Analizador con rutas de entrada y opciones de procesamiento.
    """
    parser = argparse.ArgumentParser(
        description="Aisla hojas verdes y calcula medidas aproximadas."
    )
    parser.add_argument(
        "imagenes",
        nargs="*",
        type=Path,
        help="una o mas rutas a imagenes de entrada",
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="inicia la aplicacion web en lugar de procesar imagenes por consola",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="direccion local del servidor web (por defecto: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="puerto del servidor web (por defecto: 8000)",
    )
    parser.add_argument(
        "--salida",
        type=Path,
        default=Path("resultados"),
        help="carpeta de salida (por defecto: ./resultados)",
    )
    parser.add_argument(
        "--hue-min",
        type=int,
        default=25,
        help="limite inferior de tono HSV, de 0 a 179 (por defecto: 25)",
    )
    parser.add_argument(
        "--hue-max",
        type=int,
        default=100,
        help="limite superior de tono HSV, de 0 a 179 (por defecto: 100)",
    )
    parser.add_argument(
        "--saturation-min",
        type=int,
        default=35,
        help="saturacion minima HSV, de 0 a 255 (por defecto: 35)",
    )
    parser.add_argument(
        "--value-min",
        type=int,
        default=30,
        help="brillo minimo HSV, de 0 a 255 (por defecto: 30)",
    )
    parser.add_argument(
        "--kernel-size",
        type=int,
        default=5,
        help="tamano impar del kernel morfologico (por defecto: 5)",
    )
    parser.add_argument(
        "--min-area-ratio",
        type=float,
        default=0.01,
        help="area minima de la hoja como fraccion de la imagen (por defecto: 0.01)",
    )
    return parser


def main() -> int:
    """Procesa las imagenes indicadas y guarda las etapas en disco.

    Returns:
        Codigo de salida: 0 si todas las imagenes se analizaron, 1 si alguna fallo.
    """
    parser = build_parser()
    args = parser.parse_args()
    if args.web:
        if args.imagenes:
            parser.error("No indiques rutas de imagen junto con --web.")
        import uvicorn

        from backend.app.main import app

        uvicorn.run(app, host=args.host, port=args.port)
        return 0
    if not args.imagenes:
        parser.error("Indica al menos una imagen o utiliza --web.")

    try:
        options = ProcessingOptions(
            hue_min=args.hue_min,
            hue_max=args.hue_max,
            saturation_min=args.saturation_min,
            value_min=args.value_min,
            kernel_size=args.kernel_size,
            min_area_ratio=args.min_area_ratio,
        )
    except ValueError as error:
        parser.error(str(error))

    analyzer = LeafAnalyzer(options)
    failures = 0
    for image_path in args.imagenes:
        try:
            image = load_image(image_path)
            result = analyzer.analyze(image)
            output_dir = args.salida / image_path.stem
            saved_files = save_stages(result.stages, output_dir, image_path.stem)
        except (OSError, InvalidImageError, LeafNotFoundError, ValueError) as error:
            print(f"Error en {image_path}: {error}")
            failures += 1
            continue

        measurements = result.measurements
        print(f"\n{image_path}:")
        print(f"  Area: {measurements.area_px:.0f} px^2")
        print(f"  Perimetro: {measurements.perimeter_px:.1f} px")
        print(
            f"  Ancho x alto: {measurements.width_px} x "
            f"{measurements.height_px} px"
        )
        print(f"  Proporcion ancho/alto: {measurements.aspect_ratio:.3f}")
        print(f"  Resultados: {output_dir.resolve()}")
        for saved_file in saved_files:
            print(f"    - {saved_file.name}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
