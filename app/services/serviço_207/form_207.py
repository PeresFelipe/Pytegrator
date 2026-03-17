# app/services/servico_207/form_207.py
# -*- coding: utf-8 -*-
"""
Tela: Gerador de XML - Serviço 207 (otimizado)

Melhorias principais:
- Removido import não utilizado.
- Rolagem cross-platform para Windows/macOS/Linux (MouseWheel / Button-4/5).
- Normalização de entradas (UF e Município) para reduzir erros de API.
- Tratamento de falhas das APIs (IBGE/ViaCEP) com mensagens amigáveis e defaults.
- Botões desabilitados durante operações para evitar cliques repetidos.
- Checagens de layout e grid/pack simplificadas.
- Código mais legível: utilitários para repetição (ex.: _cbool, _safe_api_call, _normalize_*).
"""

import tkinter as tk
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
    FONT_SM,
    FONT_MD,
)

# ---- Integrações e utilitários do projeto (mantidos como no original) ----
from app.lib.api.ibgeAPI import buscar_codigo_municipio
from app.lib.api.viaCepAPI import buscar_endereco_por_municipio
from app.lib.mappers.codigoMapper import get_codigo_interno_por_ibge
from app.lib.generators.cpfGenerator import gerar_cpf
from app.lib.generators.cnpjGenerator import gerar_cnpj
from app.lib.generators.inscricaoGenerator import (
    gerar_inscricao_estadual,
    gerar_inscricao_municipal,
)
from app.lib.generators.nomeGenerator import (
    gerar_nome_aleatorio,
    gerar_nome_empresa,
    gerar_fantasia_empresa,
    gerar_fantasia_pessoa_fisica,
    remover_acentos,
)
from app.lib.formatters.formatters import campo_xml


# Constante de UFs para reuse e validação simples
UF_LIST = [
    "",
    "AC",
    "AL",
    "AP",
    "AM",
    "BA",
    "CE",
    "DF",
    "ES",
    "GO",
    "MA",
    "MT",
    "MS",
    "MG",
    "PA",
    "PB",
    "PR",
    "PE",
    "PI",
    "RJ",
    "RN",
    "RS",
    "RO",
    "RR",
    "SC",
    "SP",
    "SE",
    "TO",
]


