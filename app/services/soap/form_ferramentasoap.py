# app/services/soap/form_ferramentasoap.py

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import requests
import xml.etree.ElementTree as ET
from html import escape
from xml.dom import minidom
import xml.parsers.expat


class FerramentaSOAPFrame(ttk.Frame):
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
        super().__init__(parent)
        self.controller = controller
        # Evento usado para sinalizar interrupção segura do processo em thread
        self.deve_interromper = threading.Event()
        # Cria e posiciona todos os widgets da interface
        self._criar_widgets()

    def _criar_widgets(self):
        """
        Cria e organiza todos os widgets da interface gráfica (labels, entries, botões, áreas de texto).
        Observações:
          - Mantém o layout original.
          - Removeu-se o botão "Voltar ao Menu" conforme solicitado.
        """
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)
        main_frame.rowconfigure(3, weight=1)
        main_frame.columnconfigure(0, weight=1)

        # --- Barra de Título ---
        title_bar = tk.Label(
            main_frame,
            text="Ferramenta de Integração SOAP",
            bg="#005a9e",
            fg="white",
            font=("Helvetica", 12, "bold"),
            padx=10,
            pady=5,
            anchor="w",
        )
        title_bar.grid(row=0, column=0, sticky="ew", pady=(0, 5))

        # --- Configuração e Parâmetros ---
        config_frame = ttk.LabelFrame(
            main_frame, text="Configuração do Envio", padding="10"
        )
        config_frame.grid(row=1, column=0, sticky="ew", pady=5)
        config_frame.columnconfigure(4, weight=1)

        ttk.Label(config_frame, text="Computador/URL Integrador:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.url_base_entry = ttk.Entry(config_frame, width=40)
        self.url_base_entry.insert(0, "localhost")
        self.url_base_entry.grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(config_frame, text="Porta Integrador:").grid(
            row=0, column=2, sticky="w", padx=(10, 5), pady=5
        )
        self.port_entry = ttk.Entry(config_frame, width=10)
        self.port_entry.insert(0, "8110")
        self.port_entry.grid(row=0, column=3, sticky="w", padx=5)

        ttk.Label(config_frame, text="Número de Envios:").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        self.repetitions_entry = ttk.Entry(config_frame, width=10)
        self.repetitions_entry.insert(0, "1")
        self.repetitions_entry.grid(row=1, column=1, sticky="w", padx=5)

        params_frame = ttk.LabelFrame(
            main_frame, text="Parâmetros da Requisição", padding="10"
        )
        params_frame.grid(row=2, column=0, sticky="ew", pady=5)

        # Validadores (callbacks de Tk) para limitar tamanho/entrada
        vcmd_num_4 = (self.register(self._validate_numeric_input), "%P", "4")
        vcmd_num_6 = (self.register(self._validate_numeric_input), "%P", "6")
        vcmd_num_3 = (self.register(self._validate_numeric_input), "%P", "3")
        vcmd_char_50 = (self.register(self._validate_char_input), "%P", "50")

        ttk.Label(params_frame, text="Cód. Serviço:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.pro_id_entry = ttk.Entry(
            params_frame, width=10, validate="key", validatecommand=vcmd_num_4
        )
        self.pro_id_entry.insert(0, "0000")
        self.pro_id_entry.grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(params_frame, text="Cód. Usuário:").grid(
            row=0, column=2, sticky="w", padx=(20, 5), pady=5
        )
        self.usu_codigo_entry = ttk.Entry(
            params_frame, width=10, validate="key", validatecommand=vcmd_num_4
        )
        self.usu_codigo_entry.insert(0, "0001")
        self.usu_codigo_entry.grid(row=0, column=3, sticky="w", padx=5)

        ttk.Label(params_frame, text="Cód. Transação:").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        self.transacao_entry = ttk.Entry(
            params_frame, width=10, validate="key", validatecommand=vcmd_num_6
        )
        self.transacao_entry.insert(0, "0")
        self.transacao_entry.grid(row=1, column=1, sticky="w", padx=5)

        ttk.Label(params_frame, text="Cód. Sistema:").grid(
            row=1, column=2, sticky="w", padx=(20, 5), pady=5
        )
        self.sistema_entry = ttk.Entry(
            params_frame, width=10, validate="key", validatecommand=vcmd_num_3
        )
        self.sistema_entry.insert(0, "001")
        self.sistema_entry.grid(row=1, column=3, sticky="w", padx=5)

        ttk.Label(params_frame, text="Obs:").grid(
            row=2, column=0, sticky="w", padx=5, pady=5
        )
        self.obs_entry = ttk.Entry(
            params_frame, validate="key", validatecommand=vcmd_char_50
        )
        self.obs_entry.grid(row=2, column=1, columnspan=3, sticky="ew", padx=5)
        params_frame.columnconfigure(3, weight=1)

        # Paned vertical com editor de payload e logs
        paned_window = ttk.PanedWindow(main_frame, orient=tk.VERTICAL)
        paned_window.grid(row=3, column=0, sticky="nsew", pady=5)

        # --- XML Envio ---
        payload_frame = ttk.LabelFrame(paned_window, text="XML Envio", padding="10")
        payload_frame.rowconfigure(0, weight=1)
        payload_frame.columnconfigure(0, weight=1)
        paned_window.add(payload_frame, weight=2)

        self.payload_text = scrolledtext.ScrolledText(
            payload_frame, height=8, font=("Consolas", 10), wrap=tk.WORD
        )
        self.payload_text.grid(row=0, column=0, sticky="nsew")

        # --- Progresso e Logs ---
        log_frame_text = "Progresso e Logs ( arraste a barra acima para redimensionar )"
        log_frame = ttk.LabelFrame(paned_window, text=log_frame_text, padding="10")
        log_frame.rowconfigure(1, weight=1)
        log_frame.columnconfigure(0, weight=1)
        paned_window.add(log_frame, weight=3)

        self.progress_label = ttk.Label(log_frame, text="")
        self.progress_label.grid(row=0, column=0, sticky="ew", pady=(0, 2))

        self.log_text = scrolledtext.ScrolledText(
            log_frame, height=10, font=("Consolas", 10), state="disabled", wrap=tk.WORD
        )
        self.log_text.grid(row=1, column=0, sticky="nsew")

        # Estilos de log para feedback visual
        self.log_text.tag_config(
            "sucesso", foreground="green", font=("Consolas", 10, "bold")
        )
        self.log_text.tag_config(
            "erro_servico", foreground="red", font=("Consolas", 10, "bold")
        )
        self.log_text.tag_config(
            "erro_conexao", foreground="red", font=("Consolas", 10, "bold")
        )
        self.log_text.tag_config("info", foreground="gray")
        self.log_text.tag_config(
            "response", background="#f0f0f0", lmargin1=10, lmargin2=10
        )

        # --- Botões de Ação ---
        botoes_frame = ttk.Frame(main_frame)
        botoes_frame.grid(row=4, column=0, sticky="ew", pady=(10, 5))

        # Inicia a thread de integração
        self.start_btn = ttk.Button(
            botoes_frame,
            text="Iniciar Integração",
            command=self._on_start_click,
            style="Accent.TButton",
        )
        self.start_btn.pack(side="left", padx=(0, 10))

        # Sinaliza interrupção para a thread
        self.stop_btn = ttk.Button(
            botoes_frame,
            text="Interromper",
            command=self._on_stop_click,
            state="disabled",
        )
        self.stop_btn.pack(side="left", padx=(0, 10))

        # Abre modal para visualizar XML de retorno formatado
        self.view_xml_btn = ttk.Button(
            botoes_frame,
            text="Visualizar XML de Retorno",
            command=self._on_view_xml_click,
            state="disabled",
        )
        self.view_xml_btn.pack(side="left", padx=(0, 10))

        # Buffer com o último XML bruto de resposta
        self.last_response_text = ""

        # OBS: Botão "Voltar ao Menu" foi REMOVIDO conforme solicitado.

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
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.view_xml_btn.config(state="disabled")
        self.last_response_text = ""
        self.deve_interromper.clear()

        # Reseta logs
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.insert("1.0", "Tentando comunicar...\n", "info")
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
            self.stop_btn.config(state="disabled")

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
        self.after(0, lambda: self.progress_label.config(text=final_message))
        self.after(0, self._reset_ui)

    def _limpar_log_inicial(self):
        """
        Limpa o texto inicial 'Tentando comunicar...' antes de inserir logs reais.
        """
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
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
        self.view_xml_btn.config(state="normal")

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
        - Caso ainda não haja resposta, exibe alerta informativo.
        """
        if not self.last_response_text:
            messagebox.showinfo(
                "Nenhuma Resposta", "Nenhuma resposta foi recebida ainda."
            )
            return

        # Cria janela modal para exibir o retorno
        modal = tk.Toplevel(self)
        modal.title("XML de Retorno Completo")
        modal.geometry("800x600")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        text_widget = scrolledtext.ScrolledText(
            modal, font=("Consolas", 10), wrap=tk.WORD
        )
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)

        # Tenta formatar o nó Result (quando presente); senão, todo o XML bruto
        try:
            root = ET.fromstring(self.last_response_text)
            result_element = root.find(".//{http://tempuri.org/}Result")
            result_text = result_element.text if result_element is not None else None
            formatted_xml = self._format_xml(result_text or "")
        except (ET.ParseError, AttributeError):
            formatted_xml = self._format_xml(self.last_response_text)

        text_widget.insert("1.0", formatted_xml)
        text_widget.configure(state="disabled")

        close_btn = ttk.Button(modal, text="Fechar", command=modal.destroy)
        close_btn.pack(pady=10)

    def _reset_ui(self):
        """
        Restaura o estado dos botões após término/interrupção do processo.
        """
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.view_xml_btn.config(
            state="normal" if self.last_response_text else "disabled"
        )

    def _atualizar_log(self, message, tags=None):
        """
        Acrescenta uma linha ao log, preservando formatação/cores por tags.
        Usa 'state=disabled' para impedir edição manual.

        Args:
            message (str): texto a ser inserido no fim do log.
            tags (str|tuple|None): tag(s) para estilização ('sucesso', 'erro_conexao', etc.).
        """
        self.log_text.configure(state="normal")
        if tags:
            self.log_text.insert("end", (message or "") + "\n", tags)
        else:
            self.log_text.insert("end", (message or "") + "\n")
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
        self.progress_label.config(text="")
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

        # Log simples via stdout (apoio ao dev)
        print(f"Payload preenchido com XML do serviço {cod_servico}.")
