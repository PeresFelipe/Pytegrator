import tkinter.filedialog as fd
from tkinter import messagebox

import customtkinter as ctk

from app.services.trace_service import TraceService
from app.ui.components import Card, LabeledEntry, SectionHeader, primary_button
from app.ui.theme import COLOR_BG, COLOR_TEXT, SPACE_LG, SPACE_MD


class TraceInterpreterFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=COLOR_BG)
        self.controller = controller
        self.service = TraceService()
        self.all_events = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(2, weight=1)

        SectionHeader(
            self,
            "Interpretador de Trace",
            "Carregue um JSON, filtre e revise os SQLs mais relevantes.",
        ).grid(row=0, column=0, columnspan=2, sticky="ew", padx=SPACE_LG, pady=(SPACE_LG, SPACE_MD))

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=1, column=0, columnspan=2, sticky="ew", padx=SPACE_LG, pady=(0, SPACE_MD))
        top.grid_columnconfigure(0, weight=1)

        self.filter_input = LabeledEntry(top, "Filtro")
        self.filter_input.grid(row=0, column=0, sticky="ew")

        primary_button(top, "Aplicar", self.on_apply_filter).grid(row=0, column=1, padx=(8, 0), pady=(24, 0))
        primary_button(top, "Carregar JSON", self.on_load_file).grid(row=0, column=2, padx=(8, 0), pady=(24, 0))

        left = Card(self)
        left.grid(row=2, column=0, sticky="nsew", padx=(SPACE_LG, SPACE_MD), pady=(0, SPACE_LG))
        left.grid_rowconfigure(0, weight=1)
        left.grid_columnconfigure(0, weight=1)

        self.events_list = ctk.CTkScrollableFrame(left, fg_color="transparent")
        self.events_list.grid(row=0, column=0, sticky="nsew", padx=SPACE_MD, pady=SPACE_MD)

        right = Card(self)
        right.grid(row=2, column=1, sticky="nsew", padx=(0, SPACE_LG), pady=(0, SPACE_LG))
        right.grid_rowconfigure(0, weight=1)
        right.grid_columnconfigure(0, weight=1)

        self.details_box = ctk.CTkTextbox(right, font=ctk.CTkFont(family="Consolas", size=12))
        self.details_box.grid(row=0, column=0, sticky="nsew", padx=SPACE_MD, pady=SPACE_MD)

    def on_load_file(self):
        file_path = fd.askopenfilename(
            title="Selecione o trace JSON",
            filetypes=[("JSON", "*.json"), ("Todos", "*.*")],
        )
        if not file_path:
            return

        try:
            self.all_events = self.service.load_events(file_path)
            self._render_events(self.all_events)
            self.details_box.delete("1.0", "end")
            self.details_box.insert("1.0", f"Arquivo carregado com {len(self.all_events)} evento(s).")
        except Exception as exc:
            messagebox.showerror("Erro", f"Falha ao carregar trace: {exc}")

    def on_apply_filter(self):
        filtered = self.service.apply_filters(self.all_events, self.filter_input.get())
        self._render_events(filtered)

    def _render_events(self, events):
        for child in self.events_list.winfo_children():
            child.destroy()

        if not events:
            ctk.CTkLabel(self.events_list, text="Nenhum evento encontrado.").pack(anchor="w", pady=4)
            return

        ordered = sorted(events, key=lambda e: float(e.get("duration", 0)), reverse=True)
        for index, ev in enumerate(ordered[:200], start=1):
            title = f"{index}. {ev.get('module', 'modulo')} | {ev.get('duration', 0)} ms"
            btn = ctk.CTkButton(
                self.events_list,
                text=title,
                anchor="w",
                command=lambda e=ev: self._show_event(e),
            )
            btn.pack(fill="x", padx=2, pady=3)

    def _show_event(self, event: dict):
        self.details_box.delete("1.0", "end")
        formatted_sql = self.service.format_sql(event.get("sql", ""))
        params = event.get("params", {})

        output = (
            f"Modulo: {event.get('module', 'desconhecido')}\n"
            f"Duracao: {event.get('duration', 0)} ms\n\n"
            "SQL:\n"
            f"{formatted_sql}\n\n"
            "Parametros:\n"
            f"{params}"
        )
        self.details_box.insert("1.0", output)
