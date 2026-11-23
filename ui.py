from __future__ import annotations

import queue
import time
import tkinter as tk
from tkinter import ttk

import config

LANGUAGE_LABELS = {"es": "Español", "en": "English", "auto": "Auto (detectar)"}
LANGUAGE_CODES = {label: code for code, label in LANGUAGE_LABELS.items()}


class TranslatorUI:
    def __init__(self, ui_queue, stop_event, state):
        self.ui_queue = ui_queue
        self.stop_event = stop_event
        self.state = state
        self.root = tk.Tk()
        self.root.title("Traductor de Discord")
        self.root.geometry("860x520")
        self.root.minsize(560, 320)
        self.root.configure(bg="#11141b")
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.95)
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        self._build()
        self.root.after(config.POLL_INTERVAL_MS, self._poll)

    def _build(self):
        header = tk.Frame(self.root, bg="#11141b", padx=12, pady=10)
        header.pack(fill="x")

        tk.Label(
            header,
            text="TRADUCTOR DE DISCORD",
            fg="#e8edf7",
            bg="#11141b",
            font=("Segoe UI", 13, "bold"),
        ).pack(side="left")

        tk.Label(header, text="Traducir a:", fg="#9aa5b8", bg="#11141b", font=("Segoe UI", 10)).pack(
            side="left", padx=(24, 6)
        )
        self.language_combo = ttk.Combobox(
            header,
            values=[LANGUAGE_LABELS[code] for code in ("es", "en", "auto")],
            state="readonly",
            width=16,
        )
        self.language_combo.set(LANGUAGE_LABELS[self.state.target_language])
        self.language_combo.bind("<<ComboboxSelected>>", self._on_language_change)
        self.language_combo.pack(side="left")

        self.pause_button = ttk.Button(header, text="Pausar", command=self._toggle_pause, width=9)
        self.pause_button.pack(side="left", padx=(12, 0))
        ttk.Button(header, text="Limpiar", command=self._clear, width=9).pack(side="left", padx=(6, 0))
        ttk.Button(header, text="Reiniciar voces", command=self._reset_speakers, width=15).pack(side="left", padx=(6, 0))

        self.topmost_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            header,
            text="Siempre arriba",
            variable=self.topmost_var,
            command=self._toggle_topmost,
            fg="#9aa5b8",
            bg="#11141b",
            activebackground="#11141b",
            selectcolor="#1b2030",
            relief="flat",
            font=("Segoe UI", 10),
        ).pack(side="left", padx=(12, 0))

        pane = tk.Frame(self.root, bg="#161a23", padx=10, pady=8)
        pane.pack(fill="both", expand=True, padx=10, pady=(0, 6))
        self.caption = tk.Label(
            pane, text="", fg="#ffb45a", bg="#161a23", font=("Segoe UI", 11, "bold"), anchor="w"
        )
        self.caption.pack(fill="x", pady=(0, 6))

        body = tk.Frame(pane, bg="#161a23")
        body.pack(fill="both", expand=True)
        self.text = tk.Text(
            body,
            wrap="word",
            bg="#0d1016",
            fg="#f2f4f8",
            insertbackground="#f2f4f8",
            relief="flat",
            borderwidth=6,
            font=("Segoe UI", 13),
            spacing1=2,
            spacing3=2,
        )
        scrollbar = ttk.Scrollbar(body, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.text.pack(side="left", fill="both", expand=True)

        self.text.tag_configure("time", foreground="#586174", font=("Segoe UI", 9))
        self.text.tag_configure("translated", foreground="#f4f8ff", font=("Segoe UI", 15, "bold"))
        self.text.tag_configure("original", foreground="#8b95a7", font=("Segoe UI", 11, "italic"))
        for index, color in enumerate(("5ab0ff", "ffb45a", "67d68c", "c792ff", "ff7b9c", "f2d45a"), start=1):
            self.text.tag_configure(f"speaker_{index}", foreground=f"#{color}", font=("Segoe UI", 11, "bold"))
        self.text.configure(state="disabled")

        footer = tk.Frame(self.root, bg="#0b0e14", padx=12, pady=6)
        footer.pack(fill="x", side="bottom")
        self.status_var = tk.StringVar(value="Iniciando…")
        tk.Label(footer, textvariable=self.status_var, bg="#0b0e14", fg="#9aa5b8", font=("Segoe UI", 10), anchor="w").pack(side="left")
        self.latency_var = tk.StringVar(value="")
        tk.Label(footer, textvariable=self.latency_var, bg="#0b0e14", fg="#6b7280", font=("Segoe UI", 10), anchor="e").pack(side="right")

        self._update_caption()

    def _update_caption(self):
        language = self.state.target_language
        if language == "es":
            self.caption.configure(text="DISCORD — escuchas inglés · ves español")
        elif language == "en":
            self.caption.configure(text="DISCORD — escuchas español · ves inglés")
        else:
            self.caption.configure(text="DISCORD — idioma detectado automáticamente")

    def _on_language_change(self, _event):
        self.state.target_language = LANGUAGE_CODES[self.language_combo.get()]
        self._update_caption()
        self.status_var.set(f"Traducir a: {LANGUAGE_LABELS[self.state.target_language]}")

    def _toggle_pause(self):
        self.state.paused = not self.state.paused
        self.pause_button.configure(text="Reanudar" if self.state.paused else "Pausar")
        self.status_var.set("PAUSADO" if self.state.paused else "Escuchando Discord…")

    def _toggle_topmost(self):
        self.root.attributes("-topmost", self.topmost_var.get())

    def _clear(self):
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")

    def _reset_speakers(self):
        self.state.reset_speakers = True
        self.status_var.set("Reiniciando voces…")

    def _add_message(self, payload):
        speaker = payload.get("speaker", 1)
        tag = f"speaker_{((speaker - 1) % 6) + 1}"
        self.text.configure(state="normal")
        self.text.insert("end", f"{time.strftime('%H:%M:%S')}  ", "time")
        self.text.insert("end", f"SPEAKER {speaker}\n", tag)
        self.text.insert("end", payload["translated"] + "\n", "translated")
        self.text.insert("end", payload["original"] + "\n\n", "original")
        max_lines = config.MAX_HISTORY_ENTRIES * 4
        lines = int(self.text.index("end-1c").split(".")[0])
        if lines > max_lines:
            self.text.delete("1.0", f"{lines - max_lines}.0")
        self.text.configure(state="disabled")
        self.text.see("end")
        self.latency_var.set(f"ultima traduccion: {payload['latency']:.1f} s")

    def _poll(self):
        while True:
            try:
                event = self.ui_queue.get_nowait()
            except queue.Empty:
                break
            if event[0] == "message":
                self._add_message(event[1])
            elif event[0] == "error":
                self.status_var.set(event[1])
            elif event[0] == "status":
                self.status_var.set(event[1])
        self.root.after(config.POLL_INTERVAL_MS, self._poll)

    def _close(self):
        self.stop_event.set()
        self.root.destroy()

    def run(self):
        self.root.mainloop()
