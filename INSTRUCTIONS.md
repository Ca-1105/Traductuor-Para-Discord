# Traductor de Discord / Discord Translator

Subtítulos en tiempo real de lo que escuchas en Discord u otra llamada.
Solo captura el audio de salida (loopback WASAPI); **no usa tu micrófono**.
Detecta voces distintas y las etiqueta como SPEAKER 1, SPEAKER 2, etc.

Real-time subtitles for what you hear in Discord or any other call.
It only captures the output audio (WASAPI loopback); **your microphone is never used**.
It detects different voices and labels them SPEAKER 1, SPEAKER 2, etc.

---

## Español

### Requisitos
- Windows 10/11.
- Python 3.12 (https://www.python.org/downloads/) marcando **"Add python.exe to PATH"**.
- Conexión a internet la primera vez (descarga de dependencias y modelos, ~500 MB).

### Instalación
Copia esta carpeta completa **excepto** `.venv` y `__pycache__`, y ejecuta:

```
instalar.bat
```

Crea el entorno virtual, instala las librerías y descarga los modelos. Después ejecuta:

```
run.bat
```

### Uso
1. Inicia Discord y entra al canal de voz.
2. Asegúrate de que el audio de Discord salga por el dispositivo que se captura
   (por defecto, el altavoz de Windows).
3. Aparece una ventana siempre arriba con la traducción de cada frase,
   el texto original debajo y la etiqueta `SPEAKER n`.

Controles de la ventana:
- **Traducir a:** Español / English / Auto (detecta el idioma entrante).
- **Pausar / Reanudar:** detiene el procesamiento temporalmente.
- **Limpiar:** borra el historial de subtítulos.
- **Reiniciar voces:** vuelve a numerar los speakers desde 1.
- **Siempre arriba:** mantiene la ventana por encima de Discord.

### Opciones de línea de comandos
```
run.bat --list-devices              # lista las salidas disponibles
run.bat --speaker "LG TV"           # captura otro dispositivo de salida
run.bat --model small               # más preciso, más lento (tiny/base/small...)
```
Si no aparecen subtítulos, comprueba la salida de Discord con `--list-devices`
y selecciónala con `--speaker`.

### Ajustes
Edita `config.py`:
- `SPEAKER_THRESHOLD = 0.7` — bájalo (0.6) si una misma persona sale como varios
  speakers; súbelo (0.8) si personas distintas salen como una sola.
- `WHISPER_MODEL = "base"` — cambia a `tiny` para más velocidad o `small` para
  más precisión.
- `SILENCE_FRAMES` — controla cuánta pausa se necesita para cerrar una frase.

---

## English

### Requirements
- Windows 10/11.
- Python 3.12 (https://www.python.org/downloads/) with **"Add python.exe to PATH"** checked.
- Internet connection on first run (dependencies and models, ~500 MB).

### Installation
Copy this folder **except** `.venv` and `__pycache__`, then run:

```
instalar.bat
```

It creates the virtual environment, installs the libraries and downloads the models.
Then run:

```
run.bat
```

### Usage
1. Start Discord and join a voice channel.
2. Make sure Discord audio goes to the captured output device
   (the default Windows speaker unless changed).
3. A always-on-top window shows the translation of each utterance, the original
   text below it, and the `SPEAKER n` label.

Window controls:
- **Traducir a (Translate to):** Spanish / English / Auto (detects the incoming language).
- **Pausar / Reanudar (Pause / Resume):** temporarily stops processing.
- **Limpiar (Clear):** clears the subtitle history.
- **Reiniciar voces (Reset voices):** renumbers speakers from 1.
- **Siempre arriba (Always on top):** keeps the window above Discord.

### Command line options
```
run.bat --list-devices              # list available output devices
run.bat --speaker "LG TV"           # capture a different output device
run.bat --model small               # more accurate, slower (tiny/base/small...)
```
If no subtitles appear, check Discord's output device with `--list-devices`
and select it with `--speaker`.

### Tuning
Edit `config.py`:
- `SPEAKER_THRESHOLD = 0.7` — lower it (0.6) if one person is split into several
  speakers; raise it (0.8) if different people are merged into one.
- `WHISPER_MODEL = "base"` — use `tiny` for speed or `small` for accuracy.
- `SILENCE_FRAMES` — controls how much silence ends an utterance.
