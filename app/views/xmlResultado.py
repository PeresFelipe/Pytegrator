import tkinter as tk
from tkinter import ttk, messagebox


class ResultadoWindow(tk.Toplevel):
    """
    Uma janela para exibir um XML gerado, com opções para copiar e voltar.
    """

    def __init__(self, parent, xml_string: str):
        """
        Inicializa a janela.
        :param parent: A janela pai que está chamando esta.
        :param xml_string: A string XML a ser exibida.
        """
        super().__init__(parent)
        self.title("XML Gerado")
        self.geometry("700x550")
        self.minsize(500, 400)

        # Armazena o XML recebido para uso nos métodos
        self.xml_string = xml_string

        # --- Organização da Classe ---
        self._criar_widgets()
        self._configurar_eventos()
        self._popular_dados()

    def _criar_widgets(self):
        """Cria e posiciona todos os widgets da interface (o "HTML" em Python)."""

        # Container principal
        container = ttk.Frame(self, padding="10")
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)  # Faz a coluna expandir

        # Título estilo Delphi
        title_bar = tk.Label(
            container,
            text="XML Gerado com sucesso",
            bg="#005a9e",
            fg="white",
            font=("Helvetica", 12, "bold"),
            padx=10,
            pady=5,
            anchor="w",
        )
        title_bar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        # Frame para o campo de texto e a barra de rolagem
        text_frame = ttk.Frame(container)
        text_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")
        text_frame.rowconfigure(0, weight=1)
        text_frame.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)  # Faz a linha do texto expandir

        # Campo de texto para exibir o XML
        self.xml_text = tk.Text(
            text_frame,
            wrap="word",  # Quebra a linha
            font=("Consolas", 10),
            padx=5,
            pady=5,
            borderwidth=1,
            relief="solid",
        )
        self.xml_text.grid(row=0, column=0, sticky="nsew")

        # Barra de rolagem para o campo de texto
        scrollbar = ttk.Scrollbar(
            text_frame, orient="vertical", command=self.xml_text.yview
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.xml_text.config(yscrollcommand=scrollbar.set)

        # Mensagem de "copiado" (inicialmente invisível)
        self.copiado_label = ttk.Label(
            container, text="XML copiado!", foreground="green"
        )

        # Frame para os botões de ação
        button_frame = ttk.Frame(container)
        button_frame.grid(row=2, column=0, columnspan=2, sticky="e", pady=(10, 0))

        self.copiar_button = ttk.Button(button_frame, text="Copiar XML")
        self.copiar_button.pack(side="left", padx=5)

        self.voltar_button = ttk.Button(button_frame, text="Voltar")
        self.voltar_button.pack(side="left")

    def _configurar_eventos(self):
        """Associa funções aos eventos dos botões (o "JS" em Python)."""
        self.copiar_button.config(command=self.copiar_xml)
        self.voltar_button.config(command=self.destroy)  # 'destroy' fecha a janela

    def _popular_dados(self):
        """Insere o XML recebido no campo de texto."""
        if self.xml_string:
            self.xml_text.insert("1.0", self.xml_string)
        else:
            self.xml_text.insert("1.0", "Nenhum XML foi gerado ou recebido.")

        # Desabilita a edição do campo de texto
        self.xml_text.config(state="disabled")

    # --- Métodos de Lógica ---

    def copiar_xml(self):
        """Copia o conteúdo XML para a área de transferência."""
        try:
            self.clipboard_clear()  # Limpa a área de transferência
            self.clipboard_append(self.xml_string)  # Adiciona o XML
            self.update()  # Garante que a área de transferência seja atualizada

            # Mostra a mensagem de sucesso
            self.copiado_label.grid(row=2, column=0, sticky="w", padx=5)

            # Agenda o desaparecimento da mensagem após 2 segundos (2000 ms)
            self.after(2000, lambda: self.copiado_label.grid_forget())

        except Exception as e:
            print(f"Erro ao copiar para a área de transferência: {e}")
            messagebox.showerror(
                "Erro de Cópia",
                "Não foi possível copiar o XML para a área de transferência.",
            )


# --- Bloco para Teste Independente ---
if __name__ == "__main__":
    # Este código permite testar a janela de resultado de forma isolada.
    # Crie uma janela raiz temporária
    root = tk.Tk()
    root.withdraw()  # Esconde a janela raiz, pois só queremos ver a de resultado

    # Crie um XML de exemplo
    exemplo_xml = """
<Agente OPERACAO="I">
  <AGN_ST_NOME>Teste de Nome Completo</AGN_ST_NOME>
  <AGN_ST_FANTASIA>Fantasia Tech</AGN_ST_FANTASIA>
  <TPP_IN_CODIGO>J</TPP_IN_CODIGO>
  <!-- ... mais tags ... -->
</Agente>
    """.strip()

    # Crie e exiba a janela de resultado, passando o XML
    resultado_app = ResultadoWindow(parent=root, xml_string=exemplo_xml)

    # Faz com que a aplicação espere até que a janela de resultado seja fechada
    resultado_app.wait_window()
