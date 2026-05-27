"""
Módulo de Passageiros - Fase 3
------------------------------
Este arquivo contém a classe PassageirosFrame, que implementa a interface
e a lógica de banco de dados (CRUD) para gerenciar passageiros usando 
CustomTkinter e ttk.Treeview.
"""

import sqlite3
import os
import customtkinter as ctk
from tkinter import ttk, messagebox, Menu

# Caminho absoluto para o banco de dados
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "sistema_viagens.db")

class PassageirosFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        # Herda a cor transparente para pegar a cor de fundo do Main Frame (#E4F7FE)
        super().__init__(master, fg_color="transparent", **kwargs)

        # Configuração do Grid do Frame (2 linhas: ferramentas e tabela)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._construir_ferramentas()
        self._construir_tabela()
        
        # Carrega os dados ao iniciar
        self.carregar_passageiros()

    def _conectar(self):
        """Abre e retorna a conexão com o banco de dados SQLite."""
        # Se o script rodar da pasta raiz ou da pasta pages, garantimos que acha o DB
        caminho = DB_PATH if os.path.exists(DB_PATH) else "sistema_viagens.db"
        return sqlite3.connect(caminho)

    def _construir_ferramentas(self):
        """Constrói a barra superior com campo de busca e botões de ação."""
        frame_top = ctk.CTkFrame(self, fg_color="transparent")
        frame_top.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))

        # --- Busca ---
        self.entry_busca = ctk.CTkEntry(
            frame_top, 
            placeholder_text="Buscar por nome, CPF...", 
            width=250,
            fg_color="white",
            text_color="#192E33",
            border_color="#3D7BA3"
        )
        self.entry_busca.pack(side="left", padx=(0, 10))

        btn_buscar = ctk.CTkButton(
            frame_top, 
            text="🔍 Pesquisar", 
            width=100,
            fg_color="#3D7BA3",
            hover_color="#2A5A7A",
            command=lambda: self.carregar_passageiros(self.entry_busca.get())
        )
        btn_buscar.pack(side="left")

        # --- Os botões de Editar e Excluir foram movidos para o Menu de Contexto na tabela ---

        btn_novo = ctk.CTkButton(
            frame_top, 
            text="＋ Novo Passageiro", 
            width=140, 
            fg_color="#FF9940",      # Laranja vibrante
            hover_color="#E07820",
            text_color="white",
            font=ctk.CTkFont(weight="bold"),
            command=lambda: self.abrir_formulario()
        )
        btn_novo.pack(side="right", padx=(10, 0))

    def _construir_tabela(self):
        """Constrói a área de listagem usando ttk.Treeview com estilo limpo."""
        frame_tabela = ctk.CTkFrame(self, fg_color="transparent")
        frame_tabela.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        frame_tabela.grid_rowconfigure(0, weight=1)
        frame_tabela.grid_columnconfigure(0, weight=1)

        # --- Estilização do Treeview ---
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Treeview", 
            background="white", 
            foreground="#192E33", 
            rowheight=30, 
            fieldbackground="white",
            borderwidth=0
        )
        style.configure(
            "Treeview.Heading", 
            background="#3D7BA3", 
            foreground="white", 
            font=("Segoe UI", 10, "bold"),
            borderwidth=0
        )
        style.map("Treeview", background=[("selected", "#D0EAF5")], foreground=[("selected", "#192E33")])

        # --- Configuração das Colunas ---
        colunas = ("ID", "Nome Completo", "Nascimento", "RG", "CPF", "WhatsApp")
        self.tree = ttk.Treeview(frame_tabela, columns=colunas, show="headings", style="Treeview")

        # Cabeçalhos e larguras
        larguras = {"ID": 50, "Nome Completo": 250, "Nascimento": 100, "RG": 120, "CPF": 120, "WhatsApp": 120}
        for col in colunas:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=larguras[col], anchor="center" if col != "Nome Completo" else "w")

        self.tree.grid(row=0, column=0, sticky="nsew")

        # --- Scrollbar ---
        scrollbar = ttk.Scrollbar(frame_tabela, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        # --- Menu de Contexto (Botão Direito) ---
        self.menu_contexto = Menu(self, tearoff=False, font=("Segoe UI", 10))
        self.menu_contexto.add_command(label="✏️ Editar Passageiro", command=self._editar_selecionado)
        self.menu_contexto.add_separator()
        self.menu_contexto.add_command(label="🗑️ Excluir Passageiro", command=self.excluir_passageiro)

        # Binds de Eventos
        self.tree.bind("<Double-1>", lambda e: self._editar_selecionado())  # Duplo clique
        self.tree.bind("<Button-3>", self._exibir_menu_contexto)            # Botão direito

    def _exibir_menu_contexto(self, event):
        """Seleciona a linha clicada com o botão direito e exibe o menu de opções."""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.menu_contexto.post(event.x_root, event.y_root)

    # =======================================================================
    # Integração com Banco de Dados
    # =======================================================================

    def carregar_passageiros(self, busca=""):
        """Busca os dados no banco e preenche o Treeview."""
        # Limpa os itens atuais do Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        conn = self._conectar()
        cursor = conn.cursor()

        termo = f"%{busca}%"
        query = """
            SELECT id, nome_completo, data_nascimento, rg, cpf, whatsapp 
            FROM passageiros
            WHERE nome_completo LIKE ? OR cpf LIKE ?
            ORDER BY nome_completo
        """
        cursor.execute(query, (termo, termo))
        registros = cursor.fetchall()
        conn.close()

        for linha in registros:
            # Substitui None por strings vazias ou traços
            valores = [str(v) if v else "—" for v in linha]
            self.tree.insert("", "end", values=valores)

    # =======================================================================
    # Janela de Formulário (Cadastrar / Editar)
    # =======================================================================

    def _editar_selecionado(self):
        """Captura a linha selecionada para edição."""
        selecionado = self.tree.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um passageiro para editar.")
            return
        
        # Pega os valores da linha (ID é o índice 0)
        valores = self.tree.item(selecionado[0], "values")
        id_passageiro = int(valores[0])
        self.abrir_formulario(id_passageiro)

    def abrir_formulario(self, id_passageiro=None):
        """Abre a janela modal para cadastrar ou editar um passageiro."""
        janela = ctk.CTkToplevel(self)
        janela.title("Editar Passageiro" if id_passageiro else "Cadastrar Passageiro")
        janela.geometry("450x450")
        janela.configure(fg_color="#192E33")  # Fundo escuro
        janela.resizable(False, False)
        janela.grab_set()  # Impede interação com a janela principal

        # Centraliza
        janela.update_idletasks()
        x = (janela.winfo_screenwidth() // 2) - (450 // 2)
        y = (janela.winfo_screenheight() // 2) - (450 // 2)
        janela.geometry(f"+{x}+{y}")

        ctk.CTkLabel(
            janela, 
            text="Dados do Passageiro", 
            font=ctk.CTkFont(size=20, weight="bold"), 
            text_color="white"
        ).pack(pady=(20, 15))

        # Campos
        campos = {}
        chaves = [("nome", "Nome Completo *"), ("nascimento", "Data de Nascimento"), 
                  ("rg", "RG"), ("cpf", "CPF"), ("whatsapp", "WhatsApp")]

        for chave, label in chaves:
            ctk.CTkLabel(janela, text=label, text_color="white").pack(anchor="w", padx=40)
            
            entry = ctk.CTkEntry(janela, width=370, fg_color="#2A4A52", border_color="#3D7BA3", text_color="white")
            entry.pack(padx=40, pady=(0, 10))
            campos[chave] = entry
            
            # Adicionar máscara dependendo do campo
            if chave == "nascimento":
                def format_data(event, widget=entry):
                    if event.keysym in ('BackSpace', 'Delete', 'Left', 'Right'): return
                    text = widget.get().replace("/", "")
                    if len(text) > 8: text = text[:8]
                    res = ""
                    for i, c in enumerate(text):
                        if i in [2, 4]: res += "/"
                        res += c
                    if widget.get() != res:
                        widget.delete(0, "end")
                        widget.insert(0, res)
                entry.bind("<KeyRelease>", format_data)
                
            elif chave == "cpf":
                def format_cpf(event, widget=entry):
                    if event.keysym in ('BackSpace', 'Delete', 'Left', 'Right'): return
                    text = widget.get().replace(".", "").replace("-", "")
                    if len(text) > 11: text = text[:11]
                    res = ""
                    for i, c in enumerate(text):
                        if i in [3, 6]: res += "."
                        elif i == 9: res += "-"
                        res += c
                    if widget.get() != res:
                        widget.delete(0, "end")
                        widget.insert(0, res)
                entry.bind("<KeyRelease>", format_cpf)

        # Se for edição, preenche os campos
        if id_passageiro:
            conn = self._conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT nome_completo, data_nascimento, rg, cpf, whatsapp FROM passageiros WHERE id=?", (id_passageiro,))
            dados = cursor.fetchone()
            conn.close()

            if dados:
                campos["nome"].insert(0, dados[0] or "")
                campos["nascimento"].insert(0, dados[1] or "")
                campos["rg"].insert(0, dados[2] or "")
                campos["cpf"].insert(0, dados[3] or "")
                campos["whatsapp"].insert(0, dados[4] or "")

        # Botão Salvar
        def salvar():
            nome = campos["nome"].get().strip()
            nascimento = campos["nascimento"].get().strip()
            rg = campos["rg"].get().strip()
            cpf = campos["cpf"].get().strip()
            whatsapp = campos["whatsapp"].get().strip()

            if not nome:
                messagebox.showwarning("Aviso", "O campo 'Nome Completo' é obrigatório.", parent=janela)
                return

            conn = self._conectar()
            cursor = conn.cursor()

            try:
                if id_passageiro:
                    cursor.execute("""
                        UPDATE passageiros 
                        SET nome_completo=?, data_nascimento=?, rg=?, cpf=?, whatsapp=?
                        WHERE id=?
                    """, (nome, nascimento, rg, cpf, whatsapp, id_passageiro))
                    msg = "Passageiro atualizado com sucesso!"
                else:
                    cursor.execute("""
                        INSERT INTO passageiros (nome_completo, data_nascimento, rg, cpf, whatsapp)
                        VALUES (?, ?, ?, ?, ?)
                    """, (nome, nascimento, rg, cpf, whatsapp))
                    msg = "Passageiro cadastrado com sucesso!"
                
                conn.commit()
                messagebox.showinfo("Sucesso", msg, parent=janela)
                self.carregar_passageiros()
                janela.destroy()
            except Exception as e:
                messagebox.showerror("Erro", f"Ocorreu um erro ao salvar:\n{e}", parent=janela)
            finally:
                conn.close()

        ctk.CTkButton(
            janela, text="💾 Salvar", fg_color="#FF9940", hover_color="#E07820", 
            text_color="white", font=ctk.CTkFont(weight="bold"), height=40, command=salvar
        ).pack(pady=20)

    # =======================================================================
    # Lógica de Exclusão
    # =======================================================================

    def excluir_passageiro(self):
        """Identifica a linha selecionada e deleta o registro do banco."""
        selecionado = self.tree.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um passageiro para excluir.")
            return

        valores = self.tree.item(selecionado[0], "values")
        id_passageiro = int(valores[0])
        nome = valores[1]

        if messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir '{nome}'?"):
            conn = self._conectar()
            try:
                conn.execute("DELETE FROM passageiros WHERE id=?", (id_passageiro,))
                conn.commit()
                messagebox.showinfo("Sucesso", "Passageiro excluído!")
                self.carregar_passageiros()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao excluir:\n{e}")
            finally:
                conn.close()


# ===========================================================================
# INSTRUÇÕES PARA INTEGRAÇÃO NO main.py
# ===========================================================================
"""
Para integrar este frame ao arquivo 'main.py', você deve:

1. No topo de 'main.py', faça o import da classe:
   from pages.passageiros import PassageirosFrame

2. Atualize o seu dicionário de rotas na função `_carregar_pagina` (ou onde 
   você controla o clique do botão) para instanciar a classe e adicioná-la à tela:

   # Exemplo de como deve ficar a lógica no main.py:
   rotas = {
       "Passageiros": PassageirosFrame,
   }

   # Se a página existir, ela é instanciada e carregada no main frame:
   if nome_pagina in rotas:
       pagina = rotas[nome_pagina](self.frame_principal)
       pagina.pack(fill="both", expand=True)

(Caso o seu dicionário já esteja usando `PassageirosPage`, basta substituir o 
import para carregar a `PassageirosFrame` criada acima).
"""
