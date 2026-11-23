# Traductor para Discord

Subtítulos en tiempo real de lo que escuchas en Discord (o cualquier llamada) en inglés ↔ español. Captura solo el audio de salida del sistema (WASAPI loopback): **no usa tu micrófono**. Detecta voces distintas y las etiqueta como `SPEAKER 1`, `SPEAKER 2`, etc.

Real-time subtitles for what you hear in Discord (or any call), English ↔ Spanish. It only captures system output audio (WASAPI loopback): **your microphone is never used**. It distinguishes speakers and labels them `SPEAKER 1`, `SPEAKER 2`, etc.

## Características / Features

- Transcripción local con [faster-whisper](https://github.com/SYSTRAN/faster-whisper) y traducción con Argos Translate (sin APIs de pago).
- Identificación de hablantes con SpeechBrain ECAPA.
- Ventana siempre arriba con la traducción, el texto original y la etiqueta del hablante.
- Modos: español, inglés o detección automática del idioma entrante.

## Requisitos / Requirements

- Windows 10/11.
- Python 3.12 con **"Add python.exe to PATH"** marcado en la instalación.
- Conexión a internet la primera vez (dependencias y modelos, ~500 MB).

## Instalación / Installation

```bat
instalar.bat
run.bat
```

El primer comando crea `.venv`, instala `requirements.txt` y descarga los modelos; el segundo inicia la aplicación. Todo el procesamiento es local después de eso.

## Uso / Usage

1. Entra a un canal de voz en Discord.
2. Comprueba que el audio salga por el dispositivo capturado (por defecto, el altavoz de Windows).
3. Usa los botones de la ventana para traducir a Español / English / Auto, pausar, limpiar el historial, reiniciar voces o activar "siempre arriba".

Opciones / CLI options:

```bat
run.bat --list-devices
run.bat --speaker "LG TV"
run.bat --model small
```

Si no aparecen subtítulos, ejecuta `--list-devices` y selecciona la salida correcta con `--speaker`.

## Configuración / Configuration

Edita `config.py` para ajustar `SPEAKER_THRESHOLD` (separación de hablantes), `WHISPER_MODEL` (`tiny` = más rápido, `small` = más preciso) y `SILENCE_FRAMES` (pausa que cierra una frase).

Guía detallada en ambos idiomas: [INSTRUCTIONS.md](INSTRUCTIONS.md).
