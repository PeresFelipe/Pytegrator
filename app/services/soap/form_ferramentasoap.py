# app/services/soap/form_ferramentasoap.py
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import threading
import time
import requests
import xml.etree.ElementTree as ET
from html import escape
from xml.dom import minidom
import xml.parsers.expat

from app.ui.theme import (
    COLOR_BG, COLOR_SURFACE, COLOR_SURFACE_ALT, COLOR_HOVER,
    COLOR_BORDER, COLOR_TEXT, COLOR_TEXT_MUTED,
    COLOR_ACCENT, COLOR_ACCENT_HOVER,
    FONT_SM, FONT_MD,
)


class FerramentaSOAPFrame(ctk.CTkFrame):
    """
    Frame da ferramenta de envio de requisições SOAP em lote.
    Responsabilidades:
      - Montar a interface de configuração e envio.
      - Validar parâmetros digitados pelo usuário.
      - Enfileirar envios em thread para não travar a UI.
      - Apresentar progresso, logs e visualizar o XML de retorno.
    """

    def __init__(self, parent, controller):
        """
        Construtor do frame.

        Args:
            parent: widget pai onde o frame será acoplado.
            controller: controlador principal (janela/root) para navegar/compartilhar dados (mantido por compatibilidade).
        """
        super().__init__(parent, fg_color=COLOR_BG)
        self.controller = controller
        # Evento usado para sinalizar interrupção segura do processo em thread
        self.deve_interromper = threading.Event()
        # Cria e posiciona todos os widgets da interface
        self._criar_widgets()

    def _criar_widgets(self):
        """
        Cria e organiza todos os widgets da interface gráfica.
        """
        # Layout: 6 linhas, coluna única
        self.grid_rowconfigure(3, weight=1)  # payload expande
        self.grid_rowconfigure(4, weight=2)  # logs expande mais
        self.grid_columnconfigure(0, weight=1)

        # ---- Título ----
        ctk.CTkLabel(
            self,
            text="Ferramenta de Integração SOAP",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLOR_TEXT,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 0))

        # ---- Configuração do Envio ----
        config_outer = ctk.CTkFrame(
            self, fg_color=COLOR_SURFACE, corner_radius=8,
            border_width=1, border_color=COLOR_BORDER,
        )
        config_outer.grid(row=1, column=0, sticky="ew", padx=16, pady=(12, 0))
        ctk.CTkLabel(
            config_outer, text="Configuração do Envio",
            font=ctk.CTkFont(size=FONT_SM), text_color=COLOR_TEXT_MUTED, anchor="w",
        ).pack(anchor="w", padx=12, pady=(8, 4))
        config_frame = ctk.CTkFrame(config_outer, fg_color="transparent")
        config_frame.pack(fill="x", padx=10, pady=(0, 10))
        config_frame.columnconfigure(1, weight=1)
        config_frame.columnconfigure(4, weight=1)

        ctk.CTkLabel(
            config_frame, text="Computador/URL Integrador:",
            font=ctk.CTkFont(size=FONT_SM), text_color=COLOR_TEXT_MUTED,
        ).grid(row=0, column=0, sticky="w", padx=(0, 6), pady=4)
        self.url_base_entry = ctk.CTkEntry(
            config_frame, width=260,
            fg_color=COLOR_SURFACE_ALT, border_color=COLOR_BORDER, text_color=COLOR_TEXT,
        )
        self.url_base_entry.insert(0, "localhost")
        self.url_base_entry.grid(row=0, column=1, sticky="w", padx=(0, 12), pady=4)

        ctk.CTkLabel(
            config_frame, text="Porta Integrador:",
            font=ctk.CTkFont(size=FONT_SM), text_color=COLOR_TEXT_MUTED,
        ).grid(row=0, column=2, sticky="w", padx=(0, 6), pady=4)
        self.port_entry = ctk.CTkEntry(
            config_frame, width=80,
            fg_color=COLOR_SURFACE_ALT, border_color=COLOR_BORDER, text_color=COLOR_TEXT,
        )
        self.port_entry.insert(0, "8110")
        self.port_entry.grid(row=0, column=3, sticky="w", padx=(0, 12), pady=4)

        ctk.CTkLabel(
            config_frame, text="Número de Envios:",
            font=ctk.CTkFont(size=FONT_SM), text_color=COLOR_TEXT_MUTED,
        ).grid(row=1, column=0, sticky="w", padx=(0, 6), pady=4)
        self.repetitions_entry = ctk.CTkEntry(
            config_frame, width=80,
            fg_color=COLOR_SURFACE_ALT, border_color=COLOR_BORDER, text_color=COLOR_TEXT,
        )
        self.repetitions_entry.insert(0, "1")
        self.repetitions_entry.grid(row=1, column=1, sticky="w", pady=4)

        # ---- Parâmetros da Requisição ----
        params_outer = ctk.CTkFrame(
            self, fg_color=COLOR_SURFACE, corner_radius=8,
            border_width=1, border_color=COLOR_BORDER,
        )
        params_outer.grid(row=2, column=0, sticky="ew", padx=16, pady=(10, 0))
        ctk.CTkLabel(
            params_outer, text="Parâmetros da Requisição",
            font=ctk.CTkFont(size=FONT_SM), text_color=COLOR_TEXT_MUTED, anchor="w",
        ).pack(anchor="w", padx=12, pady=(8, 4))
        params_frame = ctk.CTkFrame(params_outer, fg_color="transparent")
        params_frame.pack(fill="x", padx=10, pady=(0, 10))
        params_frame.columnconfigure(4, weight=1)

        # Validadores (callbacks de Tk) para limitar tamanho/entrada
        vcmd_num_4  = (self.register(self._validate_numeric_input), "%P", "4")
        vcmd_num_6  = (self.register(self._validate_numeric_input), "%P", "6")
        vcmd_num_3  = (self.register(self._validate_numeric_input), "%P", "3")
        vcmd_char_50 = (self.register(self._validate_char_input),   "%P", "50")

        ctk.CTkLabel(
            params_frame, text="Cód. Serviço:",
            font=ctk.CTkFont(size=FONT_SM), text_color=COLOR_TEXT_MUTED,
        ).grid(row=0, column=0, sticky="w", padx=(0, 6), pady=4)
        self.pro_id_entry = ctk.CTkEntry(
            params_frame, width=80,
            fg_color=COLOR_SURFACE_ALT, border_color=COLOR_BORDER, text_color=COLOR_TEXT,
            validate="key", validatecommand=vcmd_num_4,
        )
        self.pro_id_entry.insert(0, "0000")
        self.pro_id_entry.grid(row=0, column=1, sticky="w", padx=(0, 16), pady=4)

        ctk.CTkLabel(
            params_frame, text="Cód. Usuário:",
            font=ctk.CTkFont(size=FONT_SM), text_color=COLOR_TEXT_MUTED,
        ).grid(row=0, column=2, sticky="w", padx=(0, 6), pady=4)
        self.usu_codigo_entry = ctk.CTkEntry(
            params_frame, width=80,
            fg_color=COLOR_SURFACE_ALT, border_color=COLOR_BORDER, text_color=COLOR_TEXT,
            validate="key", validatecommand=vcmd_num_4,
        )
        self.usu_codigo_entry.insert(0, "0001")
        self.usu_codigo_entry.grid(row=0, column=3, sticky="w", pady=4)

        ctk.CTkLabel(
            params_frame, text="Cód. Transação:",
            font=ctk.CTkFont(size=FONT_SM), text_color=COLOR_TEXT_MUTED,
        ).grid(row=1, column=0, sticky="w", padx=(0, 6), pady=4)
        self.transacao_entry = ctk.CTkEntry(
            params_frame, width=80,
            fg_color=COLOR_SURFACE_ALT, border_color=COLOR_BORDER, text_color=COLOR_TEXT,
            validate="key", validatecommand=vcmd_num_6,
        )
        self.transacao_entry.insert(0, "0")
        self.transacao_entry.grid(row=1, column=1, sticky="w", padx=(0, 16), pady=4)

        ctk.CTkLabel(
            params_frame, text="Cód. Sistema:",
            font=ctk.CTkFont(size=FONT_SM), text_color=COLOR_TEXT_MUTED,
        ).grid(row=1, column=2, sticky="w", padx=(0, 6), pady=4)
        self.sistema_entry = ctk.CTkEntry(
            params_frame, width=80,
            fg_color=COLOR_SURFACE_ALT, border_color=COLOR_BORDER, text_color=COLOR_TEXT,
            validate="key", validatecommand=vcmd_num_3,
        )
        self.sistema_entry.insert(0, "001")
        self.sistema_entry.grid(row=1, column=3, sticky="w", pady=4)

        ctk.CTkLabel(
            params_frame, text="Obs:",
            font=ctk.CTkFont(size=FONT_SM), text_color=COLOR_TEXT_MUTED,
        ).grid(row=2, column=0, sticky="w", padx=(0, 6), pady=4)
        self.obs_entry = ctk.CTkEntry(
            params_frame,
            fg_color=COLOR_SURFACE_ALT, border_color=COLOR_BORDER, text_color=COLOR_TEXT,
            validate="key", validatecommand=vcmd_char_50,
        )
        self.obs_entry.grid(row=2, column=1, columnspan=3, sticky="ew", pady=4)

        # ---- XML Envio ----
        payload_outer = ctk.CTkFrame(
            self, fg_color=COLOR_SURFACE, corner_radius=8,
            border_width=1, border_color=COLOR_BORDER,
        )
        payload_outer.grid(row=3, column=0, sticky="nsew", padx=16, pady=(10, 0))
        payload_outer.grid_rowconfigure(1, weight=1)
        payload_outer.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            payload_outer, text="XML Envio",
            font=ctk.CTkFont(size=FONT_SM), text_color=COLOR_TEXT_MUTED, anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(8, 4))
        self.payload_text = ctk.CTkTextbox(
            payload_outer,
            font=ctk.CTkFont(family="Consolas", size=10),
            fg_color=COLOR_SURFACE_ALT, border_color=COLOR_BORDER, border_width=1,
            text_color=COLOR_TEXT, wrap="word",
        )
        self.payload_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        # ---- Progresso e Logs ----
        log_outer = ctk.CTkFrame(
            self, fg_color=COLOR_SURFACE, corner_radius=8,
            border_width=1, border_color=COLOR_BORDER,
        )
        log_outer.grid(row=4, column=0, sticky="nsew", padx=16, pady=(10, 0))
        log_outer.grid_rowconfigure(1, weight=1)
        log_outer.grid_columnconfigure(0, weight=1)
        log_outer.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            log_outer, text="Progresso e Logs",
            font=ctk.CTkFont(size=FONT_SM), text_color=COLOR_TEXT_MUTED, anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(8, 4))
        self.progress_label = ctk.CTkLabel(
            log_outer, text="",
            font=ctk.CTkFont(size=FONT_SM), text_color=COLOR_TEXT_MUTED, anchor="e",
        )
        self.progress_label.grid(row=0, column=1, sticky="e", padx=12, pady=(8, 4))

        self.log_text = ctk.CTkTextbox(
            log_outer,
            font=ctk.CTkFont(family="Consolas", size=10),
            fg_color=COLOR_SURFACE_ALT, border_color=COLOR_BORDER, border_width=1,
            text_color=COLOR_TEXT, wrap="word", state="disabled",
        )
        self.log_text.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=(0, 10))

        # Estilos de log via textbox interno
        self.log_text._textbox.tag_config("sucesso",      foreground="#10B981", font=("Consolas", 10, "bold"))
        self.log_text._textbox.tag_config("erro_servico", foreground="#EF4444", font=("Consolas", 10, "bold"))
        self.log_text._textbox.tag_config("erro_conexao", foreground="#EF4444", font=("Consolas", 10, "bold"))
        self.log_text._textbox.tag_config("info",     foreground="#8892A4")
        self.log_text._textbox.tag_config("response", lmargin1=10, lmargin2=10)

        # ---- Botões de Ação ----
        botoes_frame = ctk.CTkFrame(self, fg_color="transparent")
        botoes_frame.grid(row=5, column=0, sticky="ew", padx=16, pady=(12, 16))

        self.start_btn = ctk.CTkButton(
            botoes_frame,
            text="Iniciar Integração",
            height=34,
            fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
            font=ctk.CTkFont(size=FONT_SM), corner_radius=6,
            command=self._on_start_click,
        )
        self.start_btn.pack(side="left", padx=(0, 8))

        self.stop_btn = ctk.CTkButton(
            botoes_frame,
            text="Interromper",
            height=34,
            fg_color=COLOR_SURFACE, hover_color=COLOR_HOVER,
            border_width=1, border_color=COLOR_BORDER, text_color=COLOR_TEXT_MUTED,
            font=ctk.CTkFont(size=FONT_SM), corner_radius=6,
            state="disabled", command=self._on_stop_click,
        )
        self.stop_btn.pack(side="left", padx=(0, 8))

        self.view_xml_btn = ctk.CTkButton(
            botoes_frame,
            text="Visualizar XML de Retorno",
            height=34,
            fg_color=COLOR_SURFACE, hover_color=COLOR_HOVER,
            border_width=1, border_color=COLOR_BORDER, text_color=COLOR_TEXT_MUTED,
            font=ctk.CTkFont(size=FONT_SM), corner_radius=6,
            state="disabled", command=self._on_view_xml_click,
        )
        self.view_xml_btn.pack(side="left")

        # Buffer com o último XML bruto de resposta
        self.last_response_text = ""

    def _validate_numeric_input(self, new_value, max_len):
        """
        Validador para entradas numéricas com tamanho máximo.

        Args:
            new_value: valor proposto pelo Tk (conteúdo após digitação).
            max_len: comprimento máximo permitido (string, vindo do %P/%d).

        Returns:
            bool: True para aceitar a digitação, False para rejeitar.
        """
        if not new_value:
            return True
        if new_value.isdigit() and len(new_value) <= int(max_len):
            return True
        return False

    def _validate_char_input(self, new_value, max_len):
        """
        Validador para entradas de texto com tamanho máximo.

        Args:
            new_value: valor proposto pelo Tk.
            max_len: comprimento máximo permitido.

        Returns:
            bool: True se dentro do limite; caso contrário, False.
        """
        if len(new_value) <= int(max_len):
            return True
        return False

    def _construir_url_final(self):
        """
        Constrói a URL completa do endpoint SOAP a partir dos campos 'Computador/URL Integrador' e 'Porta'.

        Regras:
            - Prefixa 'http://' se usuário não informar protocolo.
            - Remove '/' à direita.
            - Acrescenta rota do serviço do integrador.

        Returns:
            str: URL completa para envio.
        """
        url_base = self.url_base_entry.get().strip()
        port = self.port_entry.get().strip()

        if not url_base.lower().startswith(("http://", "https://")):
            url_base = "http://" + url_base

        url_base = url_base.rstrip("/")
        full_url = f"{url_base}:{port}/SOAP?service=MegaIntegradorService"
        return full_url

    def _on_start_click(self):
        """
        Handler do botão "Iniciar Integração".
        - Valida entradas obrigatórias.
        - Garante ausência de conflito entre 'Transação' e 'XML Envio'.
        - Prepara variáveis de estado.
        - Dispara uma thread (daemon) para executar o processo assíncrono.
        """
        try:
            self.repetitions = int(self.repetitions_entry.get())
            self.pro_id = self.pro_id_entry.get().strip()
            self.usu_codigo = self.usu_codigo_entry.get().strip()
            self.obs = self.obs_entry.get().strip()
            self.transacao = self.transacao_entry.get().strip() or "0"
            self.sistema = self.sistema_entry.get().strip()
            self.payload_template = self.payload_text.get("1.0", "end-1c").strip()
        except ValueError:
            messagebox.showerror(
                "Erro de Validação", "O 'Número de Envios' deve ser um inteiro."
            )
            return

        # Campos obrigatórios (exceto 'Obs')
        if not all([self.pro_id, self.usu_codigo, self.transacao, self.sistema]):
            messagebox.showerror(
                "Erro de Validação",
                "Todos os campos de parâmetros, exceto 'Obs', são obrigatórios.",
            )
            return

        # Regra: serviço não pode ser '0000'
        if self.pro_id == "0000":
            messagebox.showerror(
                "Erro de Validação", "O 'Cód. Serviço' deve ser diferente de 0000."
            )
            return

        # Regras de conflito entre 'transacao' e 'payload_template'
        if self.payload_template and self.transacao != "0":
            messagebox.showerror(
                "Conflito de Parâmetros",
                "Se o 'XML Envio' for preenchido, o 'Cód. Transação' deve ser 0.",
            )
            return

        if self.transacao != "0" and self.payload_template:
            messagebox.showerror(
                "Conflito de Parâmetros",
                "Se o 'Cód. Transação' for preenchido, o 'XML Envio' deve estar vazio.",
            )
            return

        # Atualiza estado da UI para execução
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.view_xml_btn.configure(state="disabled")
        self.last_response_text = ""
        self.deve_interromper.clear()

        # Reseta logs
        self.log_text.configure(state="normal")
        self.log_text._textbox.delete("1.0", "end")
        self.log_text._textbox.insert("1.0", "Tentando comunicar...\n")
        self.log_text.configure(state="disabled")

        # Thread de trabalho (daemon) para não bloquear a UI
        self.worker_thread = threading.Thread(
            target=self._iniciar_processo, daemon=True
        )
        self.worker_thread.start()

    def _on_stop_click(self):
        """
        Handler do botão "Interromper".
        - Dispara o Event para sinalizar interrupção.
        - Desabilita o botão de interrupção enquanto a thread finaliza.
        """
        if (
            hasattr(self, "worker_thread")
            and self.worker_thread
            and self.worker_thread.is_alive()
        ):
            self.deve_interromper.set()
            self._atualizar_log("Interrupção solicitada...", tags="info")
            self.stop_btn.configure(state="disabled")

    def _iniciar_processo(self):
        """
        Loop de envios executado em thread.
        - Para cada repetição, monta o envelope SOAP e realiza POST.
        - Usa 'after' para atualizar a UI a partir da thread com segurança.
        - Trata exceções de rede e interrompe em falhas.
        """
        primeira_resposta = True

        for i in range(1, self.repetitions + 1):
            # Checa se foi solicitado parar
            if self.deve_interromper.is_set():
                self.after(
                    0,
                    lambda: self._atualizar_log(
                        "Processo interrompido pelo usuário.", tags="info"
                    ),
                )
                break

            # Atualiza a etiqueta de progresso (thread-safe com 'after')
            self.after(
                0,
                lambda i=i: self.progress_label.config(
                    text=f"Enviando {i} de {self.repetitions}..."
                ),
            )

            # Obs dinâmica por envio
            obs_final = self.obs or f"Envio #{i} pela ferramenta"

            # Envelope SOAP (com CDATA para o XML)
            envelope_soap = f"""
            <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tns="http://tempuri.org/">
                <soap:Body>
                    <tns:IntegraXMLString>
                        <pPRO_IN_ID>{self.pro_id}</pPRO_IN_ID>
                        <pUSU_IN_CODIGO>{self.usu_codigo}</pUSU_IN_CODIGO>
                        <pXML><![CDATA[{self.payload_template}]]></pXML>
                        <pXMLHeader></pXMLHeader>
                        <pObs>{escape(obs_final )}</pObs>
                        <pEnviaRecebe>R</pEnviaRecebe>
                        <pTransacao>{self.transacao}</pTransacao>
                        <pSistema>{self.sistema}</pSistema>
                    </tns:IntegraXMLString>
                </soap:Body>
            </soap:Envelope>
            """

            try:
                headers = {
                    "Content-Type": "text/xml; charset=utf-8",
                    "SOAPAction": "urn:MegaIntegradorLibrary-MegaIntegradorService#IntegraXMLString",
                }
                service_url = self._construir_url_final()
                response = requests.post(
                    service_url,
                    data=envelope_soap.encode("utf-8"),
                    headers=headers,
                    timeout=30,
                )
                response.raise_for_status()

                # Limpa o log inicial quando a primeira resposta chega
                if primeira_resposta:
                    self.after(0, self._limpar_log_inicial)
                    primeira_resposta = False

                # Agenda o processamento do retorno na thread da UI
                self.after(0, self._processar_resposta_servico, i, response.text)

            except requests.exceptions.RequestException as e:
                # Se falhar a conexão, limpa o log inicial (uma única vez)
                if primeira_resposta:
                    self.after(0, self._limpar_log_inicial)
                    primeira_resposta = False

                error_message = f"Erro de conexão: {e}"
                self.after(
                    0,
                    self._atualizar_log,
                    f"[{i}] FALHA: {error_message}",
                    ("erro_conexao",),
                )
                break

            # Pequeno intervalo para não “saturar” a UI
            time.sleep(0.1)

        # Mensagem final + reset de UI
        final_message = (
            "Processo concluído!"
            if not self.deve_interromper.is_set()
            else "Processo interrompido!"
        )
        self.after(0, lambda: self.progress_label.configure(text=final_message))
        self.after(0, self._reset_ui)

    def _limpar_log_inicial(self):
        """
        Limpa o texto inicial 'Tentando comunicar...' antes de inserir logs reais.
        """
        self.log_text.configure(state="normal")
        self.log_text._textbox.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def _processar_resposta_servico(self, index, response_text):
        """
        Interpreta a resposta do serviço:
          - Extrai o nó {http://tempuri.org/}Result.
          - Verifica se há subnó 'Erro' no XML interno.
          - Loga mensagens de sucesso/falha e um resumo (Mensagem, CodTransacao).
          - Armazena o último XML bruto para visualização.

        Args:
            index (int): Contador do envio atual.
            response_text (str): XML bruto da resposta HTTP.
        """
        self.last_response_text = response_text
        self.view_xml_btn.configure(state="normal")

        try:
            root = ET.fromstring(response_text)
            result_element = root.find(".//{http://tempuri.org/}Result")
            result_text = result_element.text if result_element is not None else None

            if result_text is None:
                self._atualizar_log(
                    f"[{index}] SUCESSO: Comunicação realizada, mas o servidor retornou uma resposta vazia.",
                    tags="sucesso",
                )
                return

            # O texto de Result costuma conter um XML "interno"
            inner_root = ET.fromstring(result_text)
            erro_element = inner_root.find("Erro")
            is_erro = (
                erro_element is not None
                and erro_element.text is not None
                and erro_element.text.lower() == "true"
            )

            if is_erro:
                self._atualizar_log(
                    f"[{index}] Comunicação realizada com sucesso. Retorno com falhas.",
                    tags="erro_servico",
                )
            else:
                self._atualizar_log(
                    f"[{index}] SUCESSO: Comunicação realizada com sucesso.",
                    tags="sucesso",
                )

            msg_element = inner_root.find("Mensagem")
            cod_element = inner_root.find("CodTransacao")

            mensagem = (
                msg_element.text
                if msg_element is not None and msg_element.text is not None
                else "N/A"
            )
            cod_transacao = (
                cod_element.text
                if cod_element is not None and cod_element.text is not None
                else "N/A"
            )

            resumo = (
                f"\n  Mensagem: {mensagem}\n  Código da Transação: {cod_transacao}\n"
            )
            self._atualizar_log(escape(resumo), tags="response")

        except (ET.ParseError, AttributeError):
            # Se a resposta não for XML válido, loga texto bruto para análise
            self._atualizar_log(
                f"[{index}] ERRO: Não foi possível parsear o XML de resposta.",
                tags="erro_conexao",
            )
            self._atualizar_log(escape(response_text), tags="response")

    def _format_xml(self, xml_string):
        """
        Recebe uma string XML e retorna uma versão identada com 'minidom'.
        Em caso de erro de parse, retorna o texto original.

        Args:
            xml_string (str): XML de entrada.

        Returns:
            str: XML formatado ou original.
        """
        if not xml_string:
            return ""
        try:
            dom = minidom.parseString(xml_string)
            return dom.toprettyxml(indent="    ")
        except (xml.parsers.expat.ExpatError, TypeError):
            return xml_string

    def _on_view_xml_click(self):
        """
        Abre um modal com o XML de retorno formatado.
        """
        if not self.last_response_text:
            messagebox.showinfo("Nenhuma Resposta", "Nenhuma resposta foi recebida ainda.")
            return

        modal = ctk.CTkToplevel(self)
        modal.title("XML de Retorno Completo")
        modal.geometry("860x620")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()
        modal.grid_rowconfigure(0, weight=1)
        modal.grid_columnconfigure(0, weight=1)

        text_widget = ctk.CTkTextbox(
            modal,
            font=ctk.CTkFont(family="Consolas", size=10),
            fg_color=COLOR_SURFACE_ALT, border_color=COLOR_BORDER, border_width=1,
            text_color=COLOR_TEXT, wrap="word",
        )
        text_widget.grid(row=0, column=0, sticky="nsew", padx=12, pady=(12, 6))

        try:
            root = ET.fromstring(self.last_response_text)
            result_element = root.find(".//{http://tempuri.org/}Result")
            result_text = result_element.text if result_element is not None else None
            formatted_xml = self._format_xml(result_text or "")
        except (ET.ParseError, AttributeError):
            formatted_xml = self._format_xml(self.last_response_text)

        text_widget.insert("end", formatted_xml)
        text_widget.configure(state="disabled")

        ctk.CTkButton(
            modal, text="Fechar",
            fg_color=COLOR_SURFACE, hover_color=COLOR_HOVER,
            border_width=1, border_color=COLOR_BORDER,
            text_color=COLOR_TEXT_MUTED,
            font=ctk.CTkFont(size=FONT_SM), corner_radius=6,
            command=modal.destroy,
        ).grid(row=1, column=0, pady=(0, 12))

    def _reset_ui(self):
        """
        Restaura o estado dos botões após término/interrupção do processo.
        """
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.view_xml_btn.configure(
            state="normal" if self.last_response_text else "disabled"
        )

    def _atualizar_log(self, message, tags=None):
        """
        Acrescenta uma linha ao log, preservando formatação/cores por tags.
        """
        self.log_text.configure(state="normal")
        if tags:
            self.log_text._textbox.insert("end", (message or "") + "\n", tags)
        else:
            self.log_text._textbox.insert("end", (message or "") + "\n")
        self.log_text.configure(state="disabled")
        self.log_text.see("end")

    def preencher_payload(self, xml_string: str, cod_servico: str):
        """
        API pública do frame para preencher a tela com dados de outro gerador.

        Args:
            xml_string (str): XML a ser inserido no campo de payload.
            cod_servico (str): Código do serviço que originou o XML.
        """
        # Preenche campos relacionados ao serviço/payload
        self.pro_id_entry.delete(0, "end")
        self.pro_id_entry.insert(0, cod_servico)

        self.payload_text.delete("1.0", "end")
        self.payload_text.insert("1.0", xml_string)

        # Reseta indicadores visuais
        self.progress_label.configure(text="")
        self.log_text.configure(state="normal")
        self.log_text._textbox.delete("1.0", "end")
        self.log_text.configure(state="disabled")

        # Log simples via stdout (apoio ao dev)
        print(f"Payload preenchido com XML do serviço {cod_servico}.")
