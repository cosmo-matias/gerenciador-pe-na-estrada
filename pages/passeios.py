"""
Módulo de Passeios - Fase 4 e Refatoração Kanban
------------------------------------------------
Este arquivo contém a classe PasseiosFrame, que implementa a interface
em formato de Kanban e o CRUD para gerenciar os passeios
da agência Pé Na Estrada Tour.
"""

import sqlite3
import os
import customtkinter as ctk
from tkinter import messagebox
from pages.mapa_onibus import MapaOnibusWindow

# Caminho absoluto para o banco de dados
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "sistema_viagens.db")

class PasseiosFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        # Fundo transparente para herdar o azul claro do Main Frame (#E4F7FE)
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._construir_cabecalho()
        self._construir_scrollable_area()
        
        # Carrega os encartes ao iniciar
        self.carregar_passeios()

    def _conectar(self):
        """Abre e retorna a conexão com o banco de dados SQLite."""
        caminho = DB_PATH if os.path.exists(DB_PATH) else "sistema_viagens.db"
        return sqlite3.connect(caminho)

    def _construir_cabecalho(self):
        """Barra superior com título e botão de Novo Passeio."""
        frame_top = ctk.CTkFrame(self, fg_color="transparent")
        frame_top.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 12))

        ctk.CTkLabel(
            frame_top,
            text="🗺️  Passeios e Excursões (Kanban)",
            font=ctk.CTkFont(family="Segoe UI", size=26, weight="bold"),
            text_color="#192E33"
        ).pack(side="left")

        ctk.CTkButton(
            frame_top,
            text="＋ Novo Passeio",
            width=150,
            height=40,
            fg_color="#FF9940",      # Laranja vibrante
            hover_color="#E07820",
            text_color="white",
            font=ctk.CTkFont(weight="bold", size=14),
            command=self.abrir_formulario
        ).pack(side="right")

    def _construir_scrollable_area(self):
        """Área principal dividida em 3 colunas (Kanban)."""
        self.kanban_container = ctk.CTkFrame(self, fg_color="transparent")
        self.kanban_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.kanban_container.grid_columnconfigure((0, 1, 2), weight=1)
        self.kanban_container.grid_rowconfigure(0, weight=1) # Linha que segura as colunas expande verticalmente

        self.colunas_kanban = {}
        
        status_cols = [
            ("A realizar", "#3D7BA3"),  # Azul Principal
            ("Finalizado", "#27AE60"),  # Verde
            ("Cancelado", "#C0392B")    # Vermelho
        ]
        
        for idx, (status, cor) in enumerate(status_cols):
            # Frame pai da coluna
            col_frame = ctk.CTkFrame(self.kanban_container, fg_color="transparent")
            col_frame.grid(row=0, column=idx, sticky="nsew", padx=8)
            
            # Título da coluna
            ctk.CTkLabel(
                col_frame, 
                text=status,
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color="white",
                fg_color=cor,
                corner_radius=8,
                height=35
            ).pack(fill="x", pady=(0, 10))
            
            # Área rolável da coluna
            scroll = ctk.CTkScrollableFrame(
                col_frame,
                fg_color="transparent",
                scrollbar_button_color="#BDDDE8",
                scrollbar_button_hover_color=cor
            )
            scroll.pack(fill="both", expand=True)
            
            self.colunas_kanban[status] = scroll

    # =======================================================================
    # Integração com Banco de Dados e Renderização
    # =======================================================================

    def carregar_passeios(self):
        """Busca os passeios no banco e renderiza os encartes nas colunas."""
        # Limpa todos os encartes atuais em todas as colunas
        for scroll in self.colunas_kanban.values():
            for widget in scroll.winfo_children():
                widget.destroy()

        conn = self._conectar()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                p.id, p.destino, p.locais_embarque, p.local_destino, p.data_passeio, p.hora_saida, 
                p.hora_retorno, p.capacidade, p.valor_passeio, p.status,
                COUNT(a.id) AS vagas_ocupadas
            FROM passeios p
            LEFT JOIN alocacao_poltronas a ON p.id = a.passeio_id
            GROUP BY p.id
            ORDER BY p.data_passeio ASC
        """
        cursor.execute(query)
        passeios = cursor.fetchall()
        conn.close()

        # Estado Vazio
        if not passeios:
            for scroll in self.colunas_kanban.values():
                ctk.CTkLabel(
                    scroll, text="Vazio", font=ctk.CTkFont(size=14, slant="italic"), text_color="#3D7BA3"
                ).pack(pady=20)
            return

        # Renderiza o card na respectiva coluna
        for passeio in passeios:
            status = passeio[9]
            # Caso o status seja inválido/nulo, joga no "A realizar"
            scroll_dest = self.colunas_kanban.get(status, self.colunas_kanban["A realizar"])
            self._criar_encarte(passeio, scroll_dest)

    def _criar_encarte(self, passeio, parent_container):
        """Cria um Card individual para o passeio, adaptado para 1/3 da tela."""
        (id_pass, destino, locais_embarque, local_destino, data_pass, hora_saida, 
         hora_retorno, capacidade, valor, status, vagas_ocupadas) = passeio

        # Container principal do Card
        card = ctk.CTkFrame(parent_container, fg_color="white", corner_radius=12)
        card.pack(fill="x", pady=6, padx=4)

        # Destino
        ctk.CTkLabel(
            card, text=destino, font=ctk.CTkFont(size=18, weight="bold"), text_color="#192E33"
        ).pack(anchor="w", padx=16, pady=(12, 4))
        
        # Detalhes textuais compactos
        detalhes = f"📍 {local_destino or '—'}\n🗓️ {data_pass}\n⏰ {hora_saida or '--:--'} às {hora_retorno or '--:--'}\n💰 R$ {valor if valor else 0.00:.2f}"
        ctk.CTkLabel(
            card, text=detalhes, font=ctk.CTkFont(size=13), text_color="#3D7BA3", justify="left"
        ).pack(anchor="w", padx=16, pady=(0, 10))
        
        # Progresso de Ocupação
        progresso = vagas_ocupadas / capacidade if capacidade > 0 else 0
        ctk.CTkLabel(
            card, text=f"Ocupação: {vagas_ocupadas}/{capacidade}", 
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#192E33"
        ).pack(anchor="w", padx=16)
        
        barra = ctk.CTkProgressBar(card, height=10, progress_color="#FF9940", fg_color="#E4F7FE")
        barra.pack(fill="x", padx=16, pady=(2, 12))
        barra.set(progresso)
        
        # Divisor
        ctk.CTkFrame(card, height=1, fg_color="#E4F7FE").pack(fill="x", padx=16)

        # Botões de Ação Inferiores (Empilhados para caber)
        frame_botoes = ctk.CTkFrame(card, fg_color="transparent")
        frame_botoes.pack(fill="x", padx=16, pady=12)
        
        frame_botoes.grid_columnconfigure((0, 1), weight=1)
        
        ctk.CTkButton(
            frame_botoes, text="✏️ Editar", fg_color="#3D7BA3", hover_color="#2A5A7A", height=32,
            command=lambda id_p=id_pass: self.abrir_formulario(id_p)
        ).grid(row=0, column=0, padx=(0, 4), sticky="ew")

        ctk.CTkButton(
            frame_botoes, text="🗑️ Excluir", fg_color="#C0392B", hover_color="#962A20", height=32,
            command=lambda id_p=id_pass, dest=destino: self.excluir_passeio(id_p, dest)
        ).grid(row=0, column=1, padx=(4, 0), sticky="ew")

        ctk.CTkButton(
            frame_botoes, text="🚌 Gerenciar Poltronas", fg_color="#192E33", hover_color="#0F1C1F", height=36, font=ctk.CTkFont(weight="bold"),
            command=lambda id_p=id_pass: MapaOnibusWindow(self, id_p)
        ).grid(row=1, column=0, columnspan=2, pady=(8, 0), sticky="ew")


    # =======================================================================
    # Formulário (Cadastrar / Editar)
    # =======================================================================

    def abrir_formulario(self, id_passeio=None):
        """Abre a janela modal para criar ou editar um passeio."""
        janela = ctk.CTkToplevel(self)
        janela.title("Editar Passeio" if id_passeio else "Cadastrar Passeio")
        janela.geometry("500x600")
        janela.configure(fg_color="#192E33")
        janela.resizable(False, False)
        janela.grab_set()

        janela.update_idletasks()
        x = (janela.winfo_screenwidth() // 2) - (500 // 2)
        y = (janela.winfo_screenheight() // 2) - (600 // 2)
        janela.geometry(f"+{x}+{y}")

        ctk.CTkLabel(
            janela, 
            text="✏️ Editar Passeio" if id_passeio else "🗺️ Cadastrar Passeio", 
            font=ctk.CTkFont(size=20, weight="bold"), 
            text_color="white"
        ).pack(pady=(24, 20))

        form_frame = ctk.CTkScrollableFrame(janela, fg_color="transparent", width=450, height=420)
        form_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        campos = {}

        def criar_campo(chave, label, placeholder=""):
            ctk.CTkLabel(form_frame, text=label, text_color="white", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 2))
            entry = ctk.CTkEntry(form_frame, placeholder_text=placeholder, height=36, fg_color="#2A4A52", border_color="#3D7BA3", text_color="white")
            entry.pack(fill="x")
            campos[chave] = entry

        criar_campo("destino", "Nome do Destino (Bate e Volta) *", "Ex: Praia de Pipa, Festa do Bode Rei")
        criar_campo("local_destino", "Local do Destino *", "Ex: Pipa-RN, Cabaceiras-PB")

        ctk.CTkLabel(form_frame, text="Locais de Embarque (Selecione 1 ou mais)", text_color="white", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 2))
        frame_locais = ctk.CTkFrame(form_frame, fg_color="#2A4A52", border_color="#3D7BA3", border_width=1)
        frame_locais.pack(fill="x")
        
        opcoes_locais = ["Mamanguape", "Capim", "Olho D'água", "Cuité de MME", "Sapé", "João Pessoa", "Rio Tinto", "Itapororoca"]
        vars_locais = {}
        for idx, loc in enumerate(opcoes_locais):
            var = ctk.StringVar(value="")
            cb = ctk.CTkCheckBox(frame_locais, text=loc, variable=var, onvalue=loc, offvalue="", text_color="white", fg_color="#FF9940", hover_color="#E07820")
            cb.grid(row=idx//2, column=idx%2, padx=10, pady=5, sticky="w")
            vars_locais[loc] = var

        criar_campo("data", "Data do Passeio *", "DD/MM/AAAA")
        
        def format_data_passeio(event, widget=campos["data"]):
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
        campos["data"].bind("<KeyRelease>", format_data_passeio)

        frame_horas = ctk.CTkFrame(form_frame, fg_color="transparent")
        frame_horas.pack(fill="x", pady=(10, 0))
        frame_horas.grid_columnconfigure((0, 1), weight=1)

        def format_hora(event, widget):
            if event.keysym in ('BackSpace', 'Delete', 'Left', 'Right'): return
            text = widget.get().replace(":", "")
            if len(text) > 4: text = text[:4]
            res = ""
            for i, c in enumerate(text):
                if i == 2: res += ":"
                res += c
            if widget.get() != res:
                widget.delete(0, "end")
                widget.insert(0, res)

        ctk.CTkLabel(frame_horas, text="Hora Saída", text_color="white", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w")
        campos["hora_saida"] = ctk.CTkEntry(frame_horas, placeholder_text="00:00", height=36, fg_color="#2A4A52", border_color="#3D7BA3", text_color="white")
        campos["hora_saida"].grid(row=1, column=0, sticky="ew", padx=(0, 5))
        campos["hora_saida"].bind("<KeyRelease>", lambda e: format_hora(e, campos["hora_saida"]))

        ctk.CTkLabel(frame_horas, text="Hora Retorno", text_color="white", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, sticky="w")
        campos["hora_retorno"] = ctk.CTkEntry(frame_horas, placeholder_text="00:00", height=36, fg_color="#2A4A52", border_color="#3D7BA3", text_color="white")
        campos["hora_retorno"].grid(row=1, column=1, sticky="ew", padx=(5, 0))
        campos["hora_retorno"].bind("<KeyRelease>", lambda e: format_hora(e, campos["hora_retorno"]))

        criar_campo("valor", "Valor Base (R$)", "Ex: 150,00")
        
        def format_moeda(event, widget=campos["valor"]):
            text = "".join(filter(str.isdigit, widget.get()))
            if not text:
                res = ""
            else:
                valor_int = int(text)
                valor_str = str(valor_int).zfill(3)
                reais = valor_str[:-2]
                centavos = valor_str[-2:]
                
                reais_fmt = ""
                for i, d in enumerate(reversed(reais)):
                    if i > 0 and i % 3 == 0:
                        reais_fmt = "." + reais_fmt
                    reais_fmt = d + reais_fmt
                    
                res = f"R$ {reais_fmt},{centavos}"
                
            if widget.get() != res:
                widget.delete(0, "end")
                widget.insert(0, res)
                
        campos["valor"].bind("<KeyRelease>", format_moeda)

        ctk.CTkLabel(form_frame, text="Capacidade do Ônibus", text_color="white", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 2))
        campos["capacidade"] = ctk.CTkOptionMenu(form_frame, values=["30", "50"], fg_color="#3D7BA3", button_color="#2A5A7A", height=36)
        campos["capacidade"].pack(fill="x")

        ctk.CTkLabel(form_frame, text="Status do Passeio", text_color="white", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 2))
        campos["status"] = ctk.CTkOptionMenu(form_frame, values=["A realizar", "Finalizado", "Cancelado"], fg_color="#3D7BA3", button_color="#2A5A7A", height=36)
        campos["status"].pack(fill="x")

        if id_passeio:
            conn = self._conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT destino, locais_embarque, local_destino, data_passeio, hora_saida, hora_retorno, valor_passeio, capacidade, status FROM passeios WHERE id=?", (id_passeio,))
            dados = cursor.fetchone()
            conn.close()

            if dados:
                campos["destino"].insert(0, dados[0] or "")
                if dados[1]:
                    selected_locais = [x.strip() for x in dados[1].split(",")]
                    for loc in opcoes_locais:
                        if loc in selected_locais:
                            vars_locais[loc].set(loc)
                            
                campos["local_destino"].insert(0, dados[2] or "")
                campos["data"].insert(0, dados[3] or "")
                campos["hora_saida"].insert(0, dados[4] or "")
                campos["hora_retorno"].insert(0, dados[5] or "")
                campos["valor"].insert(0, f"{dados[6]:.2f}".replace(".", ",") if dados[6] else "")
                campos["capacidade"].set(str(dados[7]) if dados[7] else "50")
                campos["status"].set(dados[8] or "A realizar")

        def salvar():
            destino = campos["destino"].get().strip()
            locais_selecionados = [loc for loc in opcoes_locais if vars_locais[loc].get() == loc]
            locais_str = ", ".join(locais_selecionados)
            
            local_destino = campos["local_destino"].get().strip()
            data = campos["data"].get().strip()
            h_saida = campos["hora_saida"].get().strip()
            h_retorno = campos["hora_retorno"].get().strip()
            valor_str = campos["valor"].get().strip()
            capacidade = int(campos["capacidade"].get())
            status = campos["status"].get()

            if not destino or not data:
                messagebox.showwarning("Aviso", "Destino e Data são obrigatórios.", parent=janela)
                return

            try:
                v_str = valor_str.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
                valor = float(v_str) if v_str else 0.0
            except ValueError:
                messagebox.showwarning("Aviso", "Valor Base inválido.", parent=janela)
                return

            conn = self._conectar()
            cursor = conn.cursor()

            try:
                if id_passeio:
                    cursor.execute("""
                        UPDATE passeios 
                        SET destino=?, locais_embarque=?, local_destino=?, data_passeio=?, hora_saida=?, hora_retorno=?, capacidade=?, valor_passeio=?, status=?
                        WHERE id=?
                    """, (destino, locais_str, local_destino, data, h_saida, h_retorno, capacidade, valor, status, id_passeio))
                    msg = "Passeio atualizado com sucesso!"
                else:
                    cursor.execute("""
                        INSERT INTO passeios (destino, locais_embarque, local_destino, data_passeio, hora_saida, hora_retorno, capacidade, valor_passeio, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (destino, locais_str, local_destino, data, h_saida, h_retorno, capacidade, valor, status))
                    msg = "Passeio cadastrado com sucesso!"
                
                conn.commit()
                messagebox.showinfo("Sucesso", msg, parent=janela)
                self.carregar_passeios()
                janela.destroy()
            except Exception as e:
                messagebox.showerror("Erro", f"Ocorreu um erro ao salvar:\n{e}", parent=janela)
            finally:
                conn.close()

        frame_btn = ctk.CTkFrame(janela, fg_color="transparent")
        frame_btn.pack(fill="x", padx=20, pady=16)

        ctk.CTkButton(
            frame_btn, text="💾 Salvar Passeio", fg_color="#FF9940", hover_color="#E07820", 
            text_color="white", font=ctk.CTkFont(weight="bold", size=14), height=44, command=salvar
        ).pack(fill="x")

    # =======================================================================
    # Exclusão
    # =======================================================================

    def excluir_passeio(self, id_passeio, destino):
        if messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir o passeio para '{destino}'?\n\nTodas as poltronas vendidas para este passeio também serão apagadas (efeito cascata)."):
            conn = self._conectar()
            try:
                conn.execute("DELETE FROM passeios WHERE id=?", (id_passeio,))
                conn.commit()
                messagebox.showinfo("Sucesso", "Passeio excluído!")
                self.carregar_passeios()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao excluir:\n{e}")
            finally:
                conn.close()
