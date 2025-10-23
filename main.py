# main.py

import tkinter as tk
from tkinter import ttk, messagebox
import logging
import os
import sys

# Adiciona o diretório raiz ao path para garantir que os imports funcionem
# quando executado como script.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# --- Configurar o logger como a PRIMEIRA ação ---
try:
    from core.logger_config import setup_logging

    setup_logging()
except (ImportError, ModuleNotFoundError):
    logging.basicConfig(level=logging.INFO)
    logging.warning(
        "Módulo 'core.logger_config' não encontrado. Usando configuração de log básica."
    )

# --- Imports da aplicação ---
from app.lib.mappers import codigoMapper
from app.services.serviço_207.form_207 import Gerador207Frame

# MUDANÇA 1: Importar o FerramentaSOAPFrame refatorado
from app.services.soap.form_ferramentasoap import FerramentaSOAPFrame


class AppController(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logging.info("Inicializando o controlador principal da aplicação.")

        # --- 1. Configuração da Janela Principal (Padrão para toda a app) ---
        self.title("Pytegrator")

        # Tamanho padrão para todas as telas
        largura_padrao = 900
        altura_padrao = 680  # Ajustado para acomodar melhor a tela SOAP

        self.geometry(f"{largura_padrao}x{altura_padrao}")
        self.resizable(False, False)  # Impede o redimensionamento

        # Centralizar na tela
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (largura_padrao // 2)
        y = (self.winfo_screenheight() // 2) - (altura_padrao // 2)
        self.geometry(f"+{x}+{y}")

        # Carregar ícone
        self._carregar_icone_app()

        # --- 2. Container para os Frames (Telas) ---
        container = ttk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        # Itera sobre as classes de Frame e as adiciona ao controlador
        for F in (MenuPrincipalFrame, Gerador207Frame, FerramentaSOAPFrame):
            frame_name = F.__name__.replace("Frame", "")  # Ex: "MenuPrincipal"
            frame = F(container, self)
            self.frames[frame_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("MenuPrincipal")
        logging.info("Controlador da aplicação pronto. Exibindo menu principal.")

    def show_frame(self, nome_classe):
        """Eleva o frame solicitado para o topo, tornando-o visível."""
        logging.info(f"Transicionando para a tela: {nome_classe}")
        frame = self.frames[nome_classe]
        frame.tkraise()

    def _carregar_icone_app(self):
        """Carrega o ícone principal da janela."""
        icon_path = os.path.join("app", "assets", "icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
                logging.info("Ícone da janela carregado.")
            except tk.TclError:
                logging.warning("Não foi possível carregar o ícone 'icon.ico'.")


class MenuPrincipalFrame(ttk.Frame):
    """O Frame que representa o Menu Principal."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self._configurar_estilos()
        self._criar_layout_principal()

        self.icon_soap = self._carregar_icone("soap_icon.png")
        self.icon_xml = self._carregar_icone("xml_icon.png")

        self._criar_widgets_menu()
        logging.info("Widgets do MenuPrincipalFrame criados com sucesso.")

    def _configurar_estilos(self):
        style = ttk.Style(self)
        style.configure(
            "Menu.TButton",
            font=("Segoe UI", 12),
            padding=(20, 15),
            anchor="w",
            background="#ffffff",
            borderwidth=1,
            relief="solid",
            bordercolor="#cccccc",
        )
        style.map(
            "Menu.TButton",
            background=[("active", "#e5f1fb")],
            bordercolor=[("active", "#0078d4")],
        )
        style.configure("Inner.TFrame", background="#ffffff")
        style.configure("Inner.TLabel", background="#ffffff")
        style.configure("Menu.TFrame", background="#f0f0f0")

    def _criar_layout_principal(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        title_bar = tk.Label(
            self,
            text="Menu de Ferramentas",
            bg="#005a9e",
            fg="white",
            font=("Helvetica", 12, "bold"),
            padx=10,
            pady=5,
            anchor="w",
        )
        title_bar.grid(row=0, column=0, sticky="ew")

        main_content = ttk.Frame(self, style="Menu.TFrame", padding="20")
        main_content.grid(row=1, column=0, sticky="nsew")
        self.main_content = main_content

    def _criar_widgets_menu(self):
        title_label = ttk.Label(
            self.main_content,
            text="Ferramentas Disponíveis",
            font=("Segoe UI", 18, "bold"),
            background="#f0f0f0",
            foreground="#333333",
        )
        title_label.pack(pady=(0, 25), anchor="w")

        self.create_menu_button(
            self.main_content,
            "Gerador de XML - Serviço 207",
            "Criar um arquivo XML para integração de agentes ao Mega ERP.",
            lambda: self.controller.show_frame("Gerador207"),
            self.icon_xml,
        )
        # MUDANÇA 2: O comando do botão agora chama o frame da ferramenta SOAP
        self.create_menu_button(
            self.main_content,
            "Ferramenta de Integração SOAP",
            "Realizar envio de XML a um endpoint.",
            lambda: self.controller.show_frame("FerramentaSOAP"),
            self.icon_soap,
        )

    def create_menu_button(self, parent, title, description, command, icon=None):
        button = ttk.Button(parent, command=command, style="Menu.TButton")
        button.pack(fill="x", pady=4)
        inner_frame = ttk.Frame(button, style="Inner.TFrame")
        inner_frame.pack(fill="x", expand=True, padx=10, pady=5)
        inner_frame.bind("<Button-1>", lambda e: button.invoke())
        if icon:
            icon_label = ttk.Label(inner_frame, image=icon, style="Inner.TLabel")
            icon_label.pack(side="left", padx=(0, 15))
            icon_label.bind("<Button-1>", lambda e: button.invoke())
        text_frame = ttk.Frame(inner_frame, style="Inner.TFrame")
        text_frame.pack(side="left", fill="x", expand=True)
        text_frame.bind("<Button-1>", lambda e: button.invoke())
        title_label = ttk.Label(
            text_frame,
            text=title,
            font=("Segoe UI", 11, "bold"),
            style="Inner.TLabel",
            anchor="w",
        )
        title_label.pack(fill="x")
        title_label.bind("<Button-1>", lambda e: button.invoke())
        desc_label = ttk.Label(
            text_frame,
            text=description,
            font=("Segoe UI", 9),
            style="Inner.TLabel",
            foreground="#555555",
            anchor="w",
        )
        desc_label.pack(fill="x", pady=(2, 0))
        desc_label.bind("<Button-1>", lambda e: button.invoke())

    def _carregar_icone(self, nome_arquivo):
        path = os.path.join("app", "assets", nome_arquivo)
        try:
            return tk.PhotoImage(file=path) if os.path.exists(path) else None
        except tk.TclError:
            return None


# --- Ponto de Entrada da Aplicação ---
if __name__ == "__main__":
    try:
        logging.info("Aplicação iniciada. Carregando recursos...")
        codigoMapper.carregar_mapa_codigos()
        logging.info("Mapa de códigos carregado com sucesso.")

        app = AppController()
        app.mainloop()
        logging.info("Aplicação encerrada normalmente.")

    except Exception as e:
        logging.critical(f"ERRO CRÍTICO NA INICIALIZAÇÃO: {e}", exc_info=True)
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Erro Crítico",
            f"Falha ao iniciar a aplicação:\n\n{e}\n\nVerifique o 'app.log'.",
        )
