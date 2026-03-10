# app/services/trace_interpreter/trace_interpreter.py
# Drawer em grid (mesma janela). Cards de eventos com quebra em underscore.
# SQL formatado + substituição de parâmetros (sem aspas duplicadas);
# "PARÂMETROS" sem ":"; "Pico de Execução" clicável.

import customtkinter as ctk
from tkinter import filedialog, messagebox
import tkinter.font as tkfont
import json
import os
import re
from PIL import Image

# ---------------------- Design Tokens (dark) ----------------------
BG_APP = ("#0B1220", "#0B1220")
SURFACE = ("#111827", "#111827")
SURFACE_ALT = ("#0F172A", "#0F172A")
BORDER = ("#1F2937", "#1F2937")
PRIMARY = ("#22C55E", "#22C55E")
PRIMARY_HOVER = ("#16A34A", "#4A7058")
ACCENT = ("#38BDF8", "#38BDF8")
ERROR = ("#F43F5E", "#F43F5E")
OK = ("#10B981", "#10B981")
TEXT = ("#E5E7EB", "#E5E7EB")
TEXT_MUTED = ("#9CA3AF", "#9CA3AF")
MONO_BG = ("#0D172A", "#0D172A")

# Largura fixa do drawer
DRAWER_WIDTH = 360
# Margens internas aproximadas para cálculo do espaço de texto:
TITLE_SIDE_GAP = 130  # px (esquerda+direita+chip)
META_SIDE_GAP = 32  # px (apenas paddings)


