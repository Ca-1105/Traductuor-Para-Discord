from __future__ import annotations

import queue
import sys
import time
import tkinter as tk
from tkinter import ttk

import config

if sys.platform == "win32":
    import ctypes
    import ctypes.wintypes

LANGUAGE_LABELS = {"es": "Español", "en": "English", "auto": "Auto (detectar)"}
LANGUAGE_CODES = {label: code for code, label in LANGUAGE_LABELS.items()}

KEY_COLOR = "#0f1219"

COLORS = {
    "bg": "#0f1219",
    "panel": "#171c27",
    "panel_alt": "#121720",
    "text": "#eef2fb",
    "muted": "#9aa5b8",
    "accent": "#7aa2ff",
    "accent_hover": "#9dbcff",
    "warning": "#ffb45a",
    "danger": "#ff7b9c",
    "success": "#67d68c",
    "border": "#2a3142",
    "hover": "#242c3c",
}


class TranslatorUI:
    def __init__(self, ui_queue, stop_event, state):
        self.ui_queue = ui_queue
        self.stop_event = stop_event
        self.state = state
        self.root = tk.Tk()
        self.root.title("Traductor de Discord")
        self.root.minsize(560, 320)
        self.root.configure(bg=COLORS["bg"])
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)

        self.minimized = False
        self._minimizing = False
        self.opacity_var = tk.DoubleVar(value=config.DEFAULT_OPACITY)
        self.transparent_var = tk.BooleanVar(value=False)
        self.last_transparent_opacity = config.TRANSPARENT_OPACITY
        self.root.attributes("-alpha", 1.0)

        self._configure_styles()
        self._build()
        self.root.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}")
        self._center_top()
        self._create_glass()
        self._set_opacity(config.DEFAULT_OPACITY)
        self.root.bind("<Map>", self._reassert_topmost)
        self.root.bind("<Map>", self._on_restore, add="+")
        self.root.bind("<ButtonPress-1>", self._start_drag)
        self.root.bind("<B1-Motion>", self._do_drag)
        self.root.bind("<ButtonRelease-1>", self._stop_drag)
        self.root.after(50, self._center_top)
        self.root.after(200, self._reassert_topmost)
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        self.root.after(config.POLL_INTERVAL_MS, self._poll)

    def _configure_styles(self):
        self.style = ttk.Style()
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")

        self.style.configure("Header.TFrame", background=COLORS["bg"])
        self.style.configure("Card.TFrame", background=COLORS["border"])
        self.style.configure("Inner.TFrame", background=COLORS["panel"])
        self.style.configure("Footer.TFrame", background=COLORS["panel_alt"])

        self.style.configure(
            "TLabel",
            background=COLORS["bg"],
            foreground=COLORS["muted"],
            font=("Segoe UI", 10),
        )
        self.style.configure(
            "Title.TLabel",
            background=COLORS["bg"],
            foreground=COLORS["text"],
            font=("Segoe UI", 15, "bold"),
        )
        self.style.configure(
            "Subtitle.TLabel",
            background=COLORS["bg"],
            foreground="#6b768c",
            font=("Segoe UI", 9),
        )
        self.style.configure(
            "Badge.TLabel",
            background=COLORS["panel"],
            foreground=COLORS["accent"],
            font=("Segoe UI", 10, "bold"),
            padding=(10, 4),
        )
        self.style.configure(
            "Card.TLabel",
            background=COLORS["panel"],
            foreground=COLORS["warning"],
            font=("Segoe UI", 11, "bold"),
        )
        self.style.configure(
            "Footer.TLabel",
            background=COLORS["panel_alt"],
            foreground=COLORS["muted"],
            font=("Segoe UI", 10),
        )

        self.style.configure(
            "TButton",
            background=COLORS["panel"],
            foreground=COLORS["text"],
            bordercolor=COLORS["border"],
            lightcolor=COLORS["border"],
            darkcolor=COLORS["border"],
            relief="flat",
            padding=(10, 5),
            font=("Segoe UI", 10),
        )
        self.style.map(
            "TButton",
            background=[("active", COLORS["hover"])],
            bordercolor=[("active", COLORS["accent"])],
        )
        self.style.configure(
            "Accent.TButton",
            background=COLORS["accent"],
            foreground="#0c1220",
            bordercolor=COLORS["accent"],
            lightcolor=COLORS["accent"],
            darkcolor=COLORS["accent"],
            font=("Segoe UI", 10, "bold"),
        )
        self.style.map("Accent.TButton", background=[("active", COLORS["accent_hover"])])

        self.style.configure(
            "TCheckbutton",
            background=COLORS["bg"],
            foreground=COLORS["muted"],
            indicatorcolor=COLORS["panel"],
            indicatorforeground=COLORS["accent"],
            bordercolor=COLORS["border"],
            lightcolor=COLORS["border"],
            darkcolor=COLORS["border"],
            font=("Segoe UI", 10),
        )
        self.style.map(
            "TCheckbutton",
            background=[("active", COLORS["bg"])],
            foreground=[("active", COLORS["text"])],
        )

        self.style.configure(
            "TCombobox",
            fieldbackground=COLORS["panel"],
            background=COLORS["panel"],
            foreground=COLORS["text"],
            arrowcolor=COLORS["accent"],
            bordercolor=COLORS["border"],
            lightcolor=COLORS["border"],
            darkcolor=COLORS["border"],
            padding=4,
        )
        self.style.map(
            "TCombobox",
            fieldbackground=[("readonly", COLORS["panel"])],
            foreground=[("readonly", COLORS["text"])],
        )

        self.style.configure(
            "TScale",
            background=COLORS["panel"],
            troughcolor=COLORS["border"],
            bordercolor=COLORS["border"],
            lightcolor=COLORS["accent"],
            darkcolor=COLORS["border"],
        )

        self.style.configure(
            "Window.TButton",
            background=COLORS["bg"],
            foreground=COLORS["muted"],
            bordercolor=COLORS["bg"],
            lightcolor=COLORS["bg"],
            darkcolor=COLORS["bg"],
            padding=(7, 0),
            font=("Segoe UI", 11),
        )
        self.style.map(
            "Window.TButton",
            background=[("active", COLORS["hover"])],
            foreground=[("active", COLORS["text"])],
        )

    def _build(self):
        header = ttk.Frame(self.root, style="Header.TFrame", padding=(14, 10, 14, 4))
        header.pack(fill="x")

        title_row = ttk.Frame(header, style="Header.TFrame")
        title_row.pack(fill="x")

        self.drag_widgets = [header, title_row]

        ttk.Button(
            title_row, text="×", style="Window.TButton", command=self._close, width=3
        ).pack(side="right")
        ttk.Button(
            title_row, text="−", style="Window.TButton", command=self._minimize, width=3
        ).pack(side="right", padx=(0, 6))

        accent_bar = tk.Frame(title_row, bg=COLORS["accent"], width=4, height=22)
        accent_bar.pack(side="left", fill="y")
        accent_bar.pack_propagate(False)

        title_label = ttk.Label(title_row, text="TRADUCTOR DE DISCORD", style="Title.TLabel")
        title_label.pack(side="left", padx=(10, 0))
        subtitle_label = ttk.Label(
            title_row, text="subtítulos en tiempo real", style="Subtitle.TLabel"
        )
        subtitle_label.pack(side="left", padx=(10, 0))
        self.drag_widgets.extend([accent_bar, title_label, subtitle_label])

        self.direction_var = tk.StringVar(value="EN → ES")
        badge = ttk.Label(title_row, textvariable=self.direction_var, style="Badge.TLabel")
        badge.pack(side="right", padx=(0, 10))
        self.drag_widgets.append(badge)

        controls = ttk.Frame(header, style="Header.TFrame")
        controls.pack(fill="x", pady=(10, 0))

        ttk.Label(controls, text="Traducir a:").pack(side="left", padx=(0, 6))
        self.language_combo = ttk.Combobox(
            controls,
            values=[LANGUAGE_LABELS[code] for code in ("es", "en", "auto")],
            state="readonly",
            width=16,
        )
        self.language_combo.set(LANGUAGE_LABELS[self.state.target_language])
        self.language_combo.bind("<<ComboboxSelected>>", self._on_language_change)
        self.language_combo.pack(side="left")

        self.pause_button = ttk.Button(
            controls, text="Pausar", command=self._toggle_pause, width=9, style="Accent.TButton"
        )
        self.pause_button.pack(side="left", padx=(10, 0))
        ttk.Button(controls, text="Limpiar", command=self._clear, width=9).pack(side="left", padx=(6, 0))
        ttk.Button(controls, text="Reiniciar voces", command=self._reset_speakers, width=15).pack(
            side="left", padx=(6, 0)
        )
        ttk.Button(controls, text="Centrar arriba", command=self._center_top, width=15).pack(
            side="left", padx=(6, 0)
        )

        display = ttk.Frame(header, style="Header.TFrame")
        display.pack(fill="x", pady=(8, 2))

        toggles = ttk.Frame(display, style="Header.TFrame")
        toggles.pack(fill="x")

        ttk.Checkbutton(
            toggles,
            text="Transparente",
            variable=self.transparent_var,
            command=self._toggle_transparency,
        ).pack(side="left")

        opacity_row = ttk.Frame(display, style="Header.TFrame")
        opacity_row.pack(fill="x", pady=(6, 0))

        ttk.Label(opacity_row, text="Opacidad:").pack(side="left")
        self.opacity_scale = ttk.Scale(
            opacity_row,
            from_=config.MIN_OPACITY,
            to=1.0,
            value=config.DEFAULT_OPACITY,
            orient="horizontal",
            length=320,
            command=self._set_opacity,
        )
        self.opacity_scale.pack(side="left", padx=(6, 0))
        self.opacity_label = ttk.Label(
            opacity_row, text=f"{int(round(config.DEFAULT_OPACITY * 100))}%", width=5
        )
        self.opacity_label.pack(side="left", padx=(6, 0))

        card = ttk.Frame(self.root, style="Card.TFrame")
        card.pack(fill="both", expand=True, padx=12, pady=(8, 8))
        inner = ttk.Frame(card, style="Inner.TFrame")
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        caption_row = ttk.Frame(inner, style="Inner.TFrame")
        caption_row.pack(fill="x", padx=12, pady=(10, 4))
        caption_dot = tk.Frame(caption_row, bg=COLORS["warning"], width=7, height=7)
        caption_dot.pack(side="left")
        caption_dot.pack_propagate(False)
        self.caption = ttk.Label(caption_row, style="Card.TLabel")
        self.caption.pack(side="left", padx=(8, 0))

        text_frame = tk.Frame(inner, bg=COLORS["border"])
        text_frame.pack(fill="both", expand=True, padx=10, pady=(4, 10))
        self.text = tk.Text(
            text_frame,
            wrap="word",
            bg=COLORS["panel_alt"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            borderwidth=1,
            font=("Segoe UI", 13),
            spacing1=2,
            spacing3=3,
            padx=10,
            pady=8,
        )
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.text.pack(side="left", fill="both", expand=True)

        self.text.tag_configure("time", foreground="#5d687e", font=("Segoe UI", 9))
        self.text.tag_configure("translated", foreground="#f4f8ff", font=("Segoe UI", 15, "bold"))
        self.text.tag_configure("original", foreground="#8b95a7", font=("Segoe UI", 11, "italic"))
        for index, color in enumerate(
            ("5ab0ff", "ffb45a", "67d68c", "c792ff", "ff7b9c", "f2d45a"), start=1
        ):
            self.text.tag_configure(
                f"speaker_{index}", foreground=f"#{color}", font=("Segoe UI", 11, "bold")
            )
        self.text.configure(state="disabled")

        footer = ttk.Frame(self.root, style="Footer.TFrame", padding=(14, 6))
        footer.pack(fill="x", side="bottom")
        self.status_dot = tk.Canvas(
            footer, width=8, height=8, bg=COLORS["panel_alt"], highlightthickness=0
        )
        self.status_dot.create_oval(2, 2, 6, 6, fill=COLORS["accent"], outline="")
        self.status_dot.pack(side="left", padx=(0, 8))
        self.status_var = tk.StringVar(value="Iniciando…")
        self.status_var.trace_add("write", self._on_status_change)
        ttk.Label(footer, textvariable=self.status_var, style="Footer.TLabel", anchor="w").pack(
            side="left"
        )
        self.latency_var = tk.StringVar(value="")
        ttk.Label(footer, textvariable=self.latency_var, style="Footer.TLabel", anchor="e").pack(
            side="right"
        )

        self.tk_surfaces = [
            (text_frame, COLORS["border"]),
            (self.text, COLORS["panel_alt"]),
            (self.status_dot, COLORS["panel_alt"]),
        ]

        self._update_caption()

    def _center_top(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        if width <= 1:
            width = config.WINDOW_WIDTH
        if height <= 1:
            height = config.WINDOW_HEIGHT
        screen_width = self.root.winfo_screenwidth()
        x = max(0, (screen_width - width) // 2)
        self.root.geometry(f"{width}x{height}+{x}+{config.WINDOW_TOP_MARGIN}")

    def _start_drag(self, event):
        if event.widget not in self.drag_widgets:
            return
        self.drag_offset_x = event.x_root - self.root.winfo_x()
        self.drag_offset_y = event.y_root - self.root.winfo_y()

    def _do_drag(self, event):
        if not hasattr(self, "drag_offset_x"):
            return
        x = event.x_root - self.drag_offset_x
        y = event.y_root - self.drag_offset_y
        self.root.geometry(f"+{x}+{y}")

    def _stop_drag(self, _event=None):
        if hasattr(self, "drag_offset_x"):
            del self.drag_offset_x

    def _create_glass(self):
        self.glass = tk.Toplevel(self.root)
        self.glass.overrideredirect(True)
        self.glass.configure(bg=COLORS["bg"])
        self.glass.attributes("-topmost", True)
        self.glass.withdraw()
        self.glass.bind("<Button-1>", self._on_glass_click)
        self.glass.bind("<Map>", self._on_glass_map)
        self.root.bind("<Configure>", self._sync_glass)

    def _on_glass_click(self, _event=None):
        self.root.lift()
        self.root.focus_force()

    def _on_glass_map(self, _event=None):
        if self.transparent_var.get():
            self.glass.attributes("-alpha", self.opacity_var.get())
        self._sync_glass()
        self._reassert_topmost()

    def _client_origin(self):
        if sys.platform == "win32":
            point = ctypes.wintypes.POINT(0, 0)
            ctypes.windll.user32.ClientToScreen(
                ctypes.wintypes.HWND(int(self.root.frame(), 16)), ctypes.byref(point)
            )
            return point.x, point.y
        return self.root.winfo_rootx(), self.root.winfo_rooty()

    def _sync_glass(self, _event=None):
        glass = getattr(self, "glass", None)
        if glass is None or glass.state() != "normal":
            return
        x, y = self._client_origin()
        geometry = f"{self.root.winfo_width()}x{self.root.winfo_height()}+{x}+{y}"
        if glass.geometry() != geometry:
            glass.geometry(geometry)

    def _apply_surface_colors(self, transparent):
        surface = KEY_COLOR if transparent else COLORS["bg"]
        panel = KEY_COLOR if transparent else COLORS["panel"]
        panel_alt = KEY_COLOR if transparent else COLORS["panel_alt"]
        border = KEY_COLOR if transparent else COLORS["border"]

        self.style.configure("Header.TFrame", background=surface)
        self.style.configure("Card.TFrame", background=border)
        self.style.configure("Inner.TFrame", background=panel)
        self.style.configure("Footer.TFrame", background=panel_alt)
        self.style.configure("TLabel", background=surface)
        self.style.configure("Title.TLabel", background=surface)
        self.style.configure("Subtitle.TLabel", background=surface)
        self.style.configure("Badge.TLabel", background=panel)
        self.style.configure("Card.TLabel", background=panel)
        self.style.configure("Footer.TLabel", background=panel_alt)
        self.style.configure(
            "TButton",
            background=panel,
            bordercolor=border,
            lightcolor=border,
            darkcolor=border,
        )
        self.style.configure(
            "TCheckbutton",
            background=surface,
            indicatorcolor=border,
            bordercolor=border,
            lightcolor=border,
            darkcolor=border,
        )
        self.style.configure(
            "TCombobox",
            fieldbackground=panel,
            background=panel,
            bordercolor=border,
            lightcolor=border,
            darkcolor=border,
        )
        self.style.configure(
            "TScale",
            background=panel,
            troughcolor=border,
            bordercolor=border,
            lightcolor=COLORS["accent"],
            darkcolor=border,
        )
        self.style.configure(
            "Window.TButton",
            background=surface,
            bordercolor=surface,
            lightcolor=surface,
            darkcolor=surface,
        )
        for widget, original in self.tk_surfaces:
            widget.configure(bg=KEY_COLOR if transparent else original)

    def _set_opacity(self, value):
        opacity = max(config.MIN_OPACITY, min(1.0, float(value)))
        percent = int(round(opacity * 100))
        transparent = percent < 100
        if percent == getattr(self, "opacity_percent", None):
            return
        self.opacity_percent = percent
        if transparent:
            self.last_transparent_opacity = opacity
        self.opacity_var.set(opacity)
        self.opacity_label.configure(text=f"{percent}%")
        self.transparent_var.set(transparent)
        if transparent != getattr(self, "surfaces_transparent", None):
            self.surfaces_transparent = transparent
            self._apply_surface_colors(transparent)
            self.root.attributes("-alpha", 1.0)
            if transparent:
                self.root.attributes("-transparentcolor", KEY_COLOR)
                if self.glass.state() != "normal":
                    self.glass.deiconify()
            else:
                self.root.attributes("-transparentcolor", "")
                self.glass.withdraw()
        if transparent:
            self.glass.attributes("-alpha", opacity)
            self._sync_glass()

    def _toggle_transparency(self):
        opacity = self.last_transparent_opacity if self.transparent_var.get() else 1.0
        self.opacity_scale.set(opacity)
        self._set_opacity(opacity)

    def _update_caption(self):
        language = self.state.target_language
        if language == "es":
            self.caption.configure(text="DISCORD — detecta el idioma · prioriza español")
            self.direction_var.set("EN → ES")
        elif language == "en":
            self.caption.configure(text="DISCORD — detecta el idioma · prioriza inglés")
            self.direction_var.set("ES → EN")
        else:
            self.caption.configure(text="DISCORD — idioma detectado automáticamente")
            self.direction_var.set("AUTO")

    def _on_status_change(self, *_args):
        status = self.status_var.get().lower()
        color = COLORS["danger"] if "error" in status else COLORS["accent"]
        self.status_dot.itemconfigure(1, fill=color)

    def _on_language_change(self, _event):
        self.state.target_language = LANGUAGE_CODES[self.language_combo.get()]
        self._update_caption()
        self.status_var.set(f"Traducir a: {LANGUAGE_LABELS[self.state.target_language]}")

    def _toggle_pause(self):
        self.state.paused = not self.state.paused
        self.pause_button.configure(text="Reanudar" if self.state.paused else "Pausar")
        self.status_var.set("PAUSADO" if self.state.paused else "Escuchando Discord…")

    def _force_topmost(self, window, topmost):
        if sys.platform != "win32":
            return
        try:
            handle = int(window.frame(), 16)
            ctypes.windll.user32.SetWindowPos(
                handle,
                -1 if topmost else -2,
                0,
                0,
                0,
                0,
                0x0001 | 0x0002 | 0x0010,
            )
        except (ValueError, OSError):
            pass

    def _set_taskbar_visibility(self, visible):
        if sys.platform != "win32":
            return
        try:
            user32 = ctypes.windll.user32
            user32.GetWindowLongW.argtypes = [ctypes.wintypes.HWND, ctypes.c_int]
            user32.GetWindowLongW.restype = ctypes.c_long
            user32.SetWindowLongW.argtypes = [
                ctypes.wintypes.HWND,
                ctypes.c_int,
                ctypes.c_long,
            ]
            user32.SetWindowLongW.restype = ctypes.c_long
            handle = ctypes.wintypes.HWND(int(self.root.frame(), 16))
            style = user32.GetWindowLongW(handle, -20)
            if visible:
                style = (style & ~0x00000080) | 0x00000100
            else:
                style = (style & ~0x00000100) | 0x00000080
            user32.SetWindowLongW(handle, -20, style)
        except (ValueError, OSError):
            pass

    def _minimize(self):
        if self.minimized:
            return
        self.minimized = True
        self._minimizing = True
        self.root.overrideredirect(False)
        self._set_taskbar_visibility(True)
        self.root.iconify()
        if self.glass.state() == "normal":
            self.glass.withdraw()
        self.root.after_idle(self._finish_minimize)

    def _finish_minimize(self):
        self._minimizing = False

    def _on_restore(self, *_args):
        if not self.minimized or self._minimizing:
            return
        self.minimized = False
        self.root.after(80, self._restore_chrome)

    def _restore_chrome(self):
        if self.minimized or self.stop_event.is_set():
            return
        self.root.overrideredirect(True)
        self._set_taskbar_visibility(False)
        self.root.attributes("-topmost", True)
        self._force_topmost(self.root, True)
        self.root.lift()
        if self.transparent_var.get() and self.glass.state() != "normal":
            self.glass.deiconify()
        self._reassert_topmost()

    def _reassert_topmost(self, *_args):
        if self.minimized or self.stop_event.is_set():
            return
        glass = getattr(self, "glass", None)
        if glass is not None:
            glass.attributes("-topmost", True)
            self._force_topmost(glass, True)
        self.root.attributes("-topmost", True)
        self._force_topmost(self.root, True)
        self.root.lift()
        self._sync_glass()

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
        glass = getattr(self, "glass", None)
        if glass is not None:
            glass.destroy()
        self.root.destroy()

    def run(self):
        self.root.mainloop()
