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

from tkinter import messagebox
import customtkinter as ctk

from app.ui.theme import (
    COLOR_BG,
    COLOR_SURFACE,
    COLOR_SURFACE_ALT,
    COLOR_BORDER,
    COLOR_TEXT,
    COLOR_TEXT_MUTED,
    COLOR_ACCENT,
    COLOR_ACCENT_HOVER,
    COLOR_SUCCESS,
    COLOR_ERROR,
    COLOR_HOVER,
    FONT_SM,
)


class ResultadoFrame(ctk.CTkFrame):
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
        super().__init__(parent, fg_color=COLOR_BG)
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
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=16)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)

        # Barra de título
        title_bar = ctk.CTkLabel(
            container,
            text="XML Gerado com Sucesso",
            fg_color=COLOR_SURFACE,
            corner_radius=10,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLOR_TEXT,
            anchor="w",
        )
        title_bar.grid(row=0, column=0, sticky="ew", pady=(0, 10), padx=0, ipady=10)

        # Área de texto
        self.xml_text = ctk.CTkTextbox(
            container,
            fg_color=COLOR_SURFACE_ALT,
            border_color=COLOR_BORDER,
            border_width=1,
            text_color=COLOR_TEXT,
            wrap="word",
            font=ctk.CTkFont(family="Consolas", size=10),
            corner_radius=10,
        )
        self.xml_text.grid(row=1, column=0, sticky="nsew")
        self.xml_text.configure(state="disabled")

        # Label de feedback (ex.: “copiado com sucesso” ou avisos discretos)
        self.copiado_label = ctk.CTkLabel(
            container,
            text="",
            text_color=COLOR_SUCCESS,
            anchor="w",
            font=ctk.CTkFont(size=FONT_SM),
        )
        self.copiado_label.grid(row=2, column=0, sticky="w", padx=5, pady=(5, 0))

        # Barra de botões (direita)
        button_frame = ctk.CTkFrame(container, fg_color="transparent")
        button_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))

        # OBS: botão "Voltar ao Menu" foi removido conforme solicitado.

        # Voltar ao gerador (tela anterior)
        self.voltar_gerador_button = ctk.CTkButton(
            button_frame,
            height=34,
            text="Voltar à Geração do XML",
            fg_color=COLOR_SURFACE,
            hover_color=COLOR_HOVER,
            border_width=1,
            border_color=COLOR_BORDER,
            text_color=COLOR_TEXT_MUTED,
            font=ctk.CTkFont(size=FONT_SM),
        )
        self.voltar_gerador_button.pack(side="right", padx=(5, 0))

        # Copiar XML
        self.copiar_button = ctk.CTkButton(
            button_frame,
            height=34,
            text="Copiar XML",
            fg_color=COLOR_SURFACE,
            hover_color=COLOR_HOVER,
            border_width=1,
            border_color=COLOR_BORDER,
            text_color=COLOR_TEXT_MUTED,
            font=ctk.CTkFont(size=FONT_SM),
        )
        self.copiar_button.pack(side="right", padx=(5, 0))

        # Copiar e ir para a integração SOAP
        self.copiar_e_integrar_button = ctk.CTkButton(
            button_frame,
            height=34,
            text="Copiar XML e ir para Integração",
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            text_color="white",
            font=ctk.CTkFont(size=FONT_SM, weight="bold"),
        )
        self.copiar_e_integrar_button.pack(side="right")

    # ------------------------------------------------------------------ #
    # Conexão de eventos / atalhos
    # ------------------------------------------------------------------ #
    def _configurar_eventos(self) -> None:
        """Associa callbacks aos botões e define as rotas de navegação."""
        self.copiar_button.configure(command=self.copiar_xml)
        self.voltar_gerador_button.configure(
            command=lambda: self.controller.show_frame("Gerador207")
        )
        self.copiar_e_integrar_button.configure(command=self.copiar_e_integrar)

    def _bind_shortcuts(self) -> None:
        """
        Registra atalhos de teclado úteis:
          - Ctrl/Cmd + C: copiar XML
          - Ctrl/Cmd + I: copiar e abrir integração SOAP
        """
        # CTk widgets bloqueiam bind_all; usamos bind no toplevel com add="+"
        target = self.winfo_toplevel()

        for seq in ("<Control-c>", "<Control-C>", "<Command-c>", "<Command-C>"):
            target.bind(seq, self._on_copy_shortcut, add="+")

        for seq in ("<Control-i>", "<Control-I>", "<Command-i>", "<Command-I>"):
            target.bind(seq, self._on_integrate_shortcut, add="+")

    def _on_copy_shortcut(self, _event=None):
        """Atalho de cópia ativo apenas quando esta tela está visível."""
        if not self.winfo_viewable():
            return None
        self.copiar_xml()
        return "break"

    def _on_integrate_shortcut(self, _event=None):
        """Atalho de integração ativo apenas quando esta tela está visível."""
        if not self.winfo_viewable():
            return None
        self.copiar_e_integrar()
        return "break"

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
        self.copiado_label.configure(text="", text_color=COLOR_SUCCESS)

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
            self.copiado_label.configure(text="Nenhum XML para copiar.", text_color=COLOR_ERROR)
            self.after(
                2500, lambda: self.copiado_label.configure(text="", text_color=COLOR_SUCCESS)
            )
            return

        try:
            # Manipula a área de transferência da janela
            self.clipboard_clear()
            self.clipboard_append(self.xml_string)
            self.update_idletasks()

            if show_message:
                self.copiado_label.configure(text="XML copiado com sucesso!", text_color=COLOR_SUCCESS)
                # Limpa feedback após alguns segundos
                self.after(2500, lambda: self.copiado_label.configure(text=""))

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
    def _set_text_content(text_widget: ctk.CTkTextbox, content: str) -> None:
        """
        Helper para atualizar um CTkTextbox preservando a imutabilidade externa.

        - Coloca o widget em 'normal', altera o conteúdo e volta para 'disabled'.
        - Evita repetição desse padrão em vários pontos do código.

        Args:
            text_widget: instância de CTkTextbox a ser atualizada.
            content: texto que será inserido (string).
        """
        # CTkTextbox não expõe cget("state") na API pública; usa o Text interno.
        base_text = getattr(text_widget, "_textbox", None)
        if base_text is None:
            # Fallback defensivo raro: tenta atualizar sem preservar estado.
            text_widget.configure(state="normal")
            text_widget.delete("1.0", "end")
            text_widget.insert("1.0", content or "")
            text_widget.configure(state="disabled")
            return

        prev = str(base_text.cget("state"))
        previous_state_literal = "normal" if prev == "normal" else "disabled"
        try:
            text_widget.configure(state="normal")
            text_widget.delete("1.0", "end")
            text_widget.insert("1.0", content or "")
        finally:
            # Retorna ao estado anterior (garantido como 'normal' ou 'disabled')
            text_widget.configure(state=previous_state_literal)
