# app/services/soap/form_ferramentasoap.py

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import requests
import xml.etree.ElementTree as ET
from html import escape
import re
from xml.dom import minidom
import xml.parsers.expat


class FerramentaSOAPWindow(tk.Toplevel):
    """
    Janela da ferramenta de envio de requisições SOAP em lote.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Ferramenta de Integração SOAP")
        self.geometry("900x800")
        self.minsize(750, 650)

        self.deve_interromper = threading.Event()
        self._criar_widgets()

    def _criar_widgets(self):
        """Cria e posiciona todos os widgets da interface gráfica."""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)

        config_frame = ttk.LabelFrame(
            main_frame, text="Configuração do Envio", padding="10"
        )
        config_frame.pack(fill="x", pady=5)
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
        params_frame.pack(fill="x", pady=5)
        vcmd_num_4 = (self.register(self._validate_numeric_input), "%P", 4)
        vcmd_num_6 = (self.register(self._validate_numeric_input), "%P", 6)
        vcmd_num_3 = (self.register(self._validate_numeric_input), "%P", 3)
        vcmd_char_50 = (self.register(self._validate_char_input), "%P", 50)

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

        # --- MUDANÇA 1: Cód. Transação volta a ter o padrão 0 ---
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

        payload_frame = ttk.LabelFrame(main_frame, text="XML Envio", padding="10")
        payload_frame.pack(fill="both", expand=True, pady=5)
        self.payload_text = scrolledtext.ScrolledText(
            payload_frame, height=10, font=("Consolas", 10), wrap=tk.WORD
        )
        self.payload_text.pack(fill="both", expand=True, pady=5)

        botoes_frame = ttk.Frame(main_frame)
        botoes_frame.pack(fill="x", pady=10)
        self.start_btn = ttk.Button(
            botoes_frame,
            text="Iniciar Integração",
            command=self._on_start_click,
            style="Accent.TButton",
        )
        self.start_btn.pack(side="left", padx=(0, 10))
        self.stop_btn = ttk.Button(
            botoes_frame,
            text="Interromper",
            command=self._on_stop_click,
            state="disabled",
        )
        self.stop_btn.pack(side="left", padx=(0, 10))
        self.view_xml_btn = ttk.Button(
            botoes_frame,
            text="Visualizar XML de Retorno",
            command=self._on_view_xml_click,
            state="disabled",
        )
        self.view_xml_btn.pack(side="left")
        self.last_response_text = ""

        log_frame = ttk.LabelFrame(main_frame, text="Progresso e Logs", padding="10")
        log_frame.pack(fill="both", expand=True, pady=5)
        self.progress_label = ttk.Label(log_frame, text="")
        self.progress_label.pack(fill="x", pady=5)
        self.log_text = scrolledtext.ScrolledText(
            log_frame, height=10, font=("Consolas", 10), state="disabled", wrap=tk.WORD
        )
        self.log_text.pack(fill="both", expand=True)

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

    def _validate_numeric_input(self, new_value, max_len):
        if not new_value:
            return True
        if new_value.isdigit() and len(new_value) <= int(max_len):
            return True
        return False

    def _validate_char_input(self, new_value, max_len):
        if len(new_value) <= int(max_len):
            return True
        return False

    def _construir_url_final(self):
        url_base = self.url_base_entry.get().strip()
        port = self.port_entry.get().strip()
        if not url_base.lower().startswith(("http://", "https://")):
            url_base = "http://" + url_base
        url_base = url_base.rstrip("/")
        full_url = f"{url_base}:{port}/SOAP?service=MegaIntegradorService"
        return full_url

    def _on_start_click(self):
        try:
            url_base = self.url_base_entry.get().strip()
            port_str = self.port_entry.get().strip()
            if not url_base or not port_str:
                messagebox.showerror(
                    "Erro de Validação",
                    "Os campos de 'Computador/URL' e 'Porta' são obrigatórios.",
                )
                return
            if not port_str.isdigit():
                messagebox.showerror(
                    "Erro de Validação", "A 'Porta' deve ser um número."
                )
                return

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

        # --- MUDANÇA 2: Nova lógica de validação ---
        if not all([self.pro_id, self.usu_codigo, self.transacao, self.sistema]):
            messagebox.showerror(
                "Erro de Validação",
                "Todos os campos de parâmetros, exceto 'Obs', são obrigatórios.",
            )
            return

        if self.pro_id == "0000":
            messagebox.showerror(
                "Erro de Validação", "O 'Cód. Serviço' deve ser diferente de 0000."
            )
            return

        # Se o XML de envio estiver preenchido, a transação DEVE ser 0.
        if self.payload_template and self.transacao != "0":
            messagebox.showerror(
                "Conflito de Parâmetros",
                "Se o 'XML Envio' for preenchido, o 'Cód. Transação' deve ser 0.",
            )
            return

        # Se a transação for preenchida (diferente de 0), o XML DEVE estar vazio.
        if self.transacao != "0" and self.payload_template:
            messagebox.showerror(
                "Conflito de Parâmetros",
                "Se o 'Cód. Transação' for preenchido, o 'XML Envio' deve estar vazio.",
            )
            return

        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.view_xml_btn.config(state="disabled")
        self.last_response_text = ""
        self.deve_interromper.clear()

        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.insert("1.0", "Tentando comunicar...\n", "info")
        self.log_text.configure(state="disabled")

        self.worker_thread = threading.Thread(
            target=self._iniciar_processo, daemon=True
        )
        self.worker_thread.start()

    def _on_stop_click(self):
        if self.worker_thread and self.worker_thread.is_alive():
            self.deve_interromper.set()
            self._atualizar_log(
                "Interrupção solicitada... O processo irá parar após a requisição atual.",
                tags="info",
            )
            self.stop_btn.config(state="disabled")

    def _iniciar_processo(self):
        primeira_resposta = True
        for i in range(1, self.repetitions + 1):
            if self.deve_interromper.is_set():
                self.after(
                    0,
                    lambda: self._atualizar_log(
                        "Processo interrompido pelo usuário.", tags="info"
                    ),
                )
                break

            self.after(
                0,
                lambda i=i: self.progress_label.config(
                    text=f"Enviando {i} de {self.repetitions}..."
                ),
            )

            obs_final = self.obs or f"Envio #{i} pela ferramenta"
            # --- MUDANÇA 3: pEnviaRecebe fixo em 'R' e lógica de transação ajustada ---
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

                if primeira_resposta:
                    self.after(0, self._limpar_log_inicial)
                    primeira_resposta = False

                self.after(0, self._processar_resposta_servico, i, response.text)

            except requests.exceptions.RequestException as e:
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
            time.sleep(0.1)

        final_message = (
            "Processo concluído!"
            if not self.deve_interromper.is_set()
            else "Processo interrompido!"
        )
        self.after(0, lambda: self.progress_label.config(text=final_message))
        self.after(0, self._reset_ui)

    def _limpar_log_inicial(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def _processar_resposta_servico(self, index, response_text):
        self.last_response_text = response_text
        self.view_xml_btn.config(state="normal")
        try:
            root = ET.fromstring(response_text)
            result_text = root.find(".//{http://tempuri.org/}Result").text

            # Se o resultado for vazio (None), não há o que processar
            if result_text is None:
                self._atualizar_log(
                    f"[{index}] SUCESSO: Comunicação realizada, mas o servidor retornou uma resposta vazia.",
                    tags="sucesso",
                )
                return

            inner_root = ET.fromstring(result_text)

            erro_element = inner_root.find("Erro")
            is_erro = erro_element is not None and erro_element.text.lower() == "true"

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
            cod_transacao = cod_element.text if cod_element is not None else "N/A"

            resumo = (
                f"\n  Mensagem: {mensagem}\n  Código da Transação: {cod_transacao}\n"
            )
            self._atualizar_log(escape(resumo), tags="response")

        except (ET.ParseError, AttributeError):
            self._atualizar_log(
                f"[{index}] ERRO: Não foi possível parsear o XML de resposta.",
                tags="erro_conexao",
            )
            self._atualizar_log(escape(response_text), tags="response")

    def _format_xml(self, xml_string):
        try:
            dom = minidom.parseString(xml_string)
            return dom.toprettyxml(indent="    ")
        except (xml.parsers.expat.ExpatError, TypeError):
            return xml_string

    def _on_view_xml_click(self):
        if not self.last_response_text:
            messagebox.showinfo(
                "Nenhuma Resposta", "Nenhuma resposta foi recebida ainda."
            )
            return
        modal = tk.Toplevel(self)
        modal.title("XML de Retorno Completo")
        modal.geometry("800x600")
        modal.transient(self)
        modal.grab_set()
        text_widget = scrolledtext.ScrolledText(
            modal, font=("Consolas", 10), wrap=tk.WORD
        )
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)

        try:
            root = ET.fromstring(self.last_response_text)
            result_text = root.find(".//{http://tempuri.org/}Result").text
            # Garante que mesmo um resultado vazio seja formatado
            formatted_xml = self._format_xml(result_text or "")
        except (ET.ParseError, AttributeError):
            formatted_xml = self._format_xml(self.last_response_text)

        text_widget.insert("1.0", formatted_xml)
        text_widget.configure(state="disabled")
        close_btn = ttk.Button(modal, text="Fechar", command=modal.destroy)
        close_btn.pack(pady=10)

    def _reset_ui(self):
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

    def _atualizar_log(self, message, tags=None):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n", tags)
        self.log_text.configure(state="disabled")
        self.log_text.see("end")


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Testador da Ferramenta SOAP")

    def open_tool():
        app = FerramentaSOAPWindow(root)
        app.grab_set()

    btn = ttk.Button(root, text="Abrir Ferramenta SOAP", command=open_tool)
    btn.pack(padx=50, pady=50)
    root.mainloop()
