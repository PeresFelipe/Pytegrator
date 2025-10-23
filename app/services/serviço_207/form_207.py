# app/services/servico_207/form_207.py

import tkinter as tk
from tkinter import ttk, messagebox
import re

from app.views.xmlResultado import ResultadoWindow
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


class Gerador207Window(tk.Toplevel):
    """
    Janela da ferramenta Gerador de XML - Serviço 207.
    Contém a UI e a lógica de negócio para esta funcionalidade.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self._inicializando = True

        self.title("Gerador de XML - Serviço 207")
        self.geometry("850x750")
        self.minsize(800, 700)

        # --- Variáveis de Controle do Tkinter ---
        self.tipo_nome_var = tk.StringVar(value="pessoa")
        self.tipo_pessoa_var = tk.StringVar(value="F")
        self.tipo_rural_fj_var = tk.StringVar()

        self.check_vars = {
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
        self.tipo_agente_vars = {
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

        # --- Organização da Classe ---
        self._criar_widgets()
        self._definir_valores_padrao()
        self._configurar_eventos()
        self._inicializando = False

    def _criar_widgets(self):
        """Cria e posiciona todos os widgets da interface gráfica."""
        main_canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")),
        )

        frame_id = main_canvas.create_window(
            (0, 0), window=scrollable_frame, anchor="nw"
        )
        main_canvas.configure(yscrollcommand=scrollbar.set)

        def configure_frame_width(event):
            main_canvas.itemconfig(frame_id, width=event.width)

        main_canvas.bind("<Configure>", configure_frame_width)

        # --- MUDANÇA 1: Função para lidar com o scroll do mouse ---
        def _on_mousewheel(event):
            # O fator de divisão (-120) ajusta a velocidade da rolagem
            main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        # --- MUDANÇA 2: Vincular o evento de scroll a todos os widgets ---
        main_canvas.bind_all("<MouseWheel>", _on_mousewheel)

        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        container = ttk.Frame(scrollable_frame, padding="10")
        container.pack(fill="both", expand=True)

        title_bar = tk.Label(
            container,
            text="XML - 207 - Integrador",
            bg="#005a9e",
            fg="white",
            font=("Helvetica", 12, "bold"),
            padx=10,
            pady=5,
            anchor="w",
        )
        title_bar.pack(fill="x", pady=(0, 10))

        top_radios_frame = ttk.Frame(container)
        top_radios_frame.pack(fill="x", expand=True, pady=5)

        f1 = self._criar_grupo_radio(
            top_radios_frame,
            "Tipo de Natureza",
            [("Pessoa", "pessoa"), ("Empresa", "empresa")],
            self.tipo_nome_var,
        )
        f1.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.tipo_pessoa_frame, self.tipo_pessoa_radios = self._criar_grupo_radio(
            top_radios_frame,
            "Tipo de Pessoa",
            [("Física", "F"), ("Jurídica", "J"), ("Rural", "R")],
            self.tipo_pessoa_var,
            return_widgets=True,
        )
        self.tipo_pessoa_frame.pack(side="left", fill="x", expand=True, padx=(5, 0))

        self.rural_container = self._criar_grupo_radio(
            container,
            "Tipo de Pessoa Rural",
            [("Física", "F"), ("Jurídica", "J")],
            self.tipo_rural_fj_var,
        )

        nome_frame = ttk.LabelFrame(container, text="Nome e Fantasia", padding="10")
        nome_frame.pack(fill="x", pady=10, anchor="n")
        nome_frame.columnconfigure(1, weight=1)

        ttk.Label(nome_frame, text="Nome do Agente:").grid(
            row=0, column=0, sticky="w", padx=5, pady=2
        )
        self.nome_entry = ttk.Entry(nome_frame, width=40)
        self.nome_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        ttk.Label(nome_frame, text="Nome Fantasia:").grid(
            row=1, column=0, sticky="w", padx=5, pady=2
        )
        self.fantasia_entry = ttk.Entry(nome_frame, width=40)
        self.fantasia_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        self.btn_gerar_fantasia = ttk.Button(nome_frame, text="Gerar Nome e Fantasia")
        self.btn_gerar_fantasia.grid(row=0, column=2, rowspan=2, sticky="ns", padx=10)

        self.insc_checks = self._criar_grupo_check(
            container,
            "Será gerado Inscrição?",
            [
                ("Inscrição Estadual", "checkboxInscricaoEstadual"),
                ("Inscrição Municipal", "checkboxInscricaoMunicipal"),
                ("ISENTO", "checkboxIsento"),
            ],
        )
        self.insc_checks["frame"].pack(fill="x", pady=5, anchor="n")

        local_frame = ttk.LabelFrame(container, text="Localização", padding="10")
        local_frame.pack(fill="x", pady=10, anchor="n")
        local_frame.columnconfigure(3, weight=1)

        ttk.Label(local_frame, text="Estado (UF):").grid(
            row=0, column=0, sticky="w", padx=5
        )
        estados = [
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
        self.estado_combo = ttk.Combobox(
            local_frame, values=estados, state="readonly", width=5
        )
        self.estado_combo.grid(row=0, column=1, sticky="w", padx=5)
        ttk.Label(local_frame, text="Município:").grid(
            row=0, column=2, sticky="w", padx=10
        )
        self.municipio_entry = ttk.Entry(local_frame)
        self.municipio_entry.grid(row=0, column=3, sticky="ew", padx=5)

        tipos_agente = [
            ("Cliente", "cliente"),
            ("Fornecedor", "fornecedor"),
            ("Representante", "representante"),
            ("Contato", "contato"),
            ("Transportadora", "transportadora"),
            ("Obrigação", "obrigacao"),
            ("Colaborador", "colaborador"),
            ("Outros", "outros"),
            ("Obra", "obra"),
            ("Sindicato", "sindicato"),
        ]
        self._criar_grupo_check(
            container, "Tipo do Agente", tipos_agente, self.tipo_agente_vars, columns=4
        )["frame"].pack(fill="x", pady=5, anchor="n")

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
            container, "Configurações Fiscais", configs_fiscais, columns=4
        )["frame"].pack(fill="x", pady=5, anchor="n")

        filial_frame = ttk.Frame(container, padding="10")
        filial_frame.pack(fill="x", pady=10, anchor="n")
        ttk.Label(filial_frame, text="Código da Filial (FIL_IN_CODIGO):").pack(
            side="left"
        )
        self.filial_entry = ttk.Entry(filial_frame, width=15)
        self.filial_entry.pack(side="left", padx=5)

        separator = ttk.Separator(container, orient="horizontal")
        separator.pack(fill="x", pady=10, padx=20)

        action_frame = ttk.Frame(container, padding="10")
        action_frame.pack(fill="x", anchor="n")
        action_frame.columnconfigure(0, weight=1)
        action_frame.columnconfigure(1, weight=0)
        action_frame.columnconfigure(2, weight=0)

        btn_voltar = ttk.Button(
            action_frame, text="Voltar ao Menu", command=self.destroy
        )
        btn_voltar.grid(row=0, column=1, sticky="e", padx=(0, 10))

        self.btn_gerar_xml = ttk.Button(
            action_frame, text="Gerar XML", style="Accent.TButton"
        )
        self.btn_gerar_xml.grid(row=0, column=2, sticky="e")

    def _criar_grupo_radio(self, parent, text, options, variable, return_widgets=False):
        frame = ttk.LabelFrame(parent, text=text, padding="10")
        widgets = []
        for label, value in options:
            rb = ttk.Radiobutton(frame, text=label, variable=variable, value=value)
            rb.pack(side="left", expand=True, padx=5)
            widgets.append(rb)
        if return_widgets:
            return frame, widgets
        return frame

    def _criar_grupo_check(self, parent, text, options, var_dict=None, columns=3):
        if var_dict is None:
            var_dict = self.check_vars
        frame = ttk.LabelFrame(parent, text=text, padding="10")
        widgets = {}
        for i, (label, value) in enumerate(options):
            cb = ttk.Checkbutton(frame, text=label, variable=var_dict[value])
            cb.grid(row=i // columns, column=i % columns, sticky="w", padx=5, pady=2)
            widgets[value] = cb
        return {"frame": frame, "widgets": widgets}

    def _configurar_eventos(self):
        """Associa funções (métodos) aos eventos dos widgets."""
        self.btn_gerar_fantasia.config(command=self.on_gerar_nome_fantasia)
        self.btn_gerar_xml.config(command=self.on_gerar_xml)
        self.tipo_nome_var.trace_variable("w", self._atualizar_tipo_pessoa_ui)
        self.tipo_pessoa_var.trace_variable("w", self._atualizar_tipo_rural_ui)
        self.check_vars["checkboxIsento"].trace_variable("w", self._on_isento_change)
        self.check_vars["checkboxInscricaoEstadual"].trace_variable(
            "w", self._on_inscricao_change
        )
        self.check_vars["checkboxInscricaoMunicipal"].trace_variable(
            "w", self._on_inscricao_change
        )

    def _definir_valores_padrao(self):
        """Define valores iniciais para os campos do formulário."""
        self.estado_combo.set("SP")
        self.municipio_entry.insert(0, "Itu")
        self.filial_entry.insert(0, "100")
        self._atualizar_tipo_pessoa_ui()
        self._atualizar_tipo_rural_ui()

    def _atualizar_tipo_pessoa_ui(self, *args):
        if self._inicializando:
            return
        if self.tipo_nome_var.get() == "empresa":
            for radio in self.tipo_pessoa_radios:
                if radio.cget("value") == "J":
                    radio.config(state="normal")
                    self.tipo_pessoa_var.set("J")
                else:
                    radio.config(state="disabled")
            self.rural_container.pack_forget()
        else:
            for radio in self.tipo_pessoa_radios:
                radio.config(state="normal")
            self._atualizar_tipo_rural_ui()

    def _atualizar_tipo_rural_ui(self, *args):
        if self._inicializando:
            return
        if self.tipo_nome_var.get() == "pessoa" and self.tipo_pessoa_var.get() == "R":
            self.rural_container.pack(
                fill="x", pady=5, anchor="n", before=self.nome_entry.master
            )
        else:
            self.rural_container.pack_forget()

    def _on_isento_change(self, *args):
        if self._inicializando:
            return
        is_isento = self.check_vars["checkboxIsento"].get()
        est_check = self.insc_checks["widgets"]["checkboxInscricaoEstadual"]
        mun_check = self.insc_checks["widgets"]["checkboxInscricaoMunicipal"]
        est_check.config(state="disabled" if is_isento else "normal")
        mun_check.config(state="disabled" if is_isento else "normal")
        if is_isento:
            self.check_vars["checkboxInscricaoEstadual"].set(False)
            self.check_vars["checkboxInscricaoMunicipal"].set(False)

    def _on_inscricao_change(self, *args):
        if self._inicializando:
            return
        has_any = (
            self.check_vars["checkboxInscricaoEstadual"].get()
            or self.check_vars["checkboxInscricaoMunicipal"].get()
        )
        isento_check = self.insc_checks["widgets"]["checkboxIsento"]
        isento_check.config(state="disabled" if has_any else "normal")

    def on_gerar_nome_fantasia(self):
        tipo_nome = self.tipo_nome_var.get()
        nome, fantasia = "", ""
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

    def on_gerar_xml(self):
        """Função principal que coleta dados, chama APIs e gera o XML."""
        try:
            nome = self.nome_entry.get().strip()
            fantasia = self.fantasia_entry.get().strip()
            tipo_pessoa = self.tipo_pessoa_var.get()
            estado = self.estado_combo.get().strip().upper()
            municipio = self.municipio_entry.get().strip()
            filial_codigo = self.filial_entry.get().strip()

            if not all([municipio, estado, filial_codigo, nome]):
                messagebox.showerror(
                    "Erro de Validação",
                    "Preencha os campos obrigatórios:\n- Nome do Agente\n- Estado\n- Município\n- Código da Filial",
                )
                return

            ibge_data = buscar_codigo_municipio(municipio, estado)
            endereco_data = buscar_endereco_por_municipio(municipio, estado)
            codigo_interno = get_codigo_interno_por_ibge(ibge_data["codigo"])
            email = remover_acentos(nome.lower().replace(" ", ".")) + "@exemplo.com"
            sigla_logradouro = self._inferir_tipo_logradouro(
                endereco_data["logradouro"]
            )
            bloco_pessoa = self._gerar_bloco_pessoa(tipo_pessoa)
            bloco_inscricoes = self._gerar_bloco_inscricoes()
            bloco_fiscal = self._gerar_bloco_fiscal()
            bloco_agente_id = self._gerar_bloco_agente_id()
            bloco_rural = (
                f"\n  <AGN_CH_RURALTIPOPESSOAFJ>{campo_xml(self.tipo_rural_fj_var.get())}</AGN_CH_RURALTIPOPESSOAFJ>"
                if self.tipo_pessoa_var.get() == "R"
                else ""
            )

            xml_final = f"""
