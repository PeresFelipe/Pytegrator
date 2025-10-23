# main.py

import tkinter as tk
from tkinter import ttk, font, messagebox
import logging
import os

# --- Configurar o logger como a PRIMEIRA ação ---
try:
    from core.logger_config import setup_logging

    setup_logging()
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logging.warning(
        "Módulo 'core.logger_config' não encontrado. Usando configuração de log básica."
    )

# --- O resto dos imports da aplicação ---
from app.lib.mappers import codigoMapper
from app.services.serviço_207.form_207 import Gerador207Window

# --- MUDANÇA 1: Importar a nova classe da ferramenta SOAP ---
from app.services.soap.form_ferramentasoap import FerramentaSOAPWindow


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        logging.info("Inicializando a janela principal (MainWindow).")

        # --- 1. Configuração da Janela Principal ---
        self.title("Menu de Ferramentas")
        self.minsize(600, 450)

        icon_path = os.path.join("app", "assets", "icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
                logging.info("Ícone da janela carregado.")
            except tk.TclError:
                logging.warning(
                    "Não foi possível carregar o ícone 'icon.ico'. Formato inválido?"
                )

        self.withdraw()
        self.update_idletasks()
        width = 800
        height = 600
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.deiconify()
        self.configure(bg="#f0f0f0")

        # --- 2. Estilos e Fontes ---
        style = ttk.Style(self)
        style.theme_use("clam")

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
        style.configure("Main.TFrame", background=self.cget("bg"))

        # --- 3. Criação do Layout Central ---
        main_frame = ttk.Frame(self, padding=(20, 10), style="Main.TFrame")
        main_frame.pack(fill="both", expand=True)

        # --- 4. Título ---
        title_label = ttk.Label(
            main_frame,
            text="Ferramentas Disponíveis",
            font=("Segoe UI", 18, "bold"),
            background=self.cget("bg"),
            foreground="#333333",
        )
        title_label.pack(pady=(10, 25), anchor="w")

        # --- 5. Criação dos Botões de Menu ---
        self.icon_soap = self._carregar_icone("soap_icon.png")
        self.icon_xml = self._carregar_icone("xml_icon.png")

        self.create_menu_button(
            main_frame,
            title="Ferramenta de Integração SOAP",
            description="Realizar envio de XML a um endpoint.",
            command=self.open_soap_tool,
            icon=self.icon_soap,
        )
        self.create_menu_button(
            main_frame,
            title="Gerador de XML - Serviço 207",
            description="Criar um arquivo XML para integração de agentes ao Mega ERP.",
            command=self.open_gerador_207_tool,
            icon=self.icon_xml,
        )
        logging.info("Widgets da MainWindow criados com sucesso.")

    def _carregar_icone(self, nome_arquivo):
        """Função auxiliar para carregar ícones da pasta assets."""
        path = os.path.join("app", "assets", nome_arquivo)
        try:
            if os.path.exists(path):
                return tk.PhotoImage(file=path)
            else:
                logging.warning(f"Arquivo de ícone não encontrado: {path}")
                return None
        except tk.TclError:
            logging.error(
                f"Erro ao carregar a imagem '{nome_arquivo}'. O formato é suportado?"
            )
            return None

    def create_menu_button(self, parent, title, description, command, icon=None):
        """Cria um botão de menu moderno com título, descrição e ícone."""
        button = ttk.Button(parent, command=command, style="Menu.TButton")
        button.pack(fill="x", pady=4)

        inner_frame = ttk.Frame(button, style="Menu.TButton")
        inner_frame.pack(fill="x", expand=True, padx=10, pady=5)

        if icon:
            icon_label = ttk.Label(inner_frame, image=icon, style="Menu.TButton")
            icon_label.pack(side="left", padx=(0, 15))
            icon_label.bind("<Button-1>", lambda e: button.invoke())

        text_frame = ttk.Frame(inner_frame, style="Menu.TButton")
        text_frame.pack(side="left", fill="x", expand=True)

        title_label = ttk.Label(
            text_frame,
            text=title,
            font=("Segoe UI", 11, "bold"),
            style="Menu.TButton",
            anchor="w",
        )
        title_label.pack(fill="x")

        desc_label = ttk.Label(
            text_frame,
            text=description,
            font=("Segoe UI", 9),
            style="Menu.TButton",
            foreground="#555555",
            anchor="w",
        )
        desc_label.pack(fill="x", pady=(2, 0))

        title_label.bind("<Button-1>", lambda e: button.invoke())
        desc_label.bind("<Button-1>", lambda e: button.invoke())

    # --- MUDANÇA 2: Atualizar a função para abrir a ferramenta SOAP ---
    def open_soap_tool(self):
        """Abre a janela da ferramenta SOAP, escondendo o menu principal."""
        logging.info("Abrindo a janela da Ferramenta SOAP...")
        try:
            self.withdraw()
            janela_soap = FerramentaSOAPWindow(self)
            janela_soap.grab_set()
            self.wait_window(janela_soap)
            logging.info("Janela da Ferramenta SOAP foi fechada.")
        except Exception as e:
            logging.error(f"Falha ao abrir a Ferramenta SOAP. Erro: {e}", exc_info=True)
            messagebox.showerror(
                "Erro na Ferramenta",
                "Ocorreu um erro na ferramenta SOAP.\n\nConsulte o 'app.log'.",
            )
        finally:
            logging.info("Restaurando a janela do menu principal.")
            self.deiconify()
            self.lift()

    def open_gerador_207_tool(self):
        """Cria e exibe a janela da ferramenta Gerador 207."""
        if (
            hasattr(self, "janela_gerador_ativa")
            and self.janela_gerador_ativa.winfo_exists()
        ):
            logging.warning(
                "Tentativa de abrir a janela do Gerador 207, mas ela já está aberta."
            )
            self.janela_gerador_ativa.lift()
            return

        logging.info("Abrindo a janela do Gerador 207...")
        try:
            self.withdraw()
            self.janela_gerador_ativa = Gerador207Window(self)
            self.janela_gerador_ativa.grab_set()
            self.wait_window(self.janela_gerador_ativa)
            logging.info("Janela do Gerador 207 foi fechada.")
        except Exception as e:
            logging.error(
                f"Falha ao abrir ou aguardar a janela do Gerador 207. Erro: {e}",
                exc_info=True,
            )
            messagebox.showerror(
                "Erro na Ferramenta",
                "Ocorreu um erro na ferramenta Gerador 207.\n\nConsulte o 'app.log'.",
            )
        finally:
            logging.info("Restaurando a janela do menu principal.")
            self.deiconify()
            self.lift()


# --- Ponto de Entrada da Aplicação ---
if __name__ == "__main__":
    try:
        logging.info("Aplicação iniciada. Carregando recursos...")
        codigoMapper.carregar_mapa_codigos()
        logging.info("Mapa de códigos carregado com sucesso.")

        app = MainWindow()
        app.mainloop()
        logging.info("Aplicação encerrada normalmente.")

    except Exception as e:
        logging.critical(f"ERRO CRÍTICO NA INICIALIZAÇÃO: {e}", exc_info=True)
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Erro Crítico na Inicialização",
            f"Falha ao iniciar a aplicação:\n\n{e}\n\nVerifique o 'app.log'.",
        )
