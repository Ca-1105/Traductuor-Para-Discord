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
- **Traducir a:** Español / English / Francés / Portugués / Ruso / Italiano / Taiwanés / Alemán / Auto (detecta inglés ↔ español como antes).
- **⏸ Pausar / ▶ Reanudar:** detiene el procesamiento temporalmente.
- **🗑 Limpiar:** borra el historial de subtítulos.
- **↺ Voces:** vuelve a numerar los speakers desde 1.
- **Barra superior:** arrastra el encabezado para mover la ventana y los bordes para redimensionarla; `⊡` alterna modo compacto, `−` la minimiza (se recupera desde la barra de tareas) y `×` la cierra (no hay barra del sistema).
- **Siempre arriba:** la ventana se mantiene por encima de Discord automáticamente (no tiene botón; se reaplica solo).
- **Transparente / Opacidad:** hace translúcido solo el fondo; las letras siguen opacas. Usa el deslizador (10–100%) para ajustar cualquier nivel intermedio; también responde a las flechas del teclado cuando tiene el foco.
- **⌖ Centrar:** devuelve la ventana al centro de la parte superior (está junto a los demás botones en la fila de controles).

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
- `SILENCE_FRAMES` — controla cuánta pausa se necesita para cerrar una frase (16 = ~0,5 s).
- `MAX_UTTERANCE_SECONDS` — duración máxima de una frase antes de procesarla (12 s por defecto); bájalo para responder antes.
- `SPEAKER_EMBED_SECONDS` — segundos de audio usados para identificar al hablante (3 s).
- Los modelos se cargan en segundo plano al abrir la ventana y se calientan antes de la primera traducción.
- Los paquetes de los idiomas nuevos se instalan automáticamente la primera vez; las traducciones entre dos idiomas no ingleses pasan por inglés.

---

## English para Nash

### Requirements
- Windows 10/11.
- Python 3.12 (https://www.python.org/downloads/) with **"Add python.exe to PATH"** checked.
- Internet connection on first run (dependencies and models; the new languages download additional packages).

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
- **Traducir a (Translate to):** Spanish / English / French / Portuguese / Russian / Italian / Chinese (Taiwan) / German / Auto (keeps English ↔ Spanish detection).
- **⏸ Pausar / ▶ Reanudar (Pause / Resume):** temporarily stops processing.
- **🗑 Limpiar (Clear):** clears the subtitle history.
- **↺ Voces (Reset voices):** renumbers speakers from 1.
- **Barra superior (Title bar):** drag the header to move the window and the edges to resize it; `⊡` toggles compact mode, `−` minimizes it (restore from the taskbar) and `×` closes it (there is no system title bar).
- **Siempre arriba (Always on top):** the window stays above Discord automatically (no button; reapplied on its own).
- **Transparente / Opacidad (Transparency / Opacity):** makes only the background translucent; text stays opaque. Use the slider (10–100%) for any intermediate level; arrow keys also work when it has focus.
- **⌖ Centrar (Center at top):** moves the window back to the top center (it sits with the other buttons in the controls row).

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
- `SILENCE_FRAMES` — controls how much silence ends an utterance (16 = ~0.5 s).
- `MAX_UTTERANCE_SECONDS` — maximum utterance length before processing (12 s by default); lower it for faster responses.
- `SPEAKER_EMBED_SECONDS` — seconds of audio used to identify the speaker (3 s).
- Models load in the background when the window opens and are warmed up before the first translation.
- Packages for the new languages are installed automatically on the first run; translations between two non-English languages go through English.