<Agente OPERACAO="I">
  <AGN_ST_NOME>{campo_xml(nome, 100)}</AGN_ST_NOME>
  <AGN_ST_FANTASIA>{campo_xml(fantasia, 100)}</AGN_ST_FANTASIA>
  <TPP_IN_CODIGO>{campo_xml(tipo_pessoa)}</TPP_IN_CODIGO>
  <TAB05_IN_CODIGO>{campo_xml("1" if tipo_pessoa == "F" else "2")}</TAB05_IN_CODIGO>
  <AGN_ST_EMAIL>{campo_xml(email, 30)}</AGN_ST_EMAIL>{bloco_inscricoes}
  <PA_ST_SIGLA>BRA</PA_ST_SIGLA>
  <UF_ST_SIGLA>{campo_xml(estado)}</UF_ST_SIGLA>
  <MUN_NO_NOME>{campo_xml(municipio)}</MUN_NO_NOME>
  <MUN_IN_CODIGO>{campo_xml(codigo_interno)}</MUN_IN_CODIGO>
  <TPL_ST_SIGLA>{campo_xml(sigla_logradouro)}</TPL_ST_SIGLA>
  <AGN_ST_CEP>{campo_xml(endereco_data["cep"])}</AGN_ST_CEP>
  <AGN_ST_LOGRADOURO>{campo_xml(endereco_data["logradouro"], 50)}</AGN_ST_LOGRADOURO>
  <AGN_ST_NUMERO>{campo_xml(str(endereco_data["numero"]), 10)}</AGN_ST_NUMERO>
  <AGN_ST_BAIRRO>{campo_xml(endereco_data["bairro"], 30)}</AGN_ST_BAIRRO>{bloco_pessoa}{bloco_rural}
  <Parametros OPERACAO="I">
    <FIL_IN_CODIGO>{campo_xml(filial_codigo)}</FIL_IN_CODIGO>
  </Parametros>{bloco_agente_id}{bloco_fiscal}
