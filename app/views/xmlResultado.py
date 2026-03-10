# app/views/xmlResultado.py
# -*- coding: utf-8 -*-
"""
Tela de resultado para exibir o XML gerado.

Melhorias neste arquivo:
- Removido o botão "Voltar ao Menu".
- Comentários e docstrings explicando cada função e bloco.
- Otimizações leves:
  - Helper _set_text_content() para manipular o Text com segurança.
  - Atalhos de teclado (Ctrl+C para copiar, Ctrl+I para copiar e integrar).
  - Verificações defensivas ao navegar para a tela SOAP.
- Removido modal "Não há XML para copiar." — agora o feedback é discreto no label.
"""

import tkinter as tk
from tkinter import ttk, messagebox


class ResultadoFrame(ttk.Frame):
    """
    Frame responsável por exibir o XML gerado, com ações para:
      - Copiar o XML para a área de transferência.
      - Voltar à geração do XML (tela anterior).
      - Copiar o XML e abrir a ferramenta SOAP com o payload preenchido.
    """

    def __init__(self, parent, controller):
        """
        Construtor do frame.

        Args:
            parent: widget/container pai.
            controller: controlador principal da aplicação, usado para navegação
                        e acesso a outros frames (ex.: tela SOAP).
        """
        super().__init__(parent)
        self.controller = controller
        self.xml_string: str = ""  # Armazena o XML atual exibido na tela

        # Monta a interface e conecta eventos
        self._criar_widgets()
        self._configurar_eventos()
        self._bind_shortcuts()

    # ------------------------------------------------------------------ #
    # Construção da interface
    # ------------------------------------------------------------------ #
    def _criar_widgets(self) -> None:
        """Cria e posiciona todos os widgets da interface (título, editor, botões)."""
        container = ttk.Frame(self, padding="10")
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)

        # Barra de título
        title_bar = tk.Label(
            container,
            text="XML Gerado com Sucesso",
            bg="#005a9e",
            fg="white",
            font=("Helvetica", 12, "bold"),
            padx=10,
            pady=5,
            anchor="w",
        )
        title_bar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        # Área de texto + scrollbar
        text_frame = ttk.Frame(container)
        text_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")
        text_frame.rowconfigure(0, weight=1)
        text_frame.columnconfigure(0, weight=1)

        self.xml_text = tk.Text(
            text_frame,
            wrap="word",
            font=("Consolas", 10),
            padx=5,
            pady=5,
            borderwidth=1,
            relief="solid",
        )
        self.xml_text.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(
            text_frame, orient="vertical", command=self.xml_text.yview
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.xml_text.config(yscrollcommand=scrollbar.set)

        # Label de feedback (ex.: “copiado com sucesso” ou avisos discretos)
        self.copiado_label = ttk.Label(container, text="", foreground="green")
        self.copiado_label.grid(row=2, column=0, sticky="w", padx=5, pady=(5, 0))

        # Barra de botões (direita)
        button_frame = ttk.Frame(container)
        button_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        # OBS: botão "Voltar ao Menu" foi removido conforme solicitado.

        # Voltar ao gerador (tela anterior)
        self.voltar_gerador_button = ttk.Button(
            button_frame, text="Voltar à Geração do XML"
        )
        self.voltar_gerador_button.pack(side="right", padx=(5, 0))

        # Copiar XML
        self.copiar_button = ttk.Button(button_frame, text="Copiar XML")
        self.copiar_button.pack(side="right", padx=(5, 0))

        # Copiar e ir para a integração SOAP
        self.copiar_e_integrar_button = ttk.Button(
            button_frame,
            text="Copiar XML e ir para Integração",
            style="Accent.TButton",
        )
        self.copiar_e_integrar_button.pack(side="right")

    # ------------------------------------------------------------------ #
    # Conexão de eventos / atalhos
    # ------------------------------------------------------------------ #
    def _configurar_eventos(self) -> None:
        """Associa callbacks aos botões e define as rotas de navegação."""
        self.copiar_button.config(command=self.copiar_xml)
        self.voltar_gerador_button.config(
            command=lambda: self.controller.show_frame("Gerador207")
        )
        self.copiar_e_integrar_button.config(command=self.copiar_e_integrar)

    def _bind_shortcuts(self) -> None:
        """
        Registra atalhos de teclado úteis:
          - Ctrl/Cmd + C: copiar XML
          - Ctrl/Cmd + I: copiar e abrir integração SOAP
        """
        # Suporte Windows/Linux (Control) e macOS (Command/Meta)
        self.bind_all("<Control-c>", lambda e: self.copiar_xml())
        self.bind_all("<Control-C>", lambda e: self.copiar_xml())
        self.bind_all("<Command-c>", lambda e: self.copiar_xml())
        self.bind_all("<Command-C>", lambda e: self.copiar_xml())

        self.bind_all("<Control-i>", lambda e: self.copiar_e_integrar())
        self.bind_all("<Control-I>", lambda e: self.copiar_e_integrar())
        self.bind_all("<Command-i>", lambda e: self.copiar_e_integrar())
        self.bind_all("<Command-I>", lambda e: self.copiar_e_integrar())

    # ------------------------------------------------------------------ #
    # API pública do frame
    # ------------------------------------------------------------------ #
    def set_xml(self, xml_string: str) -> None:
        """
        Recebe o XML gerado por outra tela e atualiza a exibição.

        Args:
            xml_string: conteúdo XML a ser mostrado ao usuário.
        """
        self.xml_string = xml_string or ""
        # Atualiza a área de texto de forma segura (trava/destrava estado)
        self._set_text_content(
            self.xml_text,
            (
                self.xml_string
                if self.xml_string
                else "Nenhum XML foi gerado ou recebido."
            ),
        )
        # Limpa mensagens de feedback anteriores
        self.copiado_label.config(text="", foreground="green")

    # ------------------------------------------------------------------ #
    # Ações de UI
    # ------------------------------------------------------------------ #
    def copiar_xml(self, show_message: bool = True) -> None:
        """
        Copia o XML atual para a área de transferência.

        Args:
            show_message: se True, exibe feedback "copiado com sucesso".
        """
        if not self.xml_string:
            # Sem modal: feedback discreto na própria tela
            self.copiado_label.config(
                text="Nenhum XML para copiar.", foreground="#A94442"
            )
            self.after(
                2500, lambda: self.copiado_label.config(text="", foreground="green")
            )
            return

        try:
            # Manipula a área de transferência da janela
            self.clipboard_clear()
            self.clipboard_append(self.xml_string)
            self.update_idletasks()

            if show_message:
                self.copiado_label.config(
                    text="XML copiado com sucesso!", foreground="green"
                )
                # Limpa feedback após alguns segundos
                self.after(2500, lambda: self.copiado_label.config(text=""))

        except Exception as e:
            messagebox.showerror("Erro de Cópia", f"Não foi possível copiar o XML: {e}")

    def copiar_e_integrar(self) -> None:
        """Copia o XML e navega para a ferramenta SOAP já com o payload preenchido."""
        # Copia silenciosamente (sem label de feedback adicional aqui)
        self.copiar_xml(show_message=False)

        # Recupera a tela SOAP pelo controller
        soap_frame = self.controller.frames.get("FerramentaSOAP")

        # Verificação defensiva: se a tela existe e tem o método esperado
        if soap_frame and hasattr(soap_frame, "preencher_payload"):
            # Preenche o payload na tela SOAP e navega até ela
            try:
                soap_frame.preencher_payload(
                    xml_string=self.xml_string, cod_servico="207"
                )
            except Exception as e:
                messagebox.showerror(
                    "Erro", f"Falha ao preparar a integração SOAP:\n{e}"
                )
                return

            self.controller.show_frame("FerramentaSOAP")
        else:
            messagebox.showerror(
                "Erro", "A tela da ferramenta SOAP não foi encontrada."
            )

    # ------------------------------------------------------------------ #
    # Utilidades
    # ------------------------------------------------------------------ #
    @staticmethod
    def _set_text_content(text_widget: tk.Text, content: str) -> None:
        """
        Helper para atualizar um tk.Text preservando a imutabilidade externa.

        - Coloca o widget em 'normal', altera o conteúdo e volta para 'disabled'.
        - Evita repetição desse padrão em vários pontos do código.

        Args:
            text_widget: instância de tk.Text a ser atualizada.
            content: texto que será inserido (string).
        """
        # Captura o estado anterior e garante um valor compatível com o tipo Literal
        prev = str(text_widget.cget("state"))
        previous_state_literal = "normal" if prev == "normal" else "disabled"
        try:
            text_widget.config(state="normal")
            text_widget.delete("1.0", "end")
            text_widget.insert("1.0", content or "")
        finally:
            # Retorna ao estado anterior (garantido como 'normal' ou 'disabled')
            text_widget.config(state=previous_state_literal)
