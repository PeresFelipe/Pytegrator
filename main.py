# main.py — CustomTkinter com seções e ajuste de texto nos cards

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import logging
import os
import sys
import ctypes
from typing import Dict, Union, List, Callable, Any
from PIL import Image


# --- Configuração de Path e Logging ---
def setup_environment():
    """Configura o path do sistema e inicializa o logger."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        logging.info(f"Adicionado diretório raiz ao sys.path: {project_root}")

    try:
        from core.logger_config import setup_logging

        setup_logging()
    except (ImportError, ModuleNotFoundError) as e:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - Módulo de log não encontrado: %(message)s",
        )
        logging.warning(
            f"Falha ao carregar 'core.logger_config': {e}. Usando config básica."
        )


# --- Imports da Aplicação ---
from app.lib.mappers import codigoMapper
from app.services.serviço_207.form_207 import Gerador207Frame
from app.services.soap.form_ferramentasoap import FerramentaSOAPFrame
from app.services.trace_interpreter.trace_interpreter import TraceInterpreterFrame
from app.views.xmlResultado import ResultadoFrame


# --- Constantes ---
APP_NAME = "Pytegrator"
DEFAULT_WIDTH = 1366
DEFAULT_HEIGHT = 768
ICON_PATH = os.path.join("app", "assets", "icon.ico")
SOAP_ICON_PATH = os.path.join("app", "assets", "soap_icon.png")
XML_ICON_PATH = os.path.join("app", "assets", "xml_icon.png")
TRACE_ICON_PATH = os.path.join("app", "assets", "trace_icon.png")

# Paleta (dark elegante)
BG_APP = ("#0B1220", "#0B1220")  # fundo da janela
APPBAR_BG = ("#0F172A", "#0F172A")
APPBAR_FG = ("#E5E7EB", "#E5E7EB")
SURFACE = ("#111827", "#111827")
SURFACE_ALT = ("#0F172A", "#0F172A")
BORDER = ("#1F2937", "#1F2937")
TEXT = ("#E5E7EB", "#E5E7EB")
TEXT_MUTED = ("#9CA3AF", "#9CA3AF")
PRIMARY = ("#22C55E", "#22C55E")
PRIMARY_HOVER = ("#16A34A", "#16A34A")
CARD_HOVER = ("#101826", "#101826")


class AppController(ctk.CTk):
    """
    Controlador principal da aplicação em CustomTkinter.
    Layout:
    ┌───────────────────────────────────────────────────────────┐
    │ AppBar (título + ações)                                   │
    ├───────────────────────────────────────────────────────────┤
    │ Content (container onde os Frames são empilhados)         │
    └───────────────────────────────────────────────────────────┘
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logging.info("Inicializando o controlador principal (CTk).")

        # Aparência global
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")
        self.configure(fg_color=BG_APP)

        self.title(APP_NAME)
        self.geometry(f"{DEFAULT_WIDTH}x{DEFAULT_HEIGHT}")
        # Permite redimensionar livremente; define um mínimo confortável para notebooks
        self.minsize(1024, 640)
        self.resizable(True, True)

        # Atalhos de janela: F11 (tela cheia) / Esc (sair de tela cheia)
        self.is_fullscreen = False
        self.bind("<F11>", lambda e: self._toggle_fullscreen())
        self.bind("<Escape>", lambda e: self._exit_fullscreen())

        self._center_window()
        self._load_app_icon()

        self.shared_data: Dict = {"current_xml": ""}

        # Grid raiz
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- AppBar ---
        self._build_appbar()

        # --- Container de Conteúdo ---
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=1, column=0, sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames: Dict[str, tk.Widget] = {}

        # Tipagem relaxada para evitar conflito com módulos inferidos pela Pylance
        frames_to_load: tuple[Any, ...] = (
            MenuPrincipalFrame,
            Gerador207Frame,
            FerramentaSOAPFrame,
            ResultadoFrame,
            TraceInterpreterFrame,
        )

        for F in frames_to_load:
            frame_name = F.__name__.replace("Frame", "")
            frame = F(self.container, self)  # type: ignore[call-arg]
            self.frames[frame_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            logging.debug(f"Frame '{frame_name}' criado e armazenado.")

        self.show_frame("MenuPrincipal")
        logging.info("App pronto. Exibindo menu principal.")

    # ------------------------- Controle de Janela -------------------------
    def _toggle_fullscreen(self):
        try:
            self.is_fullscreen = not getattr(self, "is_fullscreen", False)
            self.attributes("-fullscreen", self.is_fullscreen)
        except Exception:
            # Fallback no Windows: maximiza
            if self.is_fullscreen:
                try:
                    self.state("zoomed")
                except Exception:
                    pass

    def _exit_fullscreen(self):
        try:
            self.is_fullscreen = False
            self.attributes("-fullscreen", False)
        except Exception:
            pass

    # ------------------------- Navegação -------------------------
    def show_frame(self, frame_name: str):
        logging.info(f"Transicionando para a tela: {frame_name}")
        frame = self.frames.get(frame_name)

        if not frame:
            logging.error(f"Tentativa de mostrar um frame inexistente: {frame_name}")
            messagebox.showerror(
                "Erro de Navegação", f"A tela '{frame_name}' não foi encontrada."
            )
            return

        if frame_name == "Resultado":
            xml_data = self.shared_data.get(
                "current_xml", "<Erro>Nenhum XML encontrado.</Erro>"
            )
            if hasattr(frame, "set_xml"):
                getattr(frame, "set_xml")(xml_data)

        frame.tkraise()

    # ------------------------- AppBar -------------------------
    def _build_appbar(self):
        appbar = ctk.CTkFrame(self, fg_color=APPBAR_BG, corner_radius=0)
        appbar.grid(row=0, column=0, sticky="ew")
        appbar.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            appbar,
            text=APP_NAME,
            text_color=APPBAR_FG[0],
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        title.grid(row=0, column=0, sticky="w", padx=18, pady=12)

        btn_home = ctk.CTkButton(
            appbar,
            text="Menu",
            fg_color=PRIMARY,
            hover_color=PRIMARY_HOVER,
            text_color="black",
            height=32,
            command=lambda: self.show_frame("MenuPrincipal"),
        )
        btn_home.grid(row=0, column=1, sticky="e", padx=12, pady=8)

    # ------------------------- Utilidades -------------------------
    def _center_window(self):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw // 2) - (DEFAULT_WIDTH // 2)
        y = (sh // 2) - (DEFAULT_HEIGHT // 2)
        self.geometry(f"+{x}+{y}")
        logging.info(f"Janela centralizada em: x={x}, y={y}")

    def _load_app_icon(self):
        try:
            if os.path.exists(ICON_PATH):
                self.iconbitmap(ICON_PATH)
                logging.info(f"Ícone '{ICON_PATH}' carregado com sucesso.")
            else:
                logging.warning(f"Arquivo de ícone não encontrado: {ICON_PATH}")
        except Exception as e:
            logging.error(f"Não foi possível carregar o ícone: {e}")


class MenuPrincipalFrame(ctk.CTkFrame):
    """Menu principal em estilo "cards" com CustomTkinter, com seções por categoria."""

    def __init__(self, parent: tk.Widget, controller: "AppController"):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        self.icons: Dict[str, Union[ctk.CTkImage, None]] = {
            "soap": self._load_icon(SOAP_ICON_PATH, (38, 38)),
            "xml": self._load_icon(XML_ICON_PATH, (38, 38)),
            "trace": self._load_icon(TRACE_ICON_PATH, (38, 38)),
        }

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        integrador_items = [
            {
                "title": "Gerador de XML - Serviço 207",
                "desc": "Crie arquivos XML para integração ao Mega ERP.",
                "command": lambda: self.controller.show_frame("Gerador207"),
                "icon": self.icons.get("xml"),
            },
            {
                "title": "Integração SOAP",
                "desc": "Envie XML para um endpoint SOAP.",
                "command": lambda: self.controller.show_frame("FerramentaSOAP"),
                "icon": self.icons.get("soap"),
            },
        ]

        self._create_section(row=1, title="Serviços Integrador", items=integrador_items)

        ferramentas_items = [
            {
                "title": "Interpretador de Trace",
                "desc": "Analise traces JSON e extraia SQL para depuração.",
                "command": lambda: self.controller.show_frame("TraceInterpreter"),
                "icon": self.icons.get("trace"),
            },
        ]

        self._create_section(row=2, title="Ferramentas", items=ferramentas_items)

    def _create_section(self, row: int, title: str, items: List[Dict[str, Any]]):
        """Renderiza uma *categoria* destacada (chip + divisor) e abaixo os cards.
        Remove o "cardzão" de seção e deixa o foco nos itens.
        """
        # Container da seção (transparente)
        section = ctk.CTkFrame(self, fg_color="transparent")
        section.grid(row=row, column=0, sticky="nsew", padx=14, pady=(4, 10))
        section.grid_columnconfigure(0, weight=1)

        # CHIP de categoria
        chip = ctk.CTkFrame(
            section,
            fg_color=APPBAR_BG,  # leve contraste
            border_color=PRIMARY[0],
            border_width=1,
            corner_radius=999,
        )
        chip.grid(row=0, column=0, sticky="w", padx=2, pady=(2, 6))

        chip_label = ctk.CTkLabel(
            chip,
            text=title.upper(),
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=PRIMARY[0],
        )
        chip_label.grid(row=0, column=0, padx=12, pady=6)

        # Divisor fino
        divider = ctk.CTkFrame(section, fg_color=BORDER[0], height=1, corner_radius=1)
        divider.grid(row=1, column=0, sticky="ew")

        # Área de cards
        content = ctk.CTkFrame(section, fg_color="transparent")
        content.grid(row=2, column=0, sticky="nsew", pady=(6, 0))
        for c in range(3):
            content.grid_columnconfigure(c, weight=1, uniform=f"cards_{row}")

        for i, item in enumerate(items):
            card = self._create_menu_card(content, **item)
            card.grid(row=i // 3, column=i % 3, sticky="nsew", padx=8, pady=6)

    def _create_menu_card(
        self,
        parent: ctk.CTkFrame,
        title: str,
        desc: str,
        command: Callable[[], None],
        icon: Union[ctk.CTkImage, None],
    ) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            parent,
            fg_color=SURFACE,
            corner_radius=14,
            border_width=1,
            border_color=BORDER,
        )
        card.grid_columnconfigure(1, weight=1)

        if icon:
            icon_lbl = ctk.CTkLabel(card, image=icon, text="")
            icon_lbl.grid(
                row=0, column=0, rowspan=2, sticky="nsw", padx=(14, 14), pady=16
            )

        title_lbl = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT[0],
        )
        title_lbl.grid(row=0, column=1, sticky="ew", padx=16, pady=(18, 0))

        # Descrição — com padding lateral e wrap controlado para não encostar no limite
        desc_lbl = ctk.CTkLabel(
            card,
            text=desc,
            font=ctk.CTkFont(size=12),
            text_color=TEXT_MUTED[0],
            wraplength=250,
            justify="left",
            anchor="w",
        )
        desc_lbl.grid(row=1, column=1, sticky="ew", padx=16, pady=(2, 16))

        btn = ctk.CTkButton(
            card,
            text="Abrir",
            height=32,
            fg_color=PRIMARY,
            hover_color=PRIMARY_HOVER,
            text_color="black",
            command=command,
        )
        btn.grid(row=2, column=1, sticky="e", padx=16, pady=(0, 16))

        def on_enter(_):
            card.configure(fg_color=CARD_HOVER)

        def on_leave(_):
            card.configure(fg_color=SURFACE)

        for w in (card, title_lbl, desc_lbl):
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            w.bind("<Button-1>", lambda _e: command())
            w.configure(cursor="hand2")

        # Ajuste responsivo do wraplength conforme largura do card
        def _resize_wrap(_event=None):
            try:
                # margem interna total ~ 32 (16 esquerda + 16 direita)
                # ícone ocupa a coluna 0, então consideramos apenas a coluna 1
                available = max(220, card.winfo_width() - 80)
                desc_lbl.configure(wraplength=available)
            except Exception:
                pass

        card.bind("<Configure>", _resize_wrap)
        _resize_wrap()

        return card

    def _load_icon(
        self, file_path: str, size: tuple[int, int]
    ) -> Union[ctk.CTkImage, None]:
        if not os.path.exists(file_path):
            logging.warning(f"Arquivo de ícone não encontrado: {file_path}")
            return None
        try:
            return ctk.CTkImage(Image.open(file_path), size=size)
        except Exception as e:
            logging.error(f"Falha ao carregar ícone '{file_path}': {e}")
            return None


# --- Ponto de Entrada da Aplicação ---
def main():
    try:
        setup_environment()

        if sys.platform.startswith("win"):
            app_id = f"MyCompany.{APP_NAME}.1.0"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
            logging.info(f"AppUserModelID definido como: {app_id}")

        logging.info("Aplicação iniciada. Carregando recursos…")
        codigoMapper.carregar_mapa_codigos()
        logging.info("Mapa de códigos carregado com sucesso.")

        app = AppController()
        app.mainloop()
        logging.info("Aplicação encerrada normalmente.")

    except Exception as e:
        logging.critical(f"ERRO CRÍTICO NA INICIALIZAÇÃO: {e}", exc_info=True)
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Erro Crítico", f"Falha ao iniciar a aplicação:\n\n{e}")
        root.destroy()


if __name__ == "__main__":
    main()