</Agente>
            """.strip()

            ResultadoWindow(parent=self, xml_string=xml_final).grab_set()

        except Exception as e:
            messagebox.showerror(
                "Erro ao Gerar XML", f"Ocorreu um erro inesperado:\n\n{e}"
            )

    def _inferir_tipo_logradouro(self, logradouro=""):
        tipo = logradouro.split(" ")[0].lower()
        mapa_siglas = {"rua": "R", "avenida": "AV", "travessa": "TV", "alameda": "AL"}
        return mapa_siglas.get(tipo, tipo.upper())

    def _gerar_bloco_pessoa(self, tipo_pessoa):
        if tipo_pessoa == "F":
            return f"""\n  <PesFisica OPERACAO="I"><AGN_ST_CPF>{campo_xml(gerar_cpf())}</AGN_ST_CPF></PesFisica>"""
        elif tipo_pessoa == "J":
            return f"\n  <AGN_ST_CGC>{campo_xml(gerar_cnpj())}</AGN_ST_CGC>"
        return ""

    def _gerar_bloco_inscricoes(self):
        tags = ""
        if self.check_vars["checkboxIsento"].get():
            tags += "\n  <AGN_ST_INSCRESTADUAL>ISENTO</AGN_ST_INSCRESTADUAL>"
            tags += "\n  <AGN_ST_INSCRMUNIC>ISENTO</AGN_ST_INSCRMUNIC>"
        else:
            if self.check_vars["checkboxInscricaoEstadual"].get():
                tags += f"\n  <AGN_ST_INSCRESTADUAL>{gerar_inscricao_estadual()}</AGN_ST_INSCRESTADUAL>"
            if self.check_vars["checkboxInscricaoMunicipal"].get():
                tags += f"\n  <AGN_ST_INSCRMUNIC>{gerar_inscricao_municipal()}</AGN_ST_INSCRMUNIC>"
        return tags

    def _gerar_bloco_fiscal(self):
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
        linhas_marcadas = [
            f"    <{tag}>S</{tag}>"
            for id_check, tag in mapa_tags.items()
            if self.check_vars.get(id_check) and self.check_vars[id_check].get()
        ]
        if not linhas_marcadas:
            return ""
        return f"""\n  <Fiscal OPERACAO="I">\n    <AGN_DT_INIVIGENCIA>01/01/2000</AGN_DT_INIVIGENCIA>\n{chr(10).join(linhas_marcadas)}\n  </Fiscal>"""

    def _gerar_bloco_agente_id(self):
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
        return "".join(
            [
                f"""\n    <AgenteId OPERACAO="I"><AGN_TAU_ST_CODIGO>{campo_xml(mapa_tipo_agente.get(nome, ""))}</AGN_TAU_ST_CODIGO></AgenteId>"""
                for nome, var in self.tipo_agente_vars.items()
                if var.get()
            ]
        )


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    app = Gerador207Window(root)
    app.mainloop()
