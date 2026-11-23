from __future__ import annotations

import argparse
import queue
import threading
import time

import config
from audio import AudioCapture, State, find_speaker, list_devices
from speaker import SpeakerDiarizer
from translator import Translator
from ui import TranslatorUI


def parse_args():
    parser = argparse.ArgumentParser(
        description="Traductor del audio que escuchas de Discord o llamadas (ingles <-> espanol)"
    )
    parser.add_argument("--speaker", help="Nombre o parte del nombre de la salida (loopback)")
    parser.add_argument("--model", default=config.WHISPER_MODEL, help="Modelo de faster-whisper")
    parser.add_argument("--list-devices", action="store_true", help="Listar salidas de audio y salir")
    return parser.parse_args()


def source_language(state):
    if state.target_language == "auto":
        return "auto"
    return "en" if state.target_language == "es" else "es"


def main():
    args = parse_args()
    if args.list_devices:
        list_devices()
        return

    print("Cargando modelos (la primera vez puede descargar archivos)...", flush=True)
    try:
        translator = Translator(args.model)
        diarizer = SpeakerDiarizer()
    except Exception as exc:
        print(f"Error al cargar modelos: {exc}")
        return

    try:
        speaker = find_speaker(args.speaker)
    except ValueError as exc:
        print(exc)
        list_devices()
        return

    audio_queue = queue.Queue()
    ui_queue = queue.Queue()
    stop_event = threading.Event()
    state = State()

    ui = TranslatorUI(ui_queue, stop_event, state)
    ui.status_var.set(f"Escuchando Discord · salida: {speaker.name}")

    def process_loop():
        while not stop_event.is_set():
            try:
                _, audio = audio_queue.get(timeout=0.2)
            except queue.Empty:
                continue
            if state.paused:
                continue
            if state.reset_speakers:
                diarizer.reset()
                state.reset_speakers = False
                ui_queue.put(("status", "Voces reiniciadas"))
            started = time.perf_counter()
            try:
                speaker = diarizer.identify(audio)
                result = translator.process(audio, source_language(state))
            except Exception as exc:
                ui_queue.put(("error", f"Error al procesar: {exc}"))
                continue
            if result is None:
                continue
            result["speaker"] = speaker
            result["latency"] = time.perf_counter() - started
            ui_queue.put(("message", result))

    threading.Thread(target=process_loop, daemon=True, name="translator").start()
    AudioCapture(speaker, audio_queue, ui_queue, stop_event, state).start()

    print("Traductor iniciado. Solo se traduce lo que escuchas; tu microfono no se captura.", flush=True)
    ui.run()
    stop_event.set()
    print("Traductor detenido.")


if __name__ == "__main__":
    main()
