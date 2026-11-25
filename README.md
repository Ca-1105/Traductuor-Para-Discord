# Traductor para Discord

Subtítulos en tiempo real de lo que escuchas en Discord (o cualquier llamada) en inglés ↔ español. Captura solo el audio de salida del sistema (WASAPI loopback): **no usa tu micrófono**. Detecta voces distintas y las etiqueta como `SPEAKER 1`, `SPEAKER 2`, etc.

Real-time subtitles for what you hear in Discord (or any call), English ↔ Spanish. It only captures system output audio (WASAPI loopback): **your microphone is never used**. It distinguishes speakers and labels them `SPEAKER 1`, `SPEAKER 2`, etc.

## Características / Features

- Transcripción local con [faster-whisper](https://github.com/SYSTRAN/faster-whisper) y traducción con Argos Translate (sin APIs de pago). Detecta el idioma entrante y traduce al destino elegido: español, inglés, francés, portugués, ruso, italiano, chino (Taiwán) o alemán; se descartan repeticiones alucinadas como "mainstream mainstream...".
- Identificación de hablantes con SpeechBrain ECAPA.
- Ventana siempre arriba, sin barra del sistema (fondo oscuro continuo), centrada en la parte superior, con la traducción, el texto original y la etiqueta del hablante. Se arrastra desde el encabezado y se redimensiona desde los bordes; `⊡` alterna modo compacto, `−` la minimiza (se recupera desde la barra de tareas) y `×` la cierra.
- Control de transparencia: casilla "Transparente" y deslizador de opacidad (10%–100%). Solo afecta al fondo; el texto se mantiene nítido y opaco. "⌖ Centrar" está junto al resto de botones de la fila de controles.
- Interfaz oscura rediseñada con tarjetas, colores por hablante e indicador de estado.
- Modos destino: español, inglés, francés, portugués, ruso, italiano, chino (Taiwán) y alemán. Auto mantiene la detección inglés ↔ español como antes.

## Requisitos / Requirements

- Windows 10/11.
- Python 3.12 con **"Add python.exe to PATH"** marcado en la instalación.
- Conexión a internet la primera vez (dependencias y modelos; los idiomas nuevos descargan paquetes adicionales).

## Instalación / Installation

```bat
instalar.bat
run.bat
```

El primer comando crea `.venv`, instala `requirements.txt` y descarga los modelos; el segundo inicia la aplicación. Todo el procesamiento es local después de eso.

## Uso / Usage

1. Entra a un canal de voz en Discord.
2. Comprueba que el audio salga por el dispositivo capturado (por defecto, el altavoz de Windows).
3. Usa los botones de la ventana para elegir destino (Español / English / Francés / Portugués / Ruso / Italiano / Taiwanés / Alemán / Auto), pausar (⏸/▶), limpiar (🗑), reiniciar voces (↺), centrar (⌖), ajustar "Transparente" / "Opacidad" o alternar modo compacto con `⊡`; redimensiona desde los bordes. `−` minimiza y `×` cierra. La ventana se mantiene siempre arriba automáticamente.

Opciones / CLI options:

```bat
run.bat --list-devices
run.bat --speaker "LG TV"
run.bat --model small
```

Si no aparecen subtítulos, ejecuta `--list-devices` y selecciona la salida correcta con `--speaker`.

## Configuración / Configuration

Edita `config.py` para ajustar `SPEAKER_THRESHOLD` (separación de hablantes), `WHISPER_MODEL` (`tiny` = más rápido, `small` = más preciso), `SILENCE_FRAMES` / `MAX_UTTERANCE_SECONDS` (latencia de las frases), `SPEAKER_EMBED_SECONDS` y los valores de ventana (`WINDOW_WIDTH`, `WINDOW_HEIGHT`, `WINDOW_TOP_MARGIN`, `DEFAULT_OPACITY`, `TRANSPARENT_OPACITY`, `MIN_OPACITY`). Los modelos se cargan en segundo plano al abrir la ventana para que no haya que esperar antes de verla.

Guía detallada en ambos idiomas: [INSTRUCTIONS.md](INSTRUCTIONS.md).
