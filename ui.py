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

LANGUAGE_LABELS = {
    "es": "Español",
    "en": "English",
    "fr": "Francés",
    "pt": "Portugués",
    "ru": "Ruso",
    "it": "Italiano",
    "zh": "Taiwanés",
    "de": "Alemán",
    "auto": "Auto (detectar)",
}
LANGUAGE_CODES  = {label: code for code, label in LANGUAGE_LABELS.items()}
LANGUAGE_ORDER  = (*config.TARGET_LANGUAGES, "auto")

KEY_COLOR = "#0d0f14"

COLORS = {
    "bg":           "#0d0f14",
    "panel":        "#13161f",
    "panel_alt":    "#0f1118",
    "text":         "#e8ecf5",
    "muted":        "#6b7589",
    "accent":       "#8b7cf8",
    "accent_dim":   "#2e2660",
    "accent_hover": "#a593ff",
    "warning":      "#f5a84a",
    "danger":       "#f07878",
    "success":      "#5ec97e",
    "border":       "#1c2030",
    "hover":        "#191e2d",
    "sep":          "#181c29",
}

SPEAKER_COLORS = ["#5ab0ff", "#f5a84a", "#5ec97e", "#c792ff", "#f07878", "#f2d45a"]


class TranslatorUI:
    # ── Init ──────────────────────────────────────────────────────────────────

    def __init__(self, ui_queue, stop_event, state):
        self.ui_queue   = ui_queue
        self.stop_event = stop_event
        self.state      = state

        self.root = tk.Tk()
        self.root.title("Traductor de Discord")
        self.root.configure(bg=COLORS["bg"])
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)

        self._compact            = False
        self._pre_compact_height = config.WINDOW_HEIGHT
        self.minimized           = False
        self._minimizing         = False
        self._message_count      = 0
        self._has_error          = False
        self._pulse_phase        = False

        self.opacity_var              = tk.DoubleVar(value=config.DEFAULT_OPACITY)
        self.transparent_var          = tk.BooleanVar(value=False)
        self.last_transparent_opacity = config.TRANSPARENT_OPACITY
        self.root.attributes("-alpha", 1.0)

        self._configure_styles()
        self._build()
        self._update_caption()
        self.root.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}")
        self.root.minsize(config.WINDOW_MIN_WIDTH, config.WINDOW_MIN_HEIGHT)
        self._center_top()
        self._create_glass()
        self._add_resize_handles()
        self._set_opacity(config.DEFAULT_OPACITY)
        self._do_pulse()

        self.root.bind("<Map>", self._reassert_topmost)
        self.root.bind("<Map>", self._on_restore, add="+")
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        self.root.after(50,  self._center_top)
        self.root.after(200, self._reassert_topmost)
        self.root.after(config.POLL_INTERVAL_MS, self._poll)

    # ── Styles ────────────────────────────────────────────────────────────────

    def _configure_styles(self):
        self.style = ttk.Style()
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")

        # Frames
        for name, bg in (
            ("Header.TFrame", COLORS["bg"]),
            ("Card.TFrame",   COLORS["border"]),
            ("Inner.TFrame",  COLORS["panel"]),
            ("Footer.TFrame", COLORS["panel_alt"]),
            ("Sep.TFrame",    COLORS["sep"]),
        ):
            self.style.configure(name, background=bg)

        # Labels
        self.style.configure("TLabel",          background=COLORS["bg"],        foreground=COLORS["muted"],  font=("Segoe UI", 10))
        self.style.configure("Title.TLabel",    background=COLORS["bg"],        foreground=COLORS["text"],   font=("Segoe UI", 14, "bold"))
        self.style.configure("Subtitle.TLabel", background=COLORS["bg"],        foreground=COLORS["muted"],  font=("Segoe UI", 9))
        self.style.configure("Ctrl.TLabel",     background=COLORS["bg"],        foreground=COLORS["muted"],  font=("Segoe UI", 9))
        self.style.configure("Badge.TLabel",    background=COLORS["border"],    foreground=COLORS["accent"], font=("Segoe UI", 9, "bold"), padding=(8, 3))
        self.style.configure("Footer.TLabel",   background=COLORS["panel_alt"], foreground=COLORS["muted"],  font=("Segoe UI", 9))

        # Regular button
        self.style.configure(
            "TButton",
            background=COLORS["panel"], foreground=COLORS["text"],
            bordercolor=COLORS["border"], lightcolor=COLORS["border"], darkcolor=COLORS["border"],
            relief="flat", padding=(8, 4), font=("Segoe UI", 9),
        )
        self.style.map("TButton",
            background=[("active", COLORS["hover"])],
            bordercolor=[("active", COLORS["accent"])],
        )

        # Accent button (Pausar)
        self.style.configure(
            "Accent.TButton",
            background=COLORS["accent"], foreground="#0a0c14",
            bordercolor=COLORS["accent"], lightcolor=COLORS["accent"], darkcolor=COLORS["accent"],
            relief="flat", padding=(8, 4), font=("Segoe UI", 9, "bold"),
        )
        self.style.map("Accent.TButton", background=[("active", COLORS["accent_hover"])])

        # Window chrome buttons (−, ×, ⊡)
        self.style.configure(
            "Window.TButton",
            background=COLORS["bg"], foreground=COLORS["muted"],
            bordercolor=COLORS["bg"], lightcolor=COLORS["bg"], darkcolor=COLORS["bg"],
            relief="flat", padding=(6, 0), font=("Segoe UI", 11),
        )
        self.style.map("Window.TButton",
            background=[("active", COLORS["hover"])],
            foreground=[("active", COLORS["text"])],
        )

        # Checkbutton
        self.style.configure(
            "TCheckbutton",
            background=COLORS["bg"], foreground=COLORS["muted"],
            indicatorcolor=COLORS["panel"], indicatorforeground=COLORS["accent"],
            bordercolor=COLORS["border"], lightcolor=COLORS["border"], darkcolor=COLORS["border"],
            font=("Segoe UI", 9),
        )
        self.style.map("TCheckbutton",
            background=[("active", COLORS["bg"])],
            foreground=[("active", COLORS["text"])],
        )

        # Combobox
        self.style.configure(
            "TCombobox",
            fieldbackground=COLORS["panel"], background=COLORS["panel"],
            foreground=COLORS["text"], arrowcolor=COLORS["accent"],
            bordercolor=COLORS["border"], lightcolor=COLORS["border"], darkcolor=COLORS["border"],
            padding=3, font=("Segoe UI", 9),
        )
        self.style.map("TCombobox",
            fieldbackground=[("readonly", COLORS["panel"])],
            foreground=[("readonly", COLORS["text"])],
        )

        # Scale
        self.style.configure(
            "TScale",
            background=COLORS["bg"], troughcolor=COLORS["border"],
            bordercolor=COLORS["border"], lightcolor=COLORS["accent"], darkcolor=COLORS["border"],
        )

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        self.drag_widgets = []

        # ── Title bar ─────────────────────────────────────────────────────────
        bar = ttk.Frame(self.root, style="Header.TFrame", padding=(10, 8, 10, 8))
        bar.pack(fill="x")
        self._titlebar = bar

        # Window chrome buttons (right)
        ttk.Button(bar, text="×", style="Window.TButton", command=self._close,         width=3).pack(side="right")
        ttk.Button(bar, text="−", style="Window.TButton", command=self._minimize,      width=3).pack(side="right", padx=(0, 2))
        self._compact_btn = ttk.Button(bar, text="⊡",    style="Window.TButton", command=self._toggle_compact, width=3)
        self._compact_btn.pack(side="right", padx=(0, 2))

        # Direction badge
        self.direction_var = tk.StringVar(value="EN → ES")
        badge = ttk.Label(bar, textvariable=self.direction_var, style="Badge.TLabel")
        badge.pack(side="right", padx=(0, 8))

        # Accent stripe + title + subtitle
        stripe = tk.Frame(bar, bg=COLORS["accent"], width=3, height=20)
        stripe.pack(side="left", fill="y")
        stripe.pack_propagate(False)
        t_lbl = ttk.Label(bar, text="TRADUCTOR DE DISCORD", style="Title.TLabel")
        t_lbl.pack(side="left", padx=(10, 0))
        s_lbl = ttk.Label(bar, text="subtítulos en tiempo real", style="Subtitle.TLabel")
        s_lbl.pack(side="left", padx=(10, 0))

        # All draggable surfaces
        self.drag_widgets = [bar, stripe, t_lbl, s_lbl, badge]
        for w in self.drag_widgets:
            w.bind("<ButtonPress-1>",  self._start_drag)
            w.bind("<B1-Motion>",      self._do_drag)
            w.bind("<ButtonRelease-1>",self._stop_drag)

        # Separator 1
        ttk.Frame(self.root, style="Sep.TFrame", height=1).pack(fill="x")

        # ── Footer — packed before card to claim bottom space ─────────────────
        self._footer = ttk.Frame(self.root, style="Footer.TFrame", padding=(12, 5))
        self._footer.pack(fill="x", side="bottom")

        self.status_dot = tk.Canvas(
            self._footer, width=10, height=10,
            bg=COLORS["panel_alt"], highlightthickness=0,
        )
        self.status_dot.create_oval(1, 1, 9, 9, fill=COLORS["accent_dim"], outline="", tags="glow")
        self.status_dot.create_oval(2, 2, 8, 8, fill=COLORS["accent"],     outline="", tags="dot")
        self.status_dot.pack(side="left", padx=(0, 7))

        self.status_var = tk.StringVar(value="Iniciando…")
        self.status_var.trace_add("write", self._on_status_change)
        ttk.Label(self._footer, textvariable=self.status_var, style="Footer.TLabel", anchor="w").pack(side="left")

        self.latency_var = tk.StringVar(value="")
        ttk.Label(self._footer, textvariable=self.latency_var, style="Footer.TLabel", anchor="e").pack(side="right")

        # ── Collapsible section (controls + opacity) ──────────────────────────
        self._collapsible = ttk.Frame(self.root, style="Header.TFrame", padding=(10, 7, 10, 7))
        self._collapsible.pack(fill="x")

        # Controls row
        ctrl = ttk.Frame(self._collapsible, style="Header.TFrame")
        ctrl.pack(fill="x")

        ttk.Label(ctrl, text="Traducir a:", style="Ctrl.TLabel").pack(side="left", padx=(0, 4))
        self.language_combo = ttk.Combobox(
            ctrl,
            values=[LANGUAGE_LABELS[code] for code in LANGUAGE_ORDER],
            state="readonly",
            width=18,
        )
        self.language_combo.set(LANGUAGE_LABELS[self.state.target_language])
        self.language_combo.bind("<<ComboboxSelected>>", self._on_language_change)
        self.language_combo.pack(side="left")

        # Vertical divider
        tk.Frame(ctrl, bg=COLORS["border"], width=1, height=22).pack(side="left", padx=(10, 10), fill="y")

        self.pause_button = ttk.Button(ctrl, text="⏸  Pausar",   command=self._toggle_pause,    width=10, style="Accent.TButton")
        self.pause_button.pack(side="left")
        ttk.Button(ctrl, text="🗑  Limpiar",  command=self._clear,          width=10).pack(side="left", padx=(5, 0))
        ttk.Button(ctrl, text="↺  Voces",    command=self._reset_speakers,  width=10).pack(side="left", padx=(5, 0))
        ttk.Button(ctrl, text="⌖  Centrar",  command=self._center_top,      width=10).pack(side="left", padx=(5, 0))

        # Opacity row
        op = ttk.Frame(self._collapsible, style="Header.TFrame")
        op.pack(fill="x", pady=(6, 0))
        ttk.Label(op, text="Opacidad:", style="Ctrl.TLabel").pack(side="left")
        self.opacity_scale = ttk.Scale(
            op, from_=config.MIN_OPACITY, to=1.0,
            value=config.DEFAULT_OPACITY, orient="horizontal",
            length=240, command=self._set_opacity,
        )
        self.opacity_scale.pack(side="left", padx=(5, 0))
        self.opacity_label = ttk.Label(
            op, text=f"{int(round(config.DEFAULT_OPACITY * 100))}%",
            width=5, style="Ctrl.TLabel",
        )
        self.opacity_label.pack(side="left", padx=(4, 12))
        ttk.Checkbutton(
            op, text="Transparente",
            variable=self.transparent_var,
            command=self._toggle_transparency,
        ).pack(side="left")

        # Separator 2
        self._sep2 = ttk.Frame(self.root, style="Sep.TFrame", height=1)
        self._sep2.pack(fill="x")

        # ── Text area ─────────────────────────────────────────────────────────
        self._card = ttk.Frame(self.root, style="Card.TFrame")
        self._card.pack(fill="both", expand=True, padx=10, pady=(8, 8))
        inner = ttk.Frame(self._card, style="Inner.TFrame")
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        txt_frame = tk.Frame(inner, bg=COLORS["panel_alt"])
        txt_frame.pack(fill="both", expand=True, padx=8, pady=8)

        self.text = tk.Text(
            txt_frame,
            wrap="word",
            bg=COLORS["panel_alt"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 13),
            spacing1=3,
            spacing3=4,
            padx=8,
            pady=6,
            cursor="arrow",
        )
        scrollbar = ttk.Scrollbar(txt_frame, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.text.pack(side="left", fill="both", expand=True)

        # Text tags
        self.text.tag_configure("time",       foreground="#3d4d63", font=("Segoe UI", 8))
        self.text.tag_configure("translated", foreground="#eef2ff", font=("Segoe UI", 15, "bold"))
        self.text.tag_configure("original",   foreground="#6b7a93", font=("Segoe UI", 10, "italic"))
        for idx, color in enumerate(SPEAKER_COLORS, start=1):
            self.text.tag_configure(f"speaker_{idx}", foreground=color, font=("Segoe UI", 10, "bold"))
        self.text.configure(state="disabled")

        self.tk_surfaces = [
            (txt_frame,       COLORS["panel_alt"]),
            (self.text,       COLORS["panel_alt"]),
            (self.status_dot, COLORS["panel_alt"]),
        ]

    # ── Resize handles ────────────────────────────────────────────────────────

    def _add_resize_handles(self):
        b = config.RESIZE_BORDER
        specs = [
            ("n",  "size_ns",    {"relx": 0.0, "rely": 0.0, "relwidth": 1.0, "height": b}),
            ("s",  "size_ns",    {"relx": 0.0, "rely": 1.0, "relwidth": 1.0, "height": b,     "anchor": "sw"}),
            ("w",  "size_we",    {"relx": 0.0, "rely": 0.0, "width": b,       "relheight": 1.0}),
            ("e",  "size_we",    {"relx": 1.0, "rely": 0.0, "width": b,       "relheight": 1.0, "anchor": "ne"}),
            ("nw", "size_nw_se", {"relx": 0.0, "rely": 0.0, "width": b * 2,   "height": b * 2}),
            ("ne", "size_ne_sw", {"relx": 1.0, "rely": 0.0, "width": b * 2,   "height": b * 2, "anchor": "n"}),
            ("sw", "size_ne_sw", {"relx": 0.0, "rely": 1.0, "width": b * 2,   "height": b * 2, "anchor": "s"}),
            ("se", "size_nw_se", {"relx": 1.0, "rely": 1.0, "width": b * 2,   "height": b * 2, "anchor": "se"}),
        ]
        for direction, cursor, place_kw in specs:
            handle = tk.Frame(self.root, bg=COLORS["bg"], cursor=cursor)
            handle.place(**place_kw)
            handle.bind("<ButtonPress-1>",  lambda e, d=direction: self._start_resize(e, d))
            handle.bind("<B1-Motion>",      self._do_resize)
            handle.bind("<ButtonRelease-1>",self._stop_resize)
            handle.lift()

    def _start_resize(self, event, direction):
        self._rzdir = direction
        self._rzsx  = event.x_root
        self._rzsy  = event.y_root
        self._rzsw  = self.root.winfo_width()
        self._rzsh  = self.root.winfo_height()
        self._rzwx  = self.root.winfo_x()
        self._rzwy  = self.root.winfo_y()

    def _do_resize(self, event):
        if not hasattr(self, "_rzdir"):
            return
        dx = event.x_root - self._rzsx
        dy = event.y_root - self._rzsy
        d  = self._rzdir
        mw = config.WINDOW_MIN_WIDTH
        mh = config.WINDOW_MIN_HEIGHT
        w, h = self._rzsw, self._rzsh
        x, y = self._rzwx, self._rzwy

        if "e" in d:
            w = max(mw, self._rzsw + dx)
        if "s" in d:
            h = max(mh, self._rzsh + dy)
        if "w" in d:
            nw = max(mw, self._rzsw - dx)
            x  = self._rzwx + (self._rzsw - nw)
            w  = nw
        if "n" in d:
            nh = max(mh, self._rzsh - dy)
            y  = self._rzwy + (self._rzsh - nh)
            h  = nh

        self.root.geometry(f"{int(w)}x{int(h)}+{int(x)}+{int(y)}")

    def _stop_resize(self, _event=None):
        for attr in ("_rzdir", "_rzsx", "_rzsy", "_rzsw", "_rzsh", "_rzwx", "_rzwy"):
            self.__dict__.pop(attr, None)

    # ── Compact mode ──────────────────────────────────────────────────────────

    def _toggle_compact(self):
        self._set_compact(not self._compact)

    def _set_compact(self, compact):
        self._compact = compact
        if compact:
            self._pre_compact_height = self.root.winfo_height()
            # Remove collapsible and sep2; re-pack card right after sep1
            self._card.pack_forget()
            self._sep2.pack_forget()
            self._collapsible.pack_forget()
            self._card.pack(fill="both", expand=True, padx=10, pady=(8, 8))
            self.root.geometry(
                f"{self.root.winfo_width()}x{config.COMPACT_HEIGHT}"
                f"+{self.root.winfo_x()}+{self.root.winfo_y()}"
            )
            self._compact_btn.configure(text="⊞")
        else:
            # Restore: re-insert collapsible and sep2 before card
            self._card.pack_forget()
            self._collapsible.pack(fill="x")
            self._sep2.pack(fill="x")
            self._card.pack(fill="both", expand=True, padx=10, pady=(8, 8))
            h = getattr(self, "_pre_compact_height", config.WINDOW_HEIGHT)
            self.root.geometry(
                f"{self.root.winfo_width()}x{h}"
                f"+{self.root.winfo_x()}+{self.root.winfo_y()}"
            )
            self._compact_btn.configure(text="⊡")

    # ── Window positioning ────────────────────────────────────────────────────

    def _center_top(self):
        self.root.update_idletasks()
        w  = self.root.winfo_width()  or config.WINDOW_WIDTH
        h  = self.root.winfo_height() or config.WINDOW_HEIGHT
        sw = self.root.winfo_screenwidth()
        x  = max(0, (sw - w) // 2)
        self.root.geometry(f"{w}x{h}+{x}+{config.WINDOW_TOP_MARGIN}")

    # ── Drag ─────────────────────────────────────────────────────────────────

    def _start_drag(self, event):
        if event.widget not in self.drag_widgets:
            return
        self.drag_offset_x = event.x_root - self.root.winfo_x()
        self.drag_offset_y = event.y_root - self.root.winfo_y()

    def _do_drag(self, event):
        if not hasattr(self, "drag_offset_x"):
            return
        self.root.geometry(
            f"+{event.x_root - self.drag_offset_x}+{event.y_root - self.drag_offset_y}"
        )

    def _stop_drag(self, _event=None):
        self.__dict__.pop("drag_offset_x", None)

    # ── Glass overlay ─────────────────────────────────────────────────────────

    def _create_glass(self):
        self.glass = tk.Toplevel(self.root)
        self.glass.overrideredirect(True)
        self.glass.configure(bg=COLORS["bg"])
        self.glass.attributes("-topmost", True)
        self.glass.withdraw()
        self.glass.bind("<Button-1>", self._on_glass_click)
        self.glass.bind("<Map>",      self._on_glass_map)
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
            pt = ctypes.wintypes.POINT(0, 0)
            ctypes.windll.user32.ClientToScreen(
                ctypes.wintypes.HWND(int(self.root.frame(), 16)), ctypes.byref(pt)
            )
            return pt.x, pt.y
        return self.root.winfo_rootx(), self.root.winfo_rooty()

    def _sync_glass(self, _event=None):
        glass = getattr(self, "glass", None)
        if glass is None or glass.state() != "normal":
            return
        x, y = self._client_origin()
        geo  = f"{self.root.winfo_width()}x{self.root.winfo_height()}+{x}+{y}"
        if glass.geometry() != geo:
            glass.geometry(geo)

    # ── Transparency / opacity ────────────────────────────────────────────────

    def _apply_surface_colors(self, transparent):
        K         = KEY_COLOR
        surface   = K if transparent else COLORS["bg"]
        panel     = K if transparent else COLORS["panel"]
        panel_alt = K if transparent else COLORS["panel_alt"]
        border    = K if transparent else COLORS["border"]
        sep       = K if transparent else COLORS["sep"]

        for name, bg in (
            ("Header.TFrame", surface),
            ("Card.TFrame",   border),
            ("Inner.TFrame",  panel),
            ("Footer.TFrame", panel_alt),
            ("Sep.TFrame",    sep),
        ):
            self.style.configure(name, background=bg)

        for name in ("TLabel", "Title.TLabel", "Subtitle.TLabel", "Ctrl.TLabel"):
            self.style.configure(name, background=surface)
        self.style.configure("Badge.TLabel",  background=border)
        self.style.configure("Footer.TLabel", background=panel_alt)

        self.style.configure("TButton",
            background=panel, bordercolor=border, lightcolor=border, darkcolor=border)
        self.style.configure("TCheckbutton",
            background=surface, indicatorcolor=border, bordercolor=border,
            lightcolor=border, darkcolor=border)
        self.style.configure("TCombobox",
            fieldbackground=panel, background=panel,
            bordercolor=border, lightcolor=border, darkcolor=border)
        self.style.configure("TScale",
            background=surface, troughcolor=border, bordercolor=border,
            lightcolor=COLORS["accent"], darkcolor=border)
        self.style.configure("Window.TButton",
            background=surface, bordercolor=surface, lightcolor=surface, darkcolor=surface)

        for widget, original in self.tk_surfaces:
            widget.configure(bg=K if transparent else original)

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

    # ── Status / captions ─────────────────────────────────────────────────────

    def _update_caption(self):
        lang = self.state.target_language
        if lang == "es":
            self.direction_var.set("EN → ES")
        elif lang == "en":
            self.direction_var.set("ES → EN")
        elif lang == "auto":
            self.direction_var.set("AUTO")
        else:
            self.direction_var.set(f"→ {LANGUAGE_LABELS[lang].upper()}")

    def _on_status_change(self, *_args):
        status = self.status_var.get().lower()
        self._has_error = "error" in status
        color = COLORS["danger"] if self._has_error else COLORS["accent"]
        self.status_dot.itemconfigure("dot", fill=color)
        if self._has_error:
            self.status_dot.itemconfigure("glow", fill="")

    def _do_pulse(self):
        """Subtle pulsing glow on the status dot to indicate the app is alive."""
        if self.stop_event.is_set():
            return
        if not self._has_error:
            self._pulse_phase = not self._pulse_phase
            glow = COLORS["accent_dim"] if self._pulse_phase else COLORS["bg"]
            self.status_dot.itemconfigure("glow", fill=glow)
        self.root.after(900, self._do_pulse)

    # ── Controls callbacks ────────────────────────────────────────────────────

    def _on_language_change(self, _event):
        label = self.language_combo.get()
        code  = LANGUAGE_CODES.get(label)
        if code is None:
            return
        self.state.target_language = code
        self._update_caption()
        self.status_var.set(f"Traducir a: {LANGUAGE_LABELS[code]}")

    def _toggle_pause(self):
        self.state.paused = not self.state.paused
        self.pause_button.configure(
            text="▶  Reanudar" if self.state.paused else "⏸  Pausar"
        )
        self.status_var.set("PAUSADO" if self.state.paused else "Escuchando Discord…")

    def _clear(self):
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")
        self._message_count = 0

    def _reset_speakers(self):
        self.state.reset_speakers = True
        self.status_var.set("Reiniciando voces…")

    # ── Window chrome ─────────────────────────────────────────────────────────

    def _force_topmost(self, window, topmost):
        if sys.platform != "win32":
            return
        try:
            handle = int(window.frame(), 16)
            ctypes.windll.user32.SetWindowPos(
                handle, -1 if topmost else -2, 0, 0, 0, 0,
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
            user32.GetWindowLongW.restype  = ctypes.c_long
            user32.SetWindowLongW.argtypes = [ctypes.wintypes.HWND, ctypes.c_int, ctypes.c_long]
            user32.SetWindowLongW.restype  = ctypes.c_long
            handle = ctypes.wintypes.HWND(int(self.root.frame(), 16))
            style  = user32.GetWindowLongW(handle, -20)
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
        self.minimized   = True
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

    # ── Message display ───────────────────────────────────────────────────────

    def _add_message(self, payload):
        speaker = payload.get("speaker", 1)
        idx     = ((speaker - 1) % 6) + 1
        tag     = f"speaker_{idx}"

        self.text.configure(state="normal")
        self.text.insert("end", f"{time.strftime('%H:%M:%S')}  ", "time")
        self.text.insert("end", f"● SPEAKER {speaker}\n",           tag)
        self.text.insert("end", payload["translated"] + "\n",       "translated")
        self.text.insert("end", payload["original"]   + "\n\n",     "original")

        # Prune: track message count instead of line count to handle multiline text
        self._message_count += 1
        if self._message_count > config.MAX_HISTORY_ENTRIES:
            surplus      = self._message_count - config.MAX_HISTORY_ENTRIES
            end_of_block = f"{surplus * 5}.0"
            self.text.delete("1.0", end_of_block)
            self._message_count = config.MAX_HISTORY_ENTRIES

        self.text.configure(state="disabled")
        self.text.see("end")
        self.latency_var.set(f"⏱ {payload['latency']:.1f}s")

    # ── Poll loop ─────────────────────────────────────────────────────────────

    def _poll(self):
        while True:
            try:
                event = self.ui_queue.get_nowait()
            except queue.Empty:
                break
            if event[0] == "message":
                self._add_message(event[1])
            elif event[0] in ("error", "status"):
                self.status_var.set(event[1])
        self.root.after(config.POLL_INTERVAL_MS, self._poll)

    # ── Close ─────────────────────────────────────────────────────────────────

    def _close(self):
        self.stop_event.set()
        glass = getattr(self, "glass", None)
        if glass is not None:
            glass.destroy()
        self.root.destroy()

    def run(self):
        self.root.mainloop()