class Gerador207Frame(ctk.CTkFrame):
    """
    Frame principal da ferramenta "Gerador de XML - Serviço 207".
    """

    # --------------------------------------------------------------------- #
    # Construtor
    # --------------------------------------------------------------------- #
    def __init__(self, parent: tk.Widget, controller):
        """
        Inicializa o frame, variáveis e interface.
        """
        super().__init__(parent, fg_color=COLOR_BG)
        self.controller = controller
        self._inicializando = True  # evita triggers enquanto monta UI

        # -------------------- Variáveis de estado -------------------- #
        self.tipo_nome_var = tk.StringVar(value="pessoa")  # pessoa | empresa
        self.tipo_pessoa_var = tk.StringVar(value="F")  # F | J | R
        self.tipo_rural_fj_var = tk.StringVar()  # F | J (quando R)

        # Flags/checkboxes
        self.check_vars: dict[str, tk.BooleanVar] = {
            "escriturar": tk.BooleanVar(value=True),
            "enquadraIPI": tk.BooleanVar(),
            "enquadraICMS": tk.BooleanVar(),
            "calculaICMSNaoEnq": tk.BooleanVar(),
            "enquadraISS": tk.BooleanVar(),
            "retemIR": tk.BooleanVar(),
            "retemINSS": tk.BooleanVar(),
            "enquadraSimples": tk.BooleanVar(),
            "ipiSimples": tk.BooleanVar(),
            "icmsSimples": tk.BooleanVar(),
            "issSimples": tk.BooleanVar(),
            "inssSimples": tk.BooleanVar(),
            "retemISS": tk.BooleanVar(),
            "enquadraPIS": tk.BooleanVar(),
            "enquadraCOFINS": tk.BooleanVar(),
            "retemCSLL": tk.BooleanVar(),
            "enquadraFUNRURAL": tk.BooleanVar(),
            "enquadraINSSRURAL": tk.BooleanVar(),
            "checkboxInscricaoEstadual": tk.BooleanVar(),
            "checkboxInscricaoMunicipal": tk.BooleanVar(),
            "checkboxIsento": tk.BooleanVar(),
        }

        # Tipos de agente (multi-seleção)
        self.tipo_agente_vars: dict[str, tk.BooleanVar] = {
            "cliente": tk.BooleanVar(value=True),
            "fornecedor": tk.BooleanVar(),
            "representante": tk.BooleanVar(),
            "contato": tk.BooleanVar(),
            "transportadora": tk.BooleanVar(),
            "obrigacao": tk.BooleanVar(),
            "colaborador": tk.BooleanVar(),
            "outros": tk.BooleanVar(),
            "obra": tk.BooleanVar(),
            "sindicato": tk.BooleanVar(),
        }

        # ----------------------- Montagem da UI ---------------------- #
        self._criar_widgets()
        self._definir_valores_padrao()
        self._configurar_eventos()
        self._inicializando = False

    # --------------------------------------------------------------------- #
    # Construção da interface
    # --------------------------------------------------------------------- #
    def _criar_widgets(self) -> None:
        """
        Cria e posiciona todos os widgets do formulário.
        """
        # Área rolável nativa do CustomTkinter (substitui Canvas+Scrollbar manual)
        scroll = ctk.CTkScrollableFrame(self, fg_color=COLOR_BG)
        scroll.pack(fill="both", expand=True)
        container = ctk.CTkFrame(scroll, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=16)

        # ---- Título ----
        ctk.CTkLabel(
            container,
            text="207 — Agentes",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLOR_TEXT,
            anchor="w",
        ).pack(fill="x", pady=(0, 14))

        # Linha superior: dois grupos de rádio (natureza e tipo de pessoa)
        top_radios_frame = ctk.CTkFrame(container, fg_color="transparent")
        top_radios_frame.pack(fill="x", pady=6)
        top_radios_frame.columnconfigure(0, weight=1)
        top_radios_frame.columnconfigure(1, weight=1)

        # Grupo: Tipo de Natureza
        f1_data = self._criar_grupo_radio(
            top_radios_frame,
            "Tipo de Natureza",
            [("Pessoa", "pessoa"), ("Empresa", "empresa")],
            self.tipo_nome_var,
            return_widgets=True,
        )
        self.f1_frame = f1_data["frame"]
        self.f1_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        # Grupo: Tipo de Pessoa
        tipo_pessoa_data = self._criar_grupo_radio(
            top_radios_frame,
            "Tipo de Pessoa",
            [("Física", "F"), ("Jurídica", "J"), ("Rural", "R")],
            self.tipo_pessoa_var,
            return_widgets=True,
        )
        self.tipo_pessoa_frame = tipo_pessoa_data["frame"]
        self.tipo_pessoa_radios = tipo_pessoa_data["widgets"]
        self.tipo_pessoa_frame.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        # Grupo condicional: produtor rural (só aparece quando tipo=R)
        rural_container_data = self._criar_grupo_radio(
            container,
            "Opções para Produtor Rural",
            [("Pessoa Física", "F"), ("Pessoa Jurídica", "J")],
            self.tipo_rural_fj_var,
            return_widgets=True,
        )
        self.rural_container = rural_container_data["frame"]

        # ---- Grupo: Nome e Fantasia ----
        nome_outer, nome_inner = self._make_group(container, "Nome e Fantasia")
        nome_outer.pack(fill="x", pady=6)
        self._nome_group = nome_outer  # referência para pack(before=...)
        nome_inner.columnconfigure(1, weight=1)

        ctk.CTkLabel(
            nome_inner, text="Nome do Agente:", font=ctk.CTkFont(size=FONT_SM),
            text_color=COLOR_TEXT_MUTED, anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        self.nome_entry = ctk.CTkEntry(
            nome_inner, fg_color=COLOR_SURFACE_ALT,
            border_color=COLOR_BORDER, text_color=COLOR_TEXT,
        )
        self.nome_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=4)

        ctk.CTkLabel(
            nome_inner, text="Nome Fantasia:", font=ctk.CTkFont(size=FONT_SM),
            text_color=COLOR_TEXT_MUTED, anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        self.fantasia_entry = ctk.CTkEntry(
            nome_inner, fg_color=COLOR_SURFACE_ALT,
            border_color=COLOR_BORDER, text_color=COLOR_TEXT,
        )
        self.fantasia_entry.grid(row=1, column=1, sticky="ew", padx=(0, 8), pady=4)

        self.btn_gerar_fantasia = ctk.CTkButton(
            nome_inner, text="Gerar Nome e Fantasia",
            fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
            font=ctk.CTkFont(size=FONT_SM), corner_radius=6,
        )
        self.btn_gerar_fantasia.grid(row=0, column=2, rowspan=2, sticky="ns", padx=(8, 0))

        # ---- Grupo: Inscrições ----
        self.insc_checks = self._criar_grupo_check(
            container,
            "Será gerado Inscrição?",
            [
                ("Inscrição Estadual", "checkboxInscricaoEstadual"),
                ("Inscrição Municipal", "checkboxInscricaoMunicipal"),
                ("ISENTO", "checkboxIsento"),
            ],
        )
        self.insc_checks["frame"].pack(fill="x", pady=6)

        # ---- Grupo: Localização ----
        local_outer, local_inner = self._make_group(container, "Localização")
        local_outer.pack(fill="x", pady=6)
        local_inner.columnconfigure(3, weight=1)

        ctk.CTkLabel(
            local_inner, text="Estado (UF):", font=ctk.CTkFont(size=FONT_SM),
            text_color=COLOR_TEXT_MUTED,
        ).grid(row=0, column=0, sticky="w", padx=(0, 4))
        self.estado_combo = ctk.CTkComboBox(
            local_inner, values=UF_LIST, state="readonly", width=80,
            fg_color=COLOR_SURFACE_ALT, border_color=COLOR_BORDER,
            text_color=COLOR_TEXT, dropdown_fg_color=COLOR_SURFACE,
            button_color=COLOR_BORDER, button_hover_color=COLOR_ACCENT,
        )
        self.estado_combo.grid(row=0, column=1, sticky="w", padx=(0, 12))

        ctk.CTkLabel(
            local_inner, text="Município:", font=ctk.CTkFont(size=FONT_SM),
            text_color=COLOR_TEXT_MUTED,
        ).grid(row=0, column=2, sticky="w", padx=(0, 4))
        self.municipio_entry = ctk.CTkEntry(
            local_inner, fg_color=COLOR_SURFACE_ALT,
            border_color=COLOR_BORDER, text_color=COLOR_TEXT,
        )
        self.municipio_entry.grid(row=0, column=3, sticky="ew")

        # ---- Grupo: Tipo do Agente ----
        tipos_agente = [
            ("Cliente", "cliente"), ("Fornecedor", "fornecedor"),
            ("Representante", "representante"), ("Contato", "contato"),
            ("Transportadora", "transportadora"), ("Obrigação", "obrigacao"),
            ("Colaborador", "colaborador"), ("Outros", "outros"),
            ("Obra", "obra"), ("Sindicato", "sindicato"),
        ]
        self._criar_grupo_check(
            container, "Tipo do Agente", tipos_agente, self.tipo_agente_vars, columns=4,
        )["frame"].pack(fill="x", pady=6)

        # ---- Grupo: Configurações Fiscais ----
        configs_fiscais = [
            ("Escriturar", "escriturar"),
            ("Enquadra IPI", "enquadraIPI"),
            ("Enquadra ICMS", "enquadraICMS"),
            ("Calcula ICMS não enq.", "calculaICMSNaoEnq"),
            ("Enquadra ISS", "enquadraISS"),
            ("Retém IR", "retemIR"),
            ("Retém INSS", "retemINSS"),
            ("Enquadra no Simples", "enquadraSimples"),
            ("IPI pelo Simples", "ipiSimples"),
            ("ICMS pelo Simples", "icmsSimples"),
            ("ISS pelo Simples", "issSimples"),
            ("INSS pelo Simples", "inssSimples"),
            ("Retém ISS", "retemISS"),
            ("Enquadra PIS", "enquadraPIS"),
            ("Enquadra COFINS", "enquadraCOFINS"),
            ("Retém CSLL", "retemCSLL"),
            ("Enquadra FUNRURAL", "enquadraFUNRURAL"),
            ("Enquadra INSS Rural", "enquadraINSSRURAL"),
        ]
        self._criar_grupo_check(
            container, "Configurações Fiscais", configs_fiscais, columns=4,
        )["frame"].pack(fill="x", pady=6)

        # ---- Campo: Filial ----
        filial_outer, filial_inner = self._make_group(container, "")
        filial_outer.pack(fill="x", pady=6)
        ctk.CTkLabel(
            filial_inner, text="Código da Filial (FIL_IN_CODIGO):",
            font=ctk.CTkFont(size=FONT_SM), text_color=COLOR_TEXT_MUTED,
        ).pack(side="left")
        self.filial_entry = ctk.CTkEntry(
            filial_inner, width=120, fg_color=COLOR_SURFACE_ALT,
            border_color=COLOR_BORDER, text_color=COLOR_TEXT,
        )
        self.filial_entry.pack(side="left", padx=8)

        # ---- Ações ----
        action_frame = ctk.CTkFrame(container, fg_color="transparent")
        action_frame.pack(fill="x", pady=14)
        self.btn_gerar_xml = ctk.CTkButton(
            action_frame, text="Gerar XML",
            fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
            font=ctk.CTkFont(size=FONT_MD), corner_radius=6, width=140,
        )
        self.btn_gerar_xml.pack(side="right")

    # --------------------------------------------------------------------- #
    # Helpers de layout
    # --------------------------------------------------------------------- #
    def _make_group(self, parent, text: str) -> tuple:
        """
        Cria um card (frame com borda) com título e retorna (outer, inner).
        """
        outer = ctk.CTkFrame(
            parent, fg_color=COLOR_SURFACE,
            corner_radius=8, border_width=1, border_color=COLOR_BORDER,
        )
        if text:
            ctk.CTkLabel(
                outer, text=text, font=ctk.CTkFont(size=FONT_SM),
                text_color=COLOR_TEXT_MUTED, anchor="w",
            ).pack(anchor="w", padx=12, pady=(8, 4))
        inner = ctk.CTkFrame(outer, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=10, pady=(4, 10))
        return outer, inner

    def _criar_grupo_radio(
        self,
        parent,
        text: str,
        options: list[tuple[str, str]],
        variable: tk.StringVar,
        return_widgets: bool = False,
    ) -> dict:
        """
        Cria um card com radiobuttons estilizados no design system.
        """
        outer = ctk.CTkFrame(
            parent, fg_color=COLOR_SURFACE,
            corner_radius=8, border_width=1, border_color=COLOR_BORDER,
        )
        ctk.CTkLabel(
            outer, text=text, font=ctk.CTkFont(size=FONT_SM),
            text_color=COLOR_TEXT_MUTED, anchor="w",
        ).pack(anchor="w", padx=12, pady=(8, 4))
        inner = ctk.CTkFrame(outer, fg_color="transparent")
        inner.pack(fill="x", padx=8, pady=(0, 8))

        widgets: list[ctk.CTkRadioButton] = []
        for label, value in options:
            rb = ctk.CTkRadioButton(
                inner, text=label, variable=variable, value=value,
                font=ctk.CTkFont(size=FONT_SM), text_color=COLOR_TEXT,
                fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
                border_color=COLOR_BORDER,
            )
            rb.pack(side="left", padx=8, pady=4)
            widgets.append(rb)

        if return_widgets:
            return {"frame": outer, "widgets": widgets}
        return {"frame": outer, "widgets": []}

    def _criar_grupo_check(
        self,
        parent,
        text: str,
        options: list[tuple[str, str]],
        var_dict: dict[str, tk.BooleanVar] | None = None,
        columns: int = 3,
    ) -> dict:
        """
        Cria um card com checkboxes em grade, estilizados no design system.
        """
        if var_dict is None:
            var_dict = self.check_vars

        outer = ctk.CTkFrame(
            parent, fg_color=COLOR_SURFACE,
            corner_radius=8, border_width=1, border_color=COLOR_BORDER,
        )
        ctk.CTkLabel(
            outer, text=text, font=ctk.CTkFont(size=FONT_SM),
            text_color=COLOR_TEXT_MUTED, anchor="w",
        ).pack(anchor="w", padx=12, pady=(8, 4))
        inner = ctk.CTkFrame(outer, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        widgets: dict[str, ctk.CTkCheckBox] = {}
        for i, (label, key) in enumerate(options):
            cb = ctk.CTkCheckBox(
                inner, text=label, variable=var_dict[key],
                font=ctk.CTkFont(size=FONT_SM), text_color=COLOR_TEXT,
                fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
                border_color=COLOR_BORDER,
            )
            cb.grid(row=i // columns, column=i % columns, sticky="w", padx=8, pady=3)
            widgets[key] = cb

        return {"frame": outer, "widgets": widgets}

    # --------------------------------------------------------------------- #
    # Conexão de eventos / valores padrão
    # --------------------------------------------------------------------- #
    def _configurar_eventos(self) -> None:
        """
        Conecta os handlers de eventos aos widgets criados.
        """
        self.btn_gerar_fantasia.configure(command=self.on_gerar_nome_fantasia)
        self.btn_gerar_xml.configure(command=self.on_gerar_xml)

        # Triggers reativos
        self.tipo_nome_var.trace_variable("w", self._atualizar_tipo_pessoa_ui)
        self.tipo_pessoa_var.trace_variable("w", self._atualizar_tipo_rural_ui)
        self.check_vars["checkboxIsento"].trace_variable("w", self._on_isento_change)
        self.check_vars["checkboxInscricaoEstadual"].trace_variable(
            "w", self._on_inscricao_change
        )
        self.check_vars["checkboxInscricaoMunicipal"].trace_variable(
            "w", self._on_inscricao_change
        )

    def _definir_valores_padrao(self) -> None:
        """
        Define valores iniciais do formulário e força atualização da UI dependente.
        """
        self.estado_combo.set("SP")
        self.municipio_entry.insert(0, "Itu")
        self.filial_entry.insert(0, "100")
        self._atualizar_tipo_pessoa_ui()
        self._atualizar_tipo_rural_ui()

    # --------------------------------------------------------------------- #
    # Regras de interação (mostra/esconde seções, etc.)
    # --------------------------------------------------------------------- #
    def _atualizar_tipo_pessoa_ui(self, *_):
        """
        Se for Empresa: fixa 'J' e oculta bloco rural.
        Se for Pessoa: libera F/J/R e delega ao _atualizar_tipo_rural_ui.
        """
        if self._inicializando:
            return

        if self.tipo_nome_var.get() == "empresa":
            for radio in self.tipo_pessoa_radios:
                if radio.cget("value") == "J":
                    radio.configure(state="normal")
                    self.tipo_pessoa_var.set("J")
                else:
                    radio.configure(state="disabled")
            self.rural_container.pack_forget()
        else:
            for radio in self.tipo_pessoa_radios:
                radio.configure(state="normal")
            self._atualizar_tipo_rural_ui()

    def _atualizar_tipo_rural_ui(self, *_):
        """
        Mostra o bloco de opções rurais apenas quando Pessoa & tipo 'R'.
        """
        if self._inicializando:
            return

        if self.tipo_nome_var.get() == "pessoa" and self.tipo_pessoa_var.get() == "R":
            self.rural_container.pack(
                fill="x", pady=6, anchor="n", before=self._nome_group
            )
        else:
            self.rural_container.pack_forget()

    def _on_isento_change(self, *_):
        """
        Se 'ISENTO' marcado, desativa inscrições Estadual/Municipal e limpa suas marcas.
        """
        if self._inicializando:
            return

        is_isento = self._cbool("checkboxIsento")
        est_check = self.insc_checks["widgets"]["checkboxInscricaoEstadual"]
        mun_check = self.insc_checks["widgets"]["checkboxInscricaoMunicipal"]

        est_check.configure(state="disabled" if is_isento else "normal")
        mun_check.configure(state="disabled" if is_isento else "normal")

        if is_isento:
            self.check_vars["checkboxInscricaoEstadual"].set(False)
            self.check_vars["checkboxInscricaoMunicipal"].set(False)

    def _on_inscricao_change(self, *_):
        """
        Se qualquer inscrição marcada, desabilita 'ISENTO'; caso contrário, reabilita.
        """
        if self._inicializando:
            return

        has_any = self._cbool("checkboxInscricaoEstadual") or self._cbool(
            "checkboxInscricaoMunicipal"
        )
        isento_check = self.insc_checks["widgets"]["checkboxIsento"]
        isento_check.configure(state="disabled" if has_any else "normal")

    # --------------------------------------------------------------------- #
    # Ações principais
    # --------------------------------------------------------------------- #
    def on_gerar_nome_fantasia(self) -> None:
        """
        Gera automaticamente 'Nome' e 'Nome Fantasia' conforme tipo de nome.
        """
        tipo_nome = self.tipo_nome_var.get()
        if tipo_nome == "pessoa":
            nome = gerar_nome_aleatorio()
            fantasia = gerar_fantasia_pessoa_fisica(nome)
        else:
            nome = gerar_nome_empresa()
            fantasia = gerar_fantasia_empresa()

        self.nome_entry.delete(0, "end")
        self.nome_entry.insert(0, nome)
        self.fantasia_entry.delete(0, "end")
        self.fantasia_entry.insert(0, fantasia)

    def on_gerar_xml(self) -> None:
        """
        Gera o XML do Serviço 207 com validações, chamadas de API e montagem final.
        """
        # Desabilita botão para evitar cliques repetidos enquanto processa
        self._set_actions_enabled(False)
        try:
            # --- Leitura dos campos
            nome = self._normalize_nome(self.nome_entry.get())
            fantasia = self.fantasia_entry.get().strip()
            tipo_pessoa = self.tipo_pessoa_var.get()
            estado = self._normalize_uf(self.estado_combo.get())
            municipio = self._normalize_municipio(self.municipio_entry.get())
            filial_codigo = self.filial_entry.get().strip()

            # --- Validações básicas
            if not all([municipio, estado, filial_codigo, nome]):
                messagebox.showerror(
                    "Erro de Validação",
                    "Preencha os campos obrigatórios:\n- Nome do Agente\n- Estado\n- Município\n- Código da Filial",
                )
                return

            if estado not in UF_LIST or not estado:
                messagebox.showerror("Erro de Validação", "Selecione uma UF válida.")
                return

            if tipo_pessoa == "R" and not self.tipo_rural_fj_var.get():
                messagebox.showerror(
                    "Erro de Validação",
                    "Para o tipo 'Rural', selecione 'Pessoa Física' ou 'Pessoa Jurídica'.",
                )
                return

            # --- Integrações (com proteção a exceções e retornos incompletos)
            ibge_data = self._safe_api_call(
                lambda: buscar_codigo_municipio(municipio, estado),
                default={"codigo": ""},
                fail_msg="Não foi possível obter o código do município (IBGE).",
            )
            if not ibge_data.get("codigo"):
                return  # já mostramos mensagem ao usuário

            endereco_data = self._safe_api_call(
                lambda: buscar_endereco_por_municipio(municipio, estado),
                default={"cep": "", "logradouro": "", "numero": "", "bairro": ""},
                fail_msg="Não foi possível obter endereço base (ViaCEP).",
                show_only=False,  # não é fatal; segue com campos vazios
            )

            codigo_interno = get_codigo_interno_por_ibge(ibge_data["codigo"]) or ""

            # E-mail sintético baseado no nome
            email = remover_acentos(nome.lower().replace(" ", ".")) + "@exemplo.com"

            # Descobre sigla do tipo de logradouro (R/AV/TV/AL)
            sigla_logradouro = self._inferir_tipo_logradouro(
                endereco_data.get("logradouro", "")
            )

            # --- Blocos XML
            bloco_pessoa = self._gerar_bloco_pessoa(tipo_pessoa)
            bloco_inscricoes = self._gerar_bloco_inscricoes()
            bloco_fiscal = self._gerar_bloco_fiscal()
            bloco_agente_id = self._gerar_bloco_agente_id()

            # Bloco opcional (somente se tipo=R)
            bloco_rural = (
                f"\n  <AGN_CH_RURALTIPOPESSOAFJ>{campo_xml(self.tipo_rural_fj_var.get())}</AGN_CH_RURALTIPOPESSOAFJ>"
                if self.tipo_pessoa_var.get() == "R"
                else ""
            )

            # --- Montagem do XML final (string única, com defaults seguros)
            xml_final = (
                '<Agente OPERACAO="I">'
                f"\n  <AGN_ST_NOME>{campo_xml(nome, 100)}</AGN_ST_NOME>"
                f"\n  <AGN_ST_FANTASIA>{campo_xml(fantasia, 100)}</AGN_ST_FANTASIA>"
                f"\n  <TPP_IN_CODIGO>{campo_xml(tipo_pessoa)}</TPP_IN_CODIGO>"
                f"\n  <TAB05_IN_CODIGO>{campo_xml('1' if tipo_pessoa == 'F' else '2')}</TAB05_IN_CODIGO>"
                f"\n  <AGN_ST_EMAIL>{campo_xml(email, 30)}</AGN_ST_EMAIL>{bloco_inscricoes}"
                "\n  <PA_ST_SIGLA>BRA</PA_ST_SIGLA>"
                f"\n  <UF_ST_SIGLA>{campo_xml(estado)}</UF_ST_SIGLA>"
                f"\n  <MUN_NO_NOME>{campo_xml(municipio)}</MUN_NO_NOME>"
                f"\n  <MUN_IN_CODIGO>{campo_xml(codigo_interno)}</MUN_IN_CODIGO>"
                f"\n  <TPL_ST_SIGLA>{campo_xml(sigla_logradouro)}</TPL_ST_SIGLA>"
                f"\n  <AGN_ST_CEP>{campo_xml(endereco_data.get('cep',''))}</AGN_ST_CEP>"
                f"\n  <AGN_ST_LOGRADOURO>{campo_xml(endereco_data.get('logradouro',''), 50)}</AGN_ST_LOGRADOURO>"
                f"\n  <AGN_ST_NUMERO>{campo_xml(str(endereco_data.get('numero','')), 10)}</AGN_ST_NUMERO>"
                f"\n  <AGN_ST_BAIRRO>{campo_xml(endereco_data.get('bairro',''), 30)}</AGN_ST_BAIRRO>"
                f"{bloco_pessoa}{bloco_rural}"
                '\n  <Parametros OPERACAO="I">'
                f"\n    <FIL_IN_CODIGO>{campo_xml(filial_codigo)}</FIL_IN_CODIGO>"
                "\n  </Parametros>"
                f"{bloco_agente_id}{bloco_fiscal}\n</Agente>"
            )

            # Entrega o XML para a tela de Resultado
            self.controller.shared_data["current_xml"] = xml_final
            self.controller.show_frame("Resultado")

        except Exception as e:
            messagebox.showerror(
                "Erro ao Gerar XML", f"Ocorreu um erro inesperado:\n\n{e}"
            )
        finally:
            self._set_actions_enabled(True)

    # --------------------------------------------------------------------- #
    # Utilidades / pequenos blocos XML
    # --------------------------------------------------------------------- #
    def _inferir_tipo_logradouro(self, logradouro: str = "") -> str:
        """
        Converte o primeiro termo do logradouro em sigla padrão quando reconhecido.
        """
        tipo = logradouro.split(" ")[0].lower() if logradouro else ""
        mapa = {"rua": "R", "avenida": "AV", "travessa": "TV", "alameda": "AL"}
        return mapa.get(tipo, tipo.upper())

    def _gerar_bloco_pessoa(self, tipo_pessoa: str) -> str:
        """
        Bloco de identificação conforme o tipo de pessoa.
        """
        if tipo_pessoa == "F":
            return (
                f'\n  <PesFisica OPERACAO="I"><AGN_ST_CPF>{campo_xml(gerar_cpf())}'
                f"</AGN_ST_CPF></PesFisica>"
            )
        if tipo_pessoa == "J":
            return f"\n  <AGN_ST_CGC>{campo_xml(gerar_cnpj())}</AGN_ST_CGC>"
        return ""

    def _gerar_bloco_inscricoes(self) -> str:
        """
        Bloco de inscrições: ISENTO domina; caso contrário, inclui as marcadas.
        """
        if self._cbool("checkboxIsento"):
            return "\n  <AGN_ST_INSCRESTADUAL>ISENTO</AGN_ST_INSCRESTADUAL>\n  <AGN_ST_INSCRMUNIC>ISENTO</AGN_ST_INSCRMUNIC>"
        out = []
        if self._cbool("checkboxInscricaoEstadual"):
            out.append(
                f"\n  <AGN_ST_INSCRESTADUAL>{gerar_inscricao_estadual()}</AGN_ST_INSCRESTADUAL>"
            )
        if self._cbool("checkboxInscricaoMunicipal"):
            out.append(
                f"\n  <AGN_ST_INSCRMUNIC>{gerar_inscricao_municipal()}</AGN_ST_INSCRMUNIC>"
            )
        return "".join(out)

    def _gerar_bloco_fiscal(self) -> str:
        """
        Constrói o bloco <Fiscal> com as flags marcadas; vazio se nenhuma.
        """
        mapa_tags = {
            "escriturar": "AGN_BO_ESCRITURAR",
            "enquadraIPI": "AGN_BO_ENQUADRAIPI",
            "enquadraICMS": "AGN_BO_ENQUADRAICMS",
            "calculaICMSNaoEnq": "AGN_BO_CALCICMSNAOENQ",
            "enquadraISS": "AGN_BO_ENQUADRAISS",
            "retemIR": "AGN_BO_RETERIR",
            "retemINSS": "AGN_BO_RETERINSS",
            "enquadraSimples": "AGN_BO_SIMPLES",
            "ipiSimples": "AGN_BO_IPISIMPLES",
            "icmsSimples": "AGN_BO_ICMSSIMPLES",
            "issSimples": "AGN_BO_ISSSIMPLES",
            "inssSimples": "AGN_BO_INSSSIMPLES",
            "retemISS": "AGN_BO_RETERISS",
            "enquadraPIS": "AGN_BO_ENQUADRAPIS",
            "enquadraCOFINS": "AGN_BO_ENQUADRACOFINS",
            "retemCSLL": "AGN_BO_RETERCSLL",
            "enquadraFUNRURAL": "AGN_BO_ENQUADRAFUNRURAL",
            "enquadraINSSRURAL": "AGN_BO_ENQUADRAINSSRURAL",
        }

        linhas = [
            f"    <{tag}>S</{tag}>"
            for chave, tag in mapa_tags.items()
            if self.check_vars.get(chave) and self.check_vars[chave].get()
        ]
        if not linhas:
            return ""

        return (
            '\n  <Fiscal OPERACAO="I">'
            "\n    <AGN_DT_INIVIGENCIA>01/01/2000</AGN_DT_INIVIGENCIA>\n"
            + "\n".join(linhas)
            + "\n  </Fiscal>"
        )

    def _gerar_bloco_agente_id(self) -> str:
        """
        Gera múltiplos blocos <AgenteId> conforme os tipos de agente selecionados.
        """
        mapa_tipo_agente = {
            "cliente": "C",
            "fornecedor": "F",
            "representante": "R",
            "contato": "E",
            "transportadora": "T",
            "obrigacao": "S",
            "colaborador": "U",
            "outros": "O",
            "obra": "B",
            "sindicato": "D",
        }
        parts = []
        for nome, var in self.tipo_agente_vars.items():
            if var.get():
                parts.append(
                    '\n    <AgenteId OPERACAO="I">'
                    f"<AGN_TAU_ST_CODIGO>{campo_xml(mapa_tipo_agente.get(nome, ''))}</AGN_TAU_ST_CODIGO>"
                    "</AgenteId>"
                )
        return "".join(parts)

    # --------------------------------------------------------------------- #
    # Helpers privados
    # --------------------------------------------------------------------- #
    def _cbool(self, key: str) -> bool:
        """
        Retorna valor booleano de uma chave em self.check_vars com fallback.
        """
        var = self.check_vars.get(key)
        return bool(var.get()) if isinstance(var, tk.BooleanVar) else False

    def _normalize_uf(self, uf: str) -> str:
        """
        Normaliza UF para caixa alta e remove espaços.
        """
        return (uf or "").strip().upper()

    def _normalize_municipio(self, s: str) -> str:
        """
        Normaliza município removendo espaços múltiplos e capitalizando.
        """
        s = (s or "").strip()
        # Capitalização simples preservando palavras curtas
        return " ".join(
            [w.capitalize() if len(w) > 2 else w.lower() for w in s.split()]
        )

    def _normalize_nome(self, s: str) -> str:
        """
        Nome com espaços normalizados (evita XML quebrado).
        """
        return " ".join((s or "").split())

    def _safe_api_call(self, fn, default, fail_msg: str, show_only: bool = True):
        """
        Executa uma função (chamada de API) com captura de exceções.
        - default: retorno em caso de falha
        - fail_msg: mensagem para o usuário
        - show_only: se True, mostra erro e interrompe fluxo crítico (retorna default e chama messagebox).
                     se False, apenas registra para seguir com defaults silenciosamente.
        """
        try:
            res = fn()
            return res if res is not None else default
        except Exception as e:
            if show_only:
                messagebox.showerror(
                    "Falha na Integração", f"{fail_msg}\n\nDetalhe: {e}"
                )
            return default

    def _set_actions_enabled(self, enabled: bool) -> None:
        """
        Habilita/Desabilita botões de ação para evitar cliques múltiplos.
        """
        state = "normal" if enabled else "disabled"
        try:
            self.btn_gerar_xml.configure(state=state)
            self.btn_gerar_fantasia.configure(state=state)
        except Exception:
            pass
