# main.py - Pytegrator - Linear-inspired 3-column shell
# Backend (app/lib, app/services logic, core) is untouched.

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import logging
import os
import sys
import ctypes
from typing import Dict, Any


# ── Environment & logging ───────────────────────────────────────────────────

def setup_environment() -> None:
    """Add the project root to sys.path and initialise the logger."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    try:
        from core.logger_config import setup_logging
        setup_logging()
    except (ImportError, ModuleNotFoundError) as exc:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        logging.warning(f"Logger personalizado nao carregado: {exc}")


# ── Application imports ─────────────────────────────────────────────────────

from app.lib.mappers import codigoMapper
from app.services.serviço_207.form_207 import Gerador207Frame
from app.services.soap.form_ferramentasoap import FerramentaSOAPFrame
from app.services.trace_interpreter.trace_interpreter import TraceInterpreterFrame
from app.views.xmlResultado import ResultadoFrame
from app.ui.theme import (
    COLOR_BG, COLOR_SURFACE, COLOR_SURFACE_ALT, COLOR_BORDER,
    COLOR_TEXT, COLOR_TEXT_MUTED, COLOR_ACCENT, COLOR_ACCENT_HOVER,
    SIDEBAR_BG, SIDEBAR_HOVER, SIDEBAR_ACTIVE, SIDEBAR_WIDTH,
    SPACE_SM, SPACE_MD, SPACE_LG, SPACE_XL,
    RADIUS_MD, RADIUS_LG,
    FONT_SM, FONT_MD, FONT_XL, FONT_2XL,
    c,
)


# ── Constants ───────────────────────────────────────────────────────────────

APP_NAME       = "Pytegrator"
DEFAULT_WIDTH  = 1366
DEFAULT_HEIGHT = 768
ICON_PATH      = os.path.join("app", "assets", "icon.ico")

# ── Navigation manifest ─────────────────────────────────────────────────────
# (frame_key, display_label, icon_char, section_key)

NAV_ITEMS = [
    ("Gerador207",       "Gerador 207",       "  ", "integrador"),
    ("FerramentaSOAP",   "Integracao SOAP",    "  ", "integrador"),
    ("Resultado",        "Resultado XML",      "  ", "integrador"),
    ("TraceInterpreter", "Trace Interpreter",  "  ", "ferramentas"),
]

NAV_SECTIONS = {
    "integrador":  "INTEGRADOR",
    "ferramentas": "FERRAMENTAS",
}


# ── Main shell ───────────────────────────────────────────────────────────────

class AppController(ctk.CTk):
    """
    Main application window -- Linear-inspired 3-column layout.

    Structure
    ---------
    +-------------+------------------------------------------------------+
    |  SIDEBAR    |  CONTENT  (stacked frames raised on demand)          |
    |  (fixed)    |                                                      |
    |  App name   |  MenuPrincipal | Gerador207 | FerramentaSOAP | ...  |
    |  Nav items  |                                                      |
    |  ---------  |                                                      |
    |  Footer     |                                                      |
    +-------------+------------------------------------------------------+

    Public API (consumed by service frames)
    ----------------------------------------
    - self.shared_data       -- dict used to pass data between frames
    - self.show_frame(name)  -- raise the named frame
    """

    def __init__(self) -> None:
        super().__init__()
        logging.info("Inicializando AppController (Linear shell).")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color=c(COLOR_BG))

        self.title(APP_NAME)
        self.geometry(f"{DEFAULT_WIDTH}x{DEFAULT_HEIGHT}")
        self.minsize(960, 600)
        self.resizable(True, True)

        self.is_fullscreen: bool = False
        self.bind("<F11>", lambda _e: self._toggle_fullscreen())
        self.bind("<Escape>", lambda _e: self._exit_fullscreen())

        self._center_window()
        self._load_app_icon()

        # Shared state passed between frames
        self.shared_data: Dict[str, Any] = {"current_xml": ""}

        # Active nav button refs
        self._nav_buttons: Dict[str, ctk.CTkButton] = {}

        # Root grid: col 0 = sidebar (fixed), col 1 = content (expands)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_content()

        logging.info("Shell pronto.")

    # ── Sidebar ──────────────────────────────────────────────────────────────

    def _build_sidebar(self) -> None:
        sidebar = ctk.CTkFrame(
            self,
            fg_color=c(SIDEBAR_BG),
            corner_radius=0,
            width=SIDEBAR_WIDTH,
            border_width=1,
            border_color=c(COLOR_BORDER),
        )
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_columnconfigure(0, weight=1)
        sidebar.grid_rowconfigure(3, weight=1)   # spacer before footer

        # -- Logo row --------------------------------------------------------
        logo = ctk.CTkFrame(sidebar, fg_color="transparent")
        logo.grid(row=0, column=0, sticky="ew",
                  padx=SPACE_MD, pady=(SPACE_LG, SPACE_MD))

        ctk.CTkLabel(
            logo,
            text="P",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=c(COLOR_ACCENT),
            width=28,
        ).pack(side="left", padx=(0, 6))

        ctk.CTkLabel(
            logo,
            text=APP_NAME,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=c(COLOR_TEXT),
        ).pack(side="left")

        # -- Top divider -----------------------------------------------------
        ctk.CTkFrame(
            sidebar, fg_color=c(COLOR_BORDER), height=1, corner_radius=0
        ).grid(row=1, column=0, sticky="ew")

        # -- Navigation ------------------------------------------------------
        nav = ctk.CTkFrame(sidebar, fg_color="transparent")
        nav.grid(row=2, column=0, sticky="ew",
                 padx=SPACE_SM, pady=(SPACE_SM, 0))

        current_section: str = ""
        for frame_key, label, icon, section in NAV_ITEMS:
            if section != current_section:
                current_section = section
                ctk.CTkLabel(
                    nav,
                    text=NAV_SECTIONS.get(section, section.upper()),
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color=c(COLOR_TEXT_MUTED),
                    anchor="w",
                ).pack(anchor="w", padx=SPACE_SM, pady=(SPACE_MD, 2))

            btn = ctk.CTkButton(
                nav,
                text=f"{icon} {label}",
                anchor="w",
                height=34,
                corner_radius=RADIUS_MD,
                fg_color="transparent",
                hover_color=c(SIDEBAR_HOVER),
                text_color=c(COLOR_TEXT_MUTED),
                font=ctk.CTkFont(size=FONT_SM),
                command=lambda k=frame_key: self.show_frame(k),
            )
            btn.pack(fill="x", padx=2, pady=1)
            self._nav_buttons[frame_key] = btn

        # -- Spacer (row 3 has weight=1) -------------------------------------
        ctk.CTkFrame(sidebar, fg_color="transparent").grid(
            row=3, column=0, sticky="nsew"
        )

        # -- Footer divider --------------------------------------------------
        ctk.CTkFrame(
            sidebar, fg_color=c(COLOR_BORDER), height=1, corner_radius=0
        ).grid(row=4, column=0, sticky="ew")

        # -- Home button (footer) --------------------------------------------
        home_btn = ctk.CTkButton(
            sidebar,
            text="  Inicio",
            anchor="w",
            height=36,
            corner_radius=RADIUS_MD,
            fg_color="transparent",
            hover_color=c(SIDEBAR_HOVER),
            text_color=c(COLOR_TEXT_MUTED),
            font=ctk.CTkFont(size=FONT_SM),
            command=lambda: self.show_frame("MenuPrincipal"),
        )
        home_btn.grid(row=5, column=0, sticky="ew",
                      padx=SPACE_SM, pady=(SPACE_SM, SPACE_LG))
        self._nav_buttons["MenuPrincipal"] = home_btn

    # ── Content area ─────────────────────────────────────────────────────────

    def _build_content(self) -> None:
        self.container = ctk.CTkFrame(self, fg_color=c(COLOR_BG), corner_radius=0)
        self.container.grid(row=0, column=1, sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames: Dict[str, tk.Widget] = {}

        frames_to_load: tuple = (
            MenuPrincipalFrame,
            Gerador207Frame,
            FerramentaSOAPFrame,
            ResultadoFrame,
            TraceInterpreterFrame,
        )

        for F in frames_to_load:
            name = F.__name__.replace("Frame", "")
            frame = F(self.container, self)  # type: ignore[call-arg]
            self.frames[name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            logging.debug(f"Frame '{name}' registered.")

        self.show_frame("MenuPrincipal")

    # ── Navigation ───────────────────────────────────────────────────────────

    def show_frame(self, frame_name: str) -> None:
        logging.info(f"Navigating to: {frame_name}")
        frame = self.frames.get(frame_name)

        if not frame:
            logging.error(f"Frame not found: {frame_name!r}")
            messagebox.showerror(
                "Erro de Navegacao",
                f"A tela '{frame_name}' nao foi encontrada.",
            )
            return

        if frame_name == "Resultado":
            xml = self.shared_data.get("current_xml", "<Erro>Nenhum XML.</Erro>")
            if hasattr(frame, "set_xml"):
                getattr(frame, "set_xml")(xml)

        self._update_nav_highlight(frame_name)
        frame.tkraise()

    def _update_nav_highlight(self, active_key: str) -> None:
        for key, btn in self._nav_buttons.items():
            if key == active_key:
                btn.configure(fg_color=c(SIDEBAR_ACTIVE), text_color=c(COLOR_TEXT))
            else:
                btn.configure(fg_color="transparent", text_color=c(COLOR_TEXT_MUTED))

    # ── Window utilities ─────────────────────────────────────────────────────

    def _toggle_fullscreen(self) -> None:
        self.is_fullscreen = not self.is_fullscreen
        try:
            self.attributes("-fullscreen", self.is_fullscreen)
        except Exception:
            if self.is_fullscreen:
                self.state("zoomed")

    def _exit_fullscreen(self) -> None:
        self.is_fullscreen = False
        try:
            self.attributes("-fullscreen", False)
        except Exception:
            pass

    def _center_window(self) -> None:
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        x = (sw - DEFAULT_WIDTH) // 2
        y = (sh - DEFAULT_HEIGHT) // 2
        self.geometry(f"+{x}+{y}")

    def _load_app_icon(self) -> None:
        try:
            if os.path.exists(ICON_PATH):
                self.iconbitmap(ICON_PATH)
        except Exception as exc:
            logging.warning(f"Icone nao carregado: {exc}")


# ── Home / welcome screen ────────────────────────────────────────────────────

class MenuPrincipalFrame(ctk.CTkFrame):
    """
    Welcome / dashboard screen shown on startup.

    Features clickable module cards; navigation is also available
    via the persistent sidebar at all times.
    """

    _CARDS = [
        {
            "title": "Gerador de XML - Servico 207",
            "desc":  "Crie arquivos XML para integracao com o Mega ERP.",
            "frame": "Gerador207",
        },
        {
            "title": "Integracao SOAP",
            "desc":  "Envie payloads XML em lote para um endpoint SOAP.",
            "frame": "FerramentaSOAP",
        },
        {
            "title": "Trace Interpreter",
            "desc":  "Analise traces JSON e extraia SQLs para depuracao.",
            "frame": "TraceInterpreter",
        },
    ]

    def __init__(self, parent: tk.Widget, controller: "AppController") -> None:
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self._build()

    def _build(self) -> None:
        # -- Page header -----------------------------------------------------
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew",
                    padx=SPACE_XL, pady=(SPACE_XL, SPACE_MD))

        ctk.CTkLabel(
            header,
            text="Bem-vindo ao Pytegrator",
            font=ctk.CTkFont(size=FONT_2XL, weight="bold"),
            text_color=c(COLOR_TEXT),
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="Integracao com Mega ERP  -  XML, SOAP e Trace",
            font=ctk.CTkFont(size=FONT_MD),
            text_color=c(COLOR_TEXT_MUTED),
            anchor="w",
        ).pack(anchor="w", pady=(4, 0))

        # -- Divider ---------------------------------------------------------
        ctk.CTkFrame(
            self, fg_color=c(COLOR_BORDER), height=1, corner_radius=0
        ).grid(row=1, column=0, sticky="ew", padx=SPACE_XL)

        # -- Cards -----------------------------------------------------------
        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.grid(row=2, column=0, sticky="nsew",
                         padx=SPACE_XL, pady=SPACE_XL)
        for i in range(len(self._CARDS)):
            cards_frame.grid_columnconfigure(i, weight=1, uniform="home_cards")

        for col, card_data in enumerate(self._CARDS):
            self._make_card(cards_frame, col, card_data)

    def _make_card(self, parent: ctk.CTkFrame, col: int, data: dict) -> None:
        card = ctk.CTkFrame(
            parent,
            fg_color=c(COLOR_SURFACE),
            corner_radius=RADIUS_LG,
            border_width=1,
            border_color=c(COLOR_BORDER),
            cursor="hand2",
        )
        card.grid(row=0, column=col, sticky="nsew", padx=SPACE_SM)
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text=data["title"],
            font=ctk.CTkFont(size=FONT_MD, weight="bold"),
            text_color=c(COLOR_TEXT),
            anchor="w",
            wraplength=260,
        ).grid(row=0, column=0, sticky="ew",
               padx=SPACE_LG, pady=(SPACE_LG, SPACE_SM))

        ctk.CTkLabel(
            card,
            text=data["desc"],
            font=ctk.CTkFont(size=FONT_SM),
            text_color=c(COLOR_TEXT_MUTED),
            anchor="w",
            justify="left",
            wraplength=260,
        ).grid(row=1, column=0, sticky="ew",
               padx=SPACE_LG, pady=(0, SPACE_MD))

        ctk.CTkButton(
            card,
            text="Abrir",
            height=30,
            corner_radius=RADIUS_MD,
            fg_color=c(COLOR_ACCENT),
            hover_color=c(COLOR_ACCENT_HOVER),
            text_color="white",
            font=ctk.CTkFont(size=FONT_SM, weight="bold"),
            command=lambda k=data["frame"]: self.controller.show_frame(k),
        ).grid(row=2, column=0, sticky="w",
               padx=SPACE_LG, pady=(0, SPACE_LG))

        def _enter(_e, f=card):
            f.configure(fg_color=c(COLOR_SURFACE_ALT))

        def _leave(_e, f=card):
            f.configure(fg_color=c(COLOR_SURFACE))

        def _click(_e, k=data["frame"]):
            self.controller.show_frame(k)

        card.bind("<Enter>", _enter)
        card.bind("<Leave>", _leave)
        card.bind("<Button-1>", _click)


# ── Entry point ──────────────────────────────────────────────────────────────

def main() -> None:
    try:
        setup_environment()

        if sys.platform.startswith("win"):
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "Pytegrator.App.1"
            )

        logging.info("Carregando recursos...")
        codigoMapper.carregar_mapa_codigos()
        logging.info("Mapa de codigos carregado.")

        app = AppController()
        app.mainloop()
        logging.info("Aplicacao encerrada normalmente.")

    except Exception as exc:
        logging.critical(f"ERRO CRITICO: {exc}", exc_info=True)
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Erro Critico", f"Falha ao iniciar:\n\n{exc}")
        root.destroy()


if __name__ == "__main__":
    main()