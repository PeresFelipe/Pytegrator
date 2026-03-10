import tkinter as tk
from tkinter import ttk


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Exemplo de Lógica Rural")
        self.geometry("400x300")

        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)

        # --- Variável de Controle ---
        # Esta variável vai armazenar o valor do Radiobutton selecionado ('U' ou 'R')
        self.tipo_pessoa_var = tk.StringVar(value="U")  # 'U' de Urbano é o valor padrão

        # --- Registra o Callback ---
        # A função self.on_tipo_pessoa_change será chamada toda vez que o valor mudar.
        # 'w' significa que o trace é para eventos de 'write' (escrita/mudança).
        self.tipo_pessoa_var.trace_add("w", self.on_tipo_pessoa_change)

        # --- Grupo de Radiobuttons ---
        tipo_pessoa_frame = ttk.LabelFrame(main_frame, text="Tipo de Pessoa")
        tipo_pessoa_frame.pack(pady=10, fill="x")

        urbano_rb = ttk.Radiobutton(
            tipo_pessoa_frame,
            text="Urbano",
            variable=self.tipo_pessoa_var,
            value="U",  # Valor que a variável terá se este for selecionado
        )
        urbano_rb.pack(side="left", padx=10)

        rural_rb = ttk.Radiobutton(
            tipo_pessoa_frame,
            text="Rural",
            variable=self.tipo_pessoa_var,
            value="R",  # Valor que a variável terá se este for selecionado
        )
        rural_rb.pack(side="left", padx=10)

        # --- Container que será mostrado/escondido ---
        # Este é o seu 'tipoRuralFJContainer'
        self.rural_container = ttk.LabelFrame(
            main_frame, text="Opções para Produtor Rural"
        )
        # Note que ele NÃO é adicionado à tela com .pack() ainda.

        # Conteúdo de exemplo para o container rural
        ttk.Checkbutton(self.rural_container, text="Pessoa Física").pack(
            anchor="w", padx=10
        )
        ttk.Checkbutton(self.rural_container, text="Pessoa Jurídica").pack(
            anchor="w", padx=10
        )

        # --- Chamada Inicial ---
        # Chama a função uma vez no início para garantir que o estado inicial está correto.
        # Equivalente ao seu listener 'DOMContentLoaded'.
        self.on_tipo_pessoa_change()

    def on_tipo_pessoa_change(self, *args):
        """
        Callback executado sempre que um Radiobutton de tipo de pessoa é clicado.
        O '*args' é necessário porque o trace passa argumentos extras que não usamos.
        """
        # Pega o valor atual da variável de controle
        valor_selecionado = self.tipo_pessoa_var.get()

        print(f"Tipo de pessoa mudou para: {valor_selecionado}")

        if valor_selecionado == "R":
            # Se for 'Rural', mostra o container
            print("Mostrando container de opções rurais.")
            # O .pack() adiciona o widget à tela.
            self.rural_container.pack(
                pady=10, fill="x", before=None
            )  # 'before=None' garante que ele vá para o final
        else:
            # Se for qualquer outra coisa, esconde o container
            print("Escondendo container de opções rurais.")
            # O .pack_forget() remove o widget da tela, mas ele continua existindo na memória.
            self.rural_container.pack_forget()


# Bloco para rodar a aplicação de exemplo
if __name__ == "__main__":
    app = App()
    app.mainloop()
