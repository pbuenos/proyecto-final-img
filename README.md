# Analizador de hojas

Aplicacion web para analizar fotos de hojas y una interfaz de linea de comandos para procesar imagenes locales. Usa Pillow para abrir/guardar archivos y OpenCV/NumPy para segmentar y medir.

## Requisitos

- Python 3.10 o superior
- Pillow, OpenCV, NumPy, FastAPI y Uvicorn (instalables desde `requirements.txt`)

## Instalacion y uso web

Desde la carpeta `tp-final-analizador-hojas`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py --web
```

Abrir <http://127.0.0.1:8000>. La documentacion de la API esta en <http://127.0.0.1:8000/docs>. Para cambiar el puerto, usar `python main.py --web --port 8765`.

## Uso por consola

En modo consola, la ruta de imagen es obligatoria. Se pueden indicar varias:

```powershell
python main.py fotos\hoja1.jpg fotos\hoja2.png
python main.py fotos\hoja1.jpg --salida resultados --hue-min 25 --hue-max 100 --kernel-size 5
python main.py --help
```

Cada imagen genera una subcarpeta en `resultados/`, con archivos como `hoja1_mascara_hsv.png`, `hoja1_mascara_limpia.png`, `hoja1_contorno.png` y `hoja1_hoja_aislada.png`. El directorio `backend/storage/results/` contiene las salidas de la aplicacion web.

## Tecnicas y efecto

1. **Conversion RGB a HSV y mascara por color:** separar tono, saturacion y brillo permite seleccionar los tonos verdes mediante rangos ajustables. Los valores iniciales sirven como punto de partida, no como detector universal.
2. **Apertura y cierre morfologicos:** la apertura elimina manchas pequenas y el cierre rellena huecos pequenos; el kernel controla la intensidad de ambas operaciones.
3. **Contornos externos:** se elige la region mayor que supera un area minima. Se dibujan su contorno y caja delimitadora.
4. **Medicion geometrica:** se calculan area del contorno, perimetro, ancho, alto y proporcion ancho/alto. Son medidas en pixeles, no dimensiones fisicas.

Pillow se ocupa de decodificar, orientar segun EXIF, convertir a RGB y escribir los PNG. OpenCV realiza la conversion HSV, umbralizacion, morfologia y analisis de contornos.

## Limitaciones y pruebas recomendadas

El analisis inicial esta pensado para una hoja verde sobre un fondo simple que contraste y con iluminacion pareja. Un fondo verde puede confundirse con la hoja, y una hoja amarilla o seca puede quedar fuera del rango. Ajusta los controles HSV y compara las etapas; no interpretes pixeles como centimetros sin incluir una referencia de escala en la foto.

El proyecto incluye una imagen sintetica en `samples/` para verificar el flujo de forma reproducible. Para la presentacion, agreguen fotos propias de hojas con distintos fondos y comparen resultados. Las imagenes generadas se guardan en `results/` (CLI) o `backend/storage/results/` (web).

## Pruebas

```powershell
python -m pytest -q
```

## Integrantes

- Completar con los nombres del equipo.

## Conversaciones con IA

Guardar en `conversaciones_ia/` la exportacion completa de las conversaciones usadas para disenar y desarrollar el TP (con los prompts y las respuestas). No completar esta carpeta con una transcripcion parcial presentada como si fuera completa.