class TraceInterpreterFrame(ctk.CTkFrame):
    """
    Interpretador de Trace SQL com UI em CustomTkinter.

    Topo (header): [Título]  [Box Eventos (≈308x85)]  [Carregar Trace]
    Corpo        : [Sidebar de filtros]  [Painel de Detalhes (col=0)]  [Drawer de eventos (col=1)]
    """

    # ---------------------- Helpers ----------------------
    @staticmethod
    def _c(color):
        """Converte tupla de cor CTk em string, quando necessário."""
        return color[0] if isinstance(color, tuple) else color

    @staticmethod
    def _norm(s: str) -> str:
        """Normaliza string (trim + lower) para filtros."""
        return (s or "").strip().lower()

    def __init__(self, parent, controller, **kwargs):
        super().__init__(parent, **kwargs)
        self.controller = controller
        self.configure(fg_color=BG_APP)

        # Estado
        self.all_events: list[dict] = []
        self.selected_card: ctk.CTkFrame | None = None
        self.slowest_event: dict | None = None

        # Mapa eventId -> card (apenas dentro do drawer)
        self._cards_by_id: dict[str, ctk.CTkFrame] = {}

        # Drawer (lista de eventos)
        self.events_drawer: ctk.CTkFrame | None = None
        self.events_sf: ctk.CTkScrollableFrame | None = None
        self._events_canvas = None
        self._drawer_open = False
        self.right_panel: ctk.CTkFrame | None = None

        # Ícones opcionais
        self.icon_upload = self._load_icon("upload.png", (16, 16))
        self.icon_search = self._load_icon("search.png", (16, 16))
        self.icon_broom = self._load_icon("clear.png", (16, 16))
        self.icon_clock = self._load_icon("clock.png", (18, 18))
        self.icon_fire = self._load_icon("fire.png", (18, 18))

        # Fontes (mais compactas para caber melhor)
        self.font_title = ctk.CTkFont(size=9, weight="bold")
        self.font_meta = ctk.CTkFont(size=9)

        # Grid raiz
        self.grid_columnconfigure(0, weight=0)  # sidebar
        self.grid_columnconfigure(1, weight=1)  # detalhes
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_body()
        self._build_events_drawer()

    # ---------------------- Assets ----------------------
    def _load_icon(self, filename: str, size: tuple[int, int]):
        """Carrega CTkImage de app/assets (se existir), senão None."""
        path = os.path.join("app", "assets", filename)
        try:
            if os.path.exists(path):
                return ctk.CTkImage(Image.open(path), size=size)
        except Exception:
            pass
        return None

    # ---------------------- Texto com reticências ----------------------
    def _ellipsize(self, text: str, max_px: int, font: tkfont.Font) -> str:
        """
        Corta 'text' para caber em 'max_px' usando a 'font', adicionando '…' quando necessário.
        Garante linha única (sem wrap).
        """
        if not text:
            return ""
        if font.measure(text) <= max_px:
            return text
        ell = "…"
        # busca binária para performance em nomes longos
        lo, hi = 0, len(text)
        while lo < hi:
            mid = (lo + hi) // 2
            candidate = text[:mid] + ell
            if font.measure(candidate) <= max_px:
                lo = mid + 1
            else:
                hi = mid
        cut = max(0, lo - 1)
        return text[:cut] + ell

    # ---------------------- Header ----------------------
    def _build_header(self):
        """Header com Título, Box de Eventos (308x85) e botão Carregar."""
        header = ctk.CTkFrame(
            self,
            fg_color=SURFACE,
            corner_radius=12,
            border_width=1,
            border_color=BORDER,
        )
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(20, 12))

        header.grid_columnconfigure(0, weight=0)
        header.grid_columnconfigure(1, weight=1)
        header.grid_columnconfigure(2, weight=0)

        ctk.CTkLabel(
            header,
            text="Interpretador de Trace SQL",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self._c(TEXT),
        ).grid(row=0, column=0, sticky="w", padx=16, pady=12)

        # Box "Eventos" ~308x85
        self.header_events_box = ctk.CTkFrame(
            header,
            fg_color=SURFACE_ALT,
            corner_radius=10,
            border_width=1,
            border_color=BORDER,
            height=85,
            width=308,
        )
        self.header_events_box.grid(row=0, column=1, sticky="ew", padx=12, pady=8)
        self.header_events_box.grid_propagate(False)

        inner = ctk.CTkFrame(self.header_events_box, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=10, pady=8)
        inner.grid_columnconfigure(0, weight=1)
        inner.grid_columnconfigure(1, weight=0)

        ctk.CTkLabel(
            inner,
            text="Eventos",
            text_color=self._c(TEXT_MUTED),
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=0, sticky="w")
        self.header_events_info = ctk.CTkLabel(
            inner,
            text="Total: 0 • Filtrados: 0",
            text_color=self._c(TEXT_MUTED),
            justify="left",
            anchor="w",
            wraplength=280,
        )
        self.header_events_info.grid(row=1, column=0, sticky="w", pady=(2, 0))

        self.btn_abrir_lista = ctk.CTkButton(
            inner,
            text="Abrir lista",
            height=28,
            fg_color=self._c(PRIMARY),
            hover_color=self._c(PRIMARY_HOVER),
            text_color="black",
            command=self._toggle_events_drawer,
        )
        self.btn_abrir_lista.grid(row=0, column=1, rowspan=2, sticky="e")

        self.btn_carregar = ctk.CTkButton(
            header,
            text="Carregar Trace",
            image=self.icon_upload,
            compound="left",
            height=36,
            fg_color=self._c(PRIMARY),
            hover_color=self._c(PRIMARY_HOVER),
            text_color="black",
            command=self.carregar_e_processar_json,
        )
        self.btn_carregar.grid(row=0, column=2, sticky="e", padx=12, pady=12)

    # ---------------------- Corpo ----------------------
    def _build_body(self):
        """Sidebar + painel de detalhes (col=0) + coluna para drawer (col=1)."""
        # Sidebar
        self.sidebar = ctk.CTkFrame(
            self,
            fg_color=SURFACE,
            corner_radius=12,
            border_width=1,
            border_color=BORDER,
        )
        self.sidebar.grid(row=1, column=0, sticky="nsw", padx=20, pady=(0, 20))
        self.sidebar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.sidebar,
            text="Filtros",
            text_color=self._c(TEXT_MUTED),
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(14, 8))

        ctk.CTkLabel(self.sidebar, text="Campo", text_color=self._c(TEXT_MUTED)).grid(
            row=1, column=0, sticky="w", padx=14
        )
        self.field_var = ctk.StringVar(value="selecionar")
        self.field_combo = ctk.CTkComboBox(
            self.sidebar,
            variable=self.field_var,
            values=["selecionar"],
            state="disabled",
            width=220,
        )
        self.field_combo.grid(row=2, column=0, sticky="ew", padx=14, pady=(4, 10))

        ctk.CTkLabel(self.sidebar, text="Valor", text_color=self._c(TEXT_MUTED)).grid(
            row=3, column=0, sticky="w", padx=14
        )
        self.filter_value_var = ctk.StringVar()
        self.filter_value_entry = ctk.CTkEntry(
            self.sidebar,
            textvariable=self.filter_value_var,
            placeholder_text="eventId, objectName…",
        )
        self.filter_value_entry.grid(
            row=4, column=0, sticky="ew", padx=14, pady=(4, 10)
        )

        ctk.CTkLabel(self.sidebar, text="Status", text_color=self._c(TEXT_MUTED)).grid(
            row=5, column=0, sticky="w", padx=14
        )
        self.error_only_var = ctk.BooleanVar(value=False)
        self.error_seg = ctk.CTkSegmentedButton(
            self.sidebar,
            values=["Todos", "Somente erros"],
            command=self._on_error_segment,
        )
        self.error_seg.set("Todos")
        self.error_seg.grid(row=6, column=0, sticky="ew", padx=14, pady=(4, 12))

        actions = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        actions.grid(row=7, column=0, sticky="ew", padx=14, pady=(4, 14))
        actions.grid_columnconfigure((0, 1), weight=1)

        self.btn_search = ctk.CTkButton(
            actions,
            text="Pesquisar",
            image=self.icon_search,
            compound="left",
            height=34,
            fg_color=self._c(PRIMARY),
            hover_color=self._c(PRIMARY_HOVER),
            text_color="black",
            command=self.filtrar_eventos,
        )
        self.btn_search.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.btn_clear = ctk.CTkButton(
            actions,
            text="Limpar",
            image=self.icon_broom,
            compound="left",
            height=34,
            fg_color="transparent",
            border_width=1,
            border_color=BORDER,
            text_color=self._c(TEXT_MUTED),
            hover=False,
            command=self.limpar_filtros,
        )
        self.btn_clear.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        # Feedback
        self.success_frame = ctk.CTkFrame(
            self.sidebar, fg_color=SURFACE_ALT, corner_radius=10
        )
        self.success_frame.grid(row=8, column=0, sticky="ew", padx=14, pady=(4, 14))
        self.success_frame.grid_remove()
        self.success_label = ctk.CTkLabel(
            self.success_frame, text="", text_color=self._c(OK)
        )
        self.success_label.pack(fill="x", padx=10, pady=10)

        # Painel de detalhes
        right = ctk.CTkFrame(
            self,
            fg_color=SURFACE,
            corner_radius=12,
            border_width=1,
            border_color=BORDER,
        )
        right.grid(row=1, column=1, sticky="nsew", padx=(0, 20), pady=(0, 20))
        right.grid_rowconfigure(3, weight=1)
        right.grid_columnconfigure(0, weight=1)
        right.grid_columnconfigure(1, weight=0)  # drawer
        self.right_panel = right

        ctk.CTkLabel(
            right,
            text="Detalhes do Evento",
            text_color=self._c(TEXT_MUTED),
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 8))

        metrics = ctk.CTkFrame(right, fg_color="transparent")
        metrics.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))
        metrics.grid_columnconfigure((0, 1), weight=1)

        badge_now = ctk.CTkFrame(metrics, fg_color=SURFACE_ALT, corner_radius=10)
        badge_now.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ctk.CTkLabel(badge_now, image=self.icon_clock, text="").pack(
            side="left", padx=(10, 6)
        )
        self.current_exec_label = ctk.CTkLabel(
            badge_now, text="Execução Atual:\n--", text_color=self._c(TEXT)
        )
        self.current_exec_label.pack(side="left", padx=(0, 10))

        badge_peak = ctk.CTkFrame(metrics, fg_color=SURFACE_ALT, corner_radius=10)
        badge_peak.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        ctk.CTkLabel(badge_peak, image=self.icon_fire, text="").pack(
            side="left", padx=(10, 6)
        )
        self.slowest_exec_label = ctk.CTkLabel(
            badge_peak,
            text="Pico de Execução:\n--",
            text_color=self._c(TEXT),
            cursor="hand2",
        )
        self.slowest_exec_label.pack(side="left", padx=(0, 10))
        self.slowest_exec_label.bind("<Button-1>", lambda _e: self._go_to_slowest())

        self.details_text = ctk.CTkTextbox(
            right,
            font=ctk.CTkFont(family="Consolas", size=13),
            wrap="word",
            border_width=1,
            border_color=BORDER,
            fg_color=self._c(MONO_BG),
            text_color=self._c(TEXT),
            corner_radius=10,
        )
        self.details_text.grid(row=3, column=0, sticky="nsew", padx=16, pady=(4, 14))
        self.details_text.insert(
            "1.0", "Selecione um evento (Abrir lista) para visualizar os detalhes."
        )
        self.details_text.configure(state="disabled")

    # ---------------------- Drawer (lista de eventos) ----------------------
    def _build_events_drawer(self):
        """Cria o painel lateral (drawer) na coluna 1 do painel da direita."""
        if self.right_panel is None:
            return

        self.events_drawer = ctk.CTkFrame(
            self.right_panel,
            fg_color=SURFACE,
            corner_radius=10,
            border_width=1,
            border_color=BORDER,
            width=DRAWER_WIDTH,
        )
        self.events_drawer.grid(
            row=0, column=1, rowspan=4, sticky="ns", padx=(8, 8), pady=(8, 8)
        )
        self.events_drawer.grid_propagate(False)
        self.events_drawer.grid_remove()  # começa fechado

        top = ctk.CTkFrame(self.events_drawer, fg_color=SURFACE, corner_radius=10)
        top.pack(fill="x", padx=8, pady=(8, 6))
        top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            top,
            text="Eventos",
            text_color=self._c(TEXT_MUTED),
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=8, pady=(8, 6))

        close_btn = ctk.CTkButton(
            top,
            text="Fechar",
            height=28,
            fg_color="transparent",
            border_width=1,
            border_color=BORDER,
            text_color=self._c(TEXT_MUTED),
            command=self._toggle_events_drawer,
        )
        close_btn.grid(row=0, column=1, sticky="e", padx=8, pady=(8, 6))

        self.events_sf = ctk.CTkScrollableFrame(
            self.events_drawer, fg_color=SURFACE_ALT, corner_radius=10
        )
        self.events_sf.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.events_sf.grid_columnconfigure(0, weight=1)

        try:
            self._events_canvas = self.events_sf._parent_canvas
        except Exception:
            self._events_canvas = None

    def _toggle_events_drawer(self):
        """Abre/fecha o drawer e renderiza os eventos quando abrir."""
        self._drawer_open = not self._drawer_open
        if self._drawer_open:
            self._render_events_list()
            self.events_drawer.grid()
            self.btn_abrir_lista.configure(text="Fechar lista")
        else:
            if self.events_drawer:
                self.events_drawer.grid_remove()
            self.btn_abrir_lista.configure(text="Abrir lista")

    def _render_events_list(self):
        """Renderiza os cards no drawer aplicando os filtros atuais."""
        if not self.events_sf:
            return
        for w in self.events_sf.winfo_children():
            w.destroy()
        self._cards_by_id.clear()

        if not self.all_events:
            return

        field_to_filter = self.field_var.get()
        value_to_filter = self._norm(self.filter_value_var.get())
        error_only = self.error_only_var.get()

        filtered = []
        for ev in self.all_events:
            if error_only and not ev.get("errorText", ""):
                continue
            if field_to_filter != "selecionar" and value_to_filter:
                field_val = self._norm(str(ev.get(field_to_filter, "")))
                if value_to_filter not in field_val:
                    continue
            filtered.append(ev)

        for ev in filtered:
            self._create_event_card_in_drawer(ev)

    def _create_event_card_in_drawer(self, event_data: dict):
        """Cria um card clicável dentro do drawer; título quebra em underscores."""
        has_error = bool(event_data.get("errorText", ""))
        border_col = ERROR if has_error else ACCENT
        badge_text = "ERRO" if has_error else "OK"
        badge_color = ERROR if has_error else OK

        card = ctk.CTkFrame(
            self.events_sf,
            fg_color=SURFACE,
            corner_radius=10,
            border_width=1,
            border_color=BORDER,
        )
        row = len(self.events_sf.winfo_children())
        card.grid(row=row, column=0, sticky="ew", padx=8, pady=(0, 8))
        card.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 4))
        top.grid_columnconfigure(0, weight=1)
        top.grid_columnconfigure(1, weight=0)

        # Título com quebra em underscore: substitui "_" por "_\u200b" e habilita wrap
        object_name = event_data.get("objectName", "N/A")
        object_name_wrapped = str(object_name).replace("_", "_\u200b")

        title = ctk.CTkLabel(
            top,
            text=object_name_wrapped,
            font=self.font_title,
            text_color=self._c(TEXT),
            justify="left",
            anchor="w",
            wraplength=DRAWER_WIDTH - 100,
        )
        title.grid(row=0, column=0, sticky="w")

        chip = ctk.CTkLabel(
            top,
            text=badge_text,
            fg_color=badge_color,
            text_color="black",
            corner_radius=50,
            padx=8,
            pady=2,
            font=ctk.CTkFont(size=10, weight="bold"),
        )
        chip.grid(row=0, column=1, sticky="e", padx=(8, 0))

        # Meta (usuário/evento) com reticências (linha única)
        meta_raw = f"Usuário: {event_data.get('userId', 'N/A')}  •  Evento: {event_data.get('eventId', 'N/A')}"
        max_meta_px = max(80, DRAWER_WIDTH - META_SIDE_GAP)
        meta_text = self._ellipsize(meta_raw, max_meta_px, self.font_meta)

        meta = ctk.CTkLabel(
            card,
            text=meta_text,
            text_color=self._c(TEXT_MUTED),
            justify="left",
            anchor="w",
        )
        meta.grid(row=1, column=0, sticky="w", padx=10, pady=(0, 10))

        ctk.CTkFrame(card, height=2, fg_color=border_col).grid(
            row=2, column=0, sticky="ew"
        )

        def on_click(_=None, data=event_data, clicked=card):
            self.exibir_detalhes(data, clicked)

        for w in (card, top, title, chip, meta):
            w.bind("<Button-1>", on_click)
            w.configure(cursor="hand2")

        event_id = str(event_data.get("eventId", ""))
        if event_id:
            self._cards_by_id[event_id] = card

    # ---------------------- Filtros e ações ----------------------
    def _on_error_segment(self, value: str):
        """Alterna filtro 'Todos' / 'Somente erros'."""
        self.error_only_var.set(value == "Somente erros")

    def carregar_e_processar_json(self):
        """
        Abre o seletor, carrega o JSON, valida e atualiza a UI:
        - Calcula pico de execução, popula combo de campos, reseta filtros e lista.
        """
        path = filedialog.askopenfilename(
            title="Selecione o arquivo de Trace",
            filetypes=(("Arquivos JSON", "*.json"), ("Todos os arquivos", "*.*")),
        )
        if not path:
            return

        self._set_busy(True, label="Carregando...")
        try:
            with open(path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError as je:
                    messagebox.showerror(
                        "JSON inválido", f"Falha ao interpretar o JSON.\n\n{je}"
                    )
                    return

            if (
                not isinstance(data, list)
                or not data
                or not all(isinstance(e, dict) for e in data)
            ):
                messagebox.showerror(
                    "Erro de Formato",
                    "O JSON deve conter uma lista de eventos não vazia.",
                )
                return

            self.all_events = data

            filename = os.path.basename(path)
            self.success_label.configure(
                text=f"✔ Arquivo carregado com sucesso\n({filename})"
            )
            self.success_frame.grid()

            self.calcular_pico_execucao()
            self.popular_campos_de_filtro()
            self.limpar_filtros()

        except OSError as oe:
            messagebox.showerror(
                "Erro de Leitura", f"Não foi possível abrir o arquivo:\n{oe}"
            )
            self.all_events = []
            self.success_frame.grid_remove()
            self._update_header_counts(0, 0)
        except Exception as e:
            messagebox.showerror(
                "Erro Inesperado", f"Ocorreu um erro ao processar o arquivo:\n{e}"
            )
            self.all_events = []
            self.success_frame.grid_remove()
            self._update_header_counts(0, 0)
        finally:
            self._set_busy(False)

    def calcular_pico_execucao(self):
        """Determina o evento mais lento e atualiza o badge de pico."""
        if not self.all_events:
            self.slowest_event = None
            self.slowest_exec_label.configure(text="Pico de Execução:\n--")
            return

        self.slowest_event = max(self.all_events, key=lambda ev: ev.get("execution", 0))
        slowest_time = self.slowest_event.get("execution", 0)
        slowest_id = self.slowest_event.get("eventId", "N/A")
        self.slowest_exec_label.configure(
            text=f"Pico de Execução:\n{slowest_time:.3f}s (ID: {slowest_id})"
        )

    def popular_campos_de_filtro(self):
        """Preenche o combo de 'Campo' com a união das chaves dos eventos."""
        if not self.all_events:
            return
        keys = set()
        for ev in self.all_events:
            keys.update(ev.keys())
        ordered = sorted(keys)
        self.field_combo.configure(values=["selecionar"] + ordered, state="readonly")
        self.field_var.set("selecionar")

    def limpar_filtros(self):
        """Reseta filtros e re-renderiza a lista."""
        self.field_var.set("selecionar")
        self.filter_value_var.set("")
        self.error_seg.set("Todos")
        self.error_only_var.set(False)
        self.filtrar_eventos()

    def filtrar_eventos(self):
        """
        Aplica filtros; atualiza contadores do box; repopula drawer (se aberto);
        e reseta painel de detalhes.
        """
        # Reset painel de detalhes
        self.selected_card = None
        self.details_text.configure(state="normal")
        our_msg = "Selecione um evento (Abrir lista) para visualizar os detalhes."
        self.details_text.delete("1.0", "end")
        self.details_text.insert("1.0", our_msg)
        self.details_text.configure(state="disabled")
        self.current_exec_label.configure(text="Execução Atual:\n--")

        if not self.all_events:
            self._update_header_counts(0, 0)
            if self.events_sf:
                for w in self.events_sf.winfo_children():
                    w.destroy()
            return

        # Filtros atuais
        field_to_filter = self.field_var.get()
        value_to_filter = self._norm(self.filter_value_var.get())
        error_only = self.error_only_var.get()

        filtered = []
        for ev in self.all_events:
            if error_only and not ev.get("errorText", ""):
                continue
            if field_to_filter != "selecionar" and value_to_filter:
                field_val = self._norm(str(ev.get(field_to_filter, "")))
                if value_to_filter not in field_val:
                    continue
            filtered.append(ev)

        self._update_header_counts(len(self.all_events), len(filtered))

        if self._drawer_open:
            self._render_events_list()

    def _update_header_counts(self, total: int, filtered: int):
        """Atualiza a contagem no box 308x85 do header."""
        try:
            self.header_events_info.configure(
                text=f"Total: {total} • Filtrados: {filtered}"
            )
        except Exception:
            pass

    # ---------------------- Seleção / Detalhes ----------------------
    def exibir_detalhes(self, event_data: dict, clicked_card: ctk.CTkFrame | None):
        """Mostra os detalhes do evento na área de texto e destaca o card no drawer."""
        if self.selected_card:
            try:
                self.selected_card.configure(fg_color=SURFACE)
            except Exception:
                pass
        self.selected_card = clicked_card
        if self.selected_card is not None:
            try:
                self.selected_card.configure(fg_color=SURFACE_ALT)
            except Exception:
                pass

        current_time = event_data.get("execution", 0)
        try:
            self.current_exec_label.configure(
                text=f"Execução Atual:\n{float(current_time):.3f}s"
            )
        except (TypeError, ValueError):
            self.current_exec_label.configure(text=f"Execução Atual:\n{current_time}")

        details = (
            f"Nome do objeto: {event_data.get('objectName', 'N/A')}\n"
            f"ID do evento: {event_data.get('eventId', 'N/A')}\n"
            f"Tipo do evento: {event_data.get('eventType', 'N/A')}\n"
            f"Linhas afetadas: {event_data.get('rowsAffected', 'N/A')}\n"
            f"ID do usuário: {event_data.get('userId', 'N/A')}\n"
            f"Computador do usuário: {event_data.get('userComputerName', 'N/A')}\n"
            f"IP do usuário: {event_data.get('userIp', 'N/A')}\n"
        )

        raw_sql = (event_data.get("sql") or "").strip()
        params = event_data.get("parameters", [])
        formatted_sql = self._format_sql_with_params(raw_sql, params)

        params_str = ""
        if isinstance(params, list) and params:
            for p in params:
                name = str(p.get("name", "?")).lstrip(":")
                val = p.get("outValue", p.get("value", "N/A"))
                params_str += f"  {name} = {val}\n"

        full_details = f"{details}\n"
        if formatted_sql:
            full_details += f"---------- SQL ----------\n{formatted_sql}\n\n"
        if params_str:
            full_details += f"---------- PARÂMETROS ----------\n{params_str}"
        if event_data.get("errorText"):
            full_details += f"\n---------- ERRO ----------\n{event_data['errorText']}"

        self.details_text.configure(state="normal")
        self.details_text.delete("1.0", "end")
        self.details_text.insert("1.0", full_details)
        self.details_text.configure(state="disabled")

    # ---------------------- Estado / Navegação ----------------------
    def _set_busy(self, busy: bool, label: str = "Carregar Trace"):
        """Habilita/Desabilita o botão de upload, indicando estado busy."""
        try:
            if busy:
                self.btn_carregar.configure(text=label, state="disabled")
            else:
                self.btn_carregar.configure(text="Carregar Trace", state="normal")
        except Exception:
            pass

    def _go_to_slowest(self):
        """Abre o drawer (se necessário) e rola até o card do evento mais lento."""
        if not self.slowest_event:
            return
        if not self._drawer_open:
            self._toggle_events_drawer()

        event_id = str(self.slowest_event.get("eventId", ""))
        if not event_id:
            return

        if event_id not in self._cards_by_id:
            self.limpar_filtros()
            self.after(80, self._go_to_slowest)
            return

        card = self._cards_by_id.get(event_id)
        if not card:
            return

        self.exibir_detalhes(self.slowest_event, card)
        self._scroll_to_card(card)

    def _scroll_to_card(self, card: ctk.CTkFrame):
        """Rola o scroll do drawer até o card (best effort)."""
        try:
            canvas = self._events_canvas
            if not canvas or not self.events_sf:
                return
            total = max(1, self.events_sf.winfo_reqheight())
            y = max(0, card.winfo_y() - 20)
            canvas.yview_moveto(y / total)
        except Exception:
            pass

    # ---------------------- SQL: substituição e formatação ----------------------
    def _format_sql_with_params(self, sql: str, params: list) -> str:
        """
        Substitui :NOME por valores (quoting) e formata o SQL.
        Evita aspas triplas quando o valor já vem entre aspas no trace.
        Evita aspas duplicadas quando o placeholder já está entre aspas no SQL.
        """
        if not sql:
            return ""

        original_sql = sql

        # Mapa nome->valor
        param_map: dict[str, object] = {}
        if isinstance(params, list):
            for p in params:
                name = str(p.get("name", "")).lstrip(":")
                value = p.get("outValue", p.get("value", None))
                if name:
                    param_map[name] = value

        def _is_number(text: str) -> bool:
            try:
                float(text.strip())
                return True
            except Exception:
                return False

        def _format_val(v) -> str:
            # Trata None / "NULL" / "<NULL>"
            if v is None:
                return "NULL"
            if isinstance(v, str):
                s = v.strip()
                u = s.upper()
                if u in {"NULL", "<NULL>"}:
                    return "NULL"
                # Se JÁ vem entre aspas simples do trace (ex.: "'G'"), retorna como está.
                if len(s) >= 2 and s[0] == "'" and s[-1] == "'":
                    return s
                # Números (sem aspas)
                if _is_number(s):
                    return s
                # Demais strings -> quote + escape
                return "'" + s.replace("'", "''") + "'"
            if isinstance(v, (int, float)):
                return str(v)
            # fallback
            s = str(v)
            return "'" + s.replace("'", "''") + "'"

        # regex :PARAM
        pattern = re.compile(r":([A-Za-z_][\w$]*)")

        def _replace(m: re.Match) -> str:
            key = m.group(1)
            # pega valor (case-insensitive)
            val = None
            if key in param_map:
                val = param_map[key]
            else:
                for k, v in param_map.items():
                    if k.lower() == key.lower():
                        val = v
                        break

            if val is None and key not in param_map:
                return m.group(0)  # sem valor → mantém placeholder

            formatted = _format_val(val)

            # Se placeholder já está entre aspas no SQL, e 'formatted' também foi aspado, remove aspas externas do formatted
            start, end = m.start(), m.end()
            left_char = original_sql[start - 1] if start - 1 >= 0 else ""
            right_char = original_sql[end] if end < len(original_sql) else ""
            if (
                left_char == "'"
                and right_char == "'"
                and len(formatted) >= 2
                and formatted[0] == "'"
                and formatted[-1] == "'"
            ):
                return formatted[1:-1]

            return formatted

        sql_sub = pattern.sub(_replace, original_sql)
        return self._pretty_sql(sql_sub)

    def _pretty_sql(self, sql: str) -> str:
        """Formata SQL com quebras básicas (SELECT, FROM, WHERE, AND/OR)."""
        s = sql.strip()
        s = re.sub(r"[ \t]+", " ", s)

        break_before = [
            r"SELECT",
            r"FROM",
            r"WHERE",
            r"GROUP BY",
            r"HAVING",
            r"ORDER BY",
            r"UNION",
            r"UNION ALL",
            r"EXCEPT",
            r"INTERSECT",
            r"LEFT JOIN",
            r"RIGHT JOIN",
            r"FULL JOIN",
            r"INNER JOIN",
            r"OUTER JOIN",
            r"JOIN",
            r"UPDATE",
            r"SET",
            r"INSERT INTO",
            r"VALUES",
            r"DELETE FROM",
            r"ON",
        ]
        for kw in sorted(break_before, key=len, reverse=True):
            pattern = r"(?i)\b" + kw + r"\b"
            s = re.sub(pattern, lambda m: "\n" + m.group(0).upper(), s)

        s = re.sub(r"(?i)\bAND\b", lambda m: "\n  AND", s)
        s = re.sub(r"(?i)\bOR\b", lambda m: "\n  OR", s)

        s = s.lstrip()
        s = re.sub(r"\n{2,}", "\n", s)
        return s
