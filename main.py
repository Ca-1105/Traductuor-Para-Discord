from __future__ import annotations

import argparse
import queue
import threading
import time
from concurrent.futures import ThreadPoolExecutor

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


def main():
    args = parse_args()
    if args.list_devices:
        list_devices()
        return

    audio_queue = queue.Queue()
    ui_queue = queue.Queue()
    stop_event = threading.Event()
    state = State()
    ready = threading.Event()
    services = {}

    ui = TranslatorUI(ui_queue, stop_event, state)
    ui.status_var.set("Cargando modelos…")

    def startup():
        try:
            translator = Translator(args.model)
            translator.warmup()
            diarizer = SpeakerDiarizer()
            speaker = find_speaker(args.speaker)
        except Exception as exc:
            ui_queue.put(("error", f"Error al iniciar: {exc}"))
            return
        services["translator"] = translator
        services["diarizer"] = diarizer
        services["speaker"] = speaker
        ui_queue.put(("status", f"Escuchando Discord · salida: {speaker.name}"))
        ready.set()
        AudioCapture(speaker, audio_queue, ui_queue, stop_event, state).start()

    threading.Thread(target=startup, daemon=True, name="startup").start()

    def process_loop():
        with ThreadPoolExecutor(max_workers=2, thread_name_prefix="decode") as pool:
            while not stop_event.is_set():
                if not ready.wait(timeout=0.2):
                    continue
                try:
                    _, audio = audio_queue.get(timeout=0.2)
                except queue.Empty:
                    continue
                if state.paused:
                    continue
                # Guard: ensure startup() completed successfully before using services
                if not all(k in services for k in ("translator", "diarizer", "speaker")):
                    continue
                diarizer = services["diarizer"]
                if state.reset_speakers:
                    diarizer.reset()
                    state.reset_speakers = False
                    ui_queue.put(("status", "Voces reiniciadas"))
                started = time.perf_counter()
                try:
                    speaker_future = pool.submit(diarizer.identify, audio)
                    result = services["translator"].process(audio, state.target_language)
                    speaker = speaker_future.result()
                except Exception as exc:
                    ui_queue.put(("error", f"Error al procesar: {exc}"))
                    continue
                if result is None:
                    continue
                result["speaker"] = speaker
                result["latency"] = time.perf_counter() - started
                ui_queue.put(("message", result))

    threading.Thread(target=process_loop, daemon=True, name="translator").start()

    ui.run()
    stop_event.set()


if __name__ == "__main__":
    main()
