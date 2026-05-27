"""
Módulo Fase 5 - Mapa do Ônibus e Alocação
-----------------------------------------
Implementa a janela do grid visual de poltronas e o popup de alocação de passageiros.
"""

import sqlite3
import os
import math
import customtkinter as ctk
from tkinter import ttk, messagebox
import sys

# Ajustar o sys.path se gerador_pdf estiver na raiz, pois mapa_onibus.py está em pages/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from gerador_pdf import gerar_relatorio_embarque
DB_PATH = os.path.join(BASE_DIR, "sistema_viagens.db")

class AlocarPoltronaWindow(ctk.CTkToplevel):
    def __init__(self, master, id_passeio, num_poltrona, locais_embarque, dados_alocacao=None, on_close_callback=None):
        super().__init__(master)
        self.title(f"Poltrona {num_poltrona:02d}")
        self.geometry("450x580")
        self.configure(fg_color="#192E33")
        self.resizable(False, False)
        
        self.id_passeio = id_passeio
        self.num_poltrona = num_poltrona
        self.locais_embarque = locais_embarque
        self.dados_alocacao = dados_alocacao # Tuple from DB if occupied, else None
        self.on_close_callback = on_close_callback
        
        # Faz com que a janela fique no topo
        self.transient(master)
        self.grab_set()

        # Centraliza
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.winfo_screenheight() // 2) - (580 // 2)
        self.geometry(f"+{x}+{y}")

        self._construir_interface()

    def _conectar(self):
        return sqlite3.connect(DB_PATH)

    def _construir_interface(self):
        ctk.CTkLabel(
            self, text=f"🚌 Poltrona {self.num_poltrona:02d}", 
            font=ctk.CTkFont(size=20, weight="bold"), text_color="white"
        ).pack(pady=(20, 15))

        self.form_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.form_frame.pack(fill="both", expand=True, padx=20)

        self.campos = {}

        if self.dados_alocacao:
            # OCUPADA: Mostrar dados e opções de edição/exclusão
            (id_alocacao, pass_id, nome, c_nome, local, tipo_desc, val_desc, crianca_id_raw) = self.dados_alocacao
            
            ctk.CTkLabel(self.form_frame, text="Passageiro Alocado:", text_color="#3D7BA3", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
            ctk.CTkLabel(self.form_frame, text=nome, text_color="white", font=ctk.CTkFont(size=16)).pack(anchor="w", pady=(0, 15))

            ctk.CTkLabel(self.form_frame, text="Criança de Colo:", text_color="white").pack(anchor="w")
            self.campos["crianca"] = ctk.CTkEntry(self.form_frame, fg_color="#2A4A52", border_color="#3D7BA3", text_color="white")
            self.campos["crianca"].pack(fill="x", pady=(0, 10))
            if c_nome:
                self.campos["crianca"].insert(0, c_nome)
            else:
                self.campos["crianca"].insert(0, "Nenhuma")
            self.campos["crianca"].configure(state="disabled")

            ctk.CTkLabel(self.form_frame, text="Local de Embarque:", text_color="white").pack(anchor="w")
            self.campos["local"] = ctk.CTkOptionMenu(self.form_frame, values=self.locais_embarque, fg_color="#3D7BA3", button_color="#2A5A7A")
            self.campos["local"].pack(fill="x", pady=(0, 10))
            if local and local in self.locais_embarque: self.campos["local"].set(local)

            # Descontos
            frame_desc = ctk.CTkFrame(self.form_frame, fg_color="transparent")
            frame_desc.pack(fill="x", pady=(10, 0))
            frame_desc.grid_columnconfigure(1, weight=1)
            
            self.campos["tipo_desc"] = ctk.CTkOptionMenu(frame_desc, values=["Nenhum", "R$", "%"], width=90, fg_color="#3D7BA3", button_color="#2A5A7A")
            self.campos["tipo_desc"].grid(row=0, column=0, padx=(0, 10))
            
            self.campos["val_desc"] = ctk.CTkEntry(frame_desc, placeholder_text="0", fg_color="#2A4A52", border_color="#3D7BA3", text_color="white")
            self.campos["val_desc"].grid(row=0, column=1, sticky="ew")

            if tipo_desc:
                self.campos["tipo_desc"].set(tipo_desc if tipo_desc in ["R$", "%"] else ("R$" if tipo_desc=="valor" else "%"))
                self.campos["val_desc"].insert(0, str(val_desc))
            else:
                self.campos["tipo_desc"].set("Nenhum")

            # Botões
            frame_btns = ctk.CTkFrame(self, fg_color="transparent")
            frame_btns.pack(fill="x", padx=20, pady=20)
            
            ctk.CTkButton(
                frame_btns, text="Desalocar", fg_color="#C0392B", hover_color="#962A20",
                command=lambda: self.desalocar(id_alocacao)
            ).pack(side="left", expand=True, fill="x", padx=(0, 5))

            ctk.CTkButton(
                frame_btns, text="Salvar", fg_color="#FF9940", hover_color="#E07820",
                command=lambda: self.salvar(id_alocacao, pass_id)
            ).pack(side="right", expand=True, fill="x", padx=(5, 0))

        else:
            # LIVRE: Mostrar busca de passageiros e form de alocação
            ctk.CTkLabel(self.form_frame, text="Buscar Passageiro (Nome ou CPF):", text_color="white", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
            
            frame_busca = ctk.CTkFrame(self.form_frame, fg_color="transparent")
            frame_busca.pack(fill="x", pady=(0, 10))
            
            self.entry_busca = ctk.CTkEntry(frame_busca, fg_color="white", text_color="black", placeholder_text="Digite para buscar...")
            self.entry_busca.pack(side="left", fill="x", expand=True, padx=(0, 5))
            
            ctk.CTkButton(frame_busca, text="Buscar", width=80, fg_color="#3D7BA3", command=self.buscar_passageiro).pack(side="right")

            ctk.CTkLabel(self.form_frame, text="Selecione o Passageiro:", text_color="white").pack(anchor="w")
            self.combo_pass = ctk.CTkOptionMenu(self.form_frame, values=["Faça uma busca primeiro"], fg_color="#2A4A52", button_color="#3D7BA3")
            self.combo_pass.pack(fill="x", pady=(0, 15))
            self.passageiros_encontrados = {} # dict mapping "Nome (CPF)" -> id

            ctk.CTkLabel(self.form_frame, text="Criança de Colo (Opcional):", text_color="white", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
            
            frame_busca_c = ctk.CTkFrame(self.form_frame, fg_color="transparent")
            frame_busca_c.pack(fill="x", pady=(0, 5))
            
            self.entry_busca_c = ctk.CTkEntry(frame_busca_c, fg_color="white", text_color="black", placeholder_text="Buscar criança...")
            self.entry_busca_c.pack(side="left", fill="x", expand=True, padx=(0, 5))
            
            ctk.CTkButton(frame_busca_c, text="Buscar", width=80, fg_color="#3D7BA3", command=self.buscar_crianca).pack(side="right")
            
            self.combo_crianca = ctk.CTkOptionMenu(self.form_frame, values=["Nenhuma"], fg_color="#2A4A52", button_color="#3D7BA3")
            self.combo_crianca.pack(fill="x", pady=(0, 10))
            self.combo_crianca.set("Nenhuma")
            self.criancas_encontradas = {}

            ctk.CTkLabel(self.form_frame, text="Local de Embarque:", text_color="white").pack(anchor="w")
            self.campos["local"] = ctk.CTkOptionMenu(self.form_frame, values=self.locais_embarque, fg_color="#3D7BA3", button_color="#2A5A7A")
            self.campos["local"].pack(fill="x", pady=(0, 10))

            # Descontos
            ctk.CTkLabel(self.form_frame, text="Desconto Especial:", text_color="white").pack(anchor="w")
            frame_desc = ctk.CTkFrame(self.form_frame, fg_color="transparent")
            frame_desc.pack(fill="x", pady=(0, 10))
            frame_desc.grid_columnconfigure(1, weight=1)
            
            self.campos["tipo_desc"] = ctk.CTkOptionMenu(frame_desc, values=["Nenhum", "R$", "%"], width=90, fg_color="#3D7BA3", button_color="#2A5A7A")
            self.campos["tipo_desc"].grid(row=0, column=0, padx=(0, 10))
            
            self.campos["val_desc"] = ctk.CTkEntry(frame_desc, placeholder_text="Valor numérico", fg_color="#2A4A52", border_color="#3D7BA3", text_color="white")
            self.campos["val_desc"].grid(row=0, column=1, sticky="ew")

            ctk.CTkButton(
                self, text="Confirmar Alocação", fg_color="#27AE60", hover_color="#219653",
                font=ctk.CTkFont(weight="bold", size=14), height=45,
                command=lambda: self.salvar(None, None)
            ).pack(fill="x", padx=20, pady=20)

    def buscar_passageiro(self):
        termo = self.entry_busca.get().strip()
        if not termo: return
        
        conn = self._conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome_completo, cpf FROM passageiros WHERE nome_completo LIKE ? OR cpf LIKE ? LIMIT 20", (f"%{termo}%", f"%{termo}%"))
        resultados = cursor.fetchall()
        conn.close()

        self.passageiros_encontrados.clear()
        if not resultados:
            self.combo_pass.configure(values=["Nenhum encontrado"])
            self.combo_pass.set("Nenhum encontrado")
        else:
            valores = []
            for r in resultados:
                linha = f"{r[1]} ({r[2] or 'Sem CPF'})"
                self.passageiros_encontrados[linha] = r[0]
                valores.append(linha)
            self.combo_pass.configure(values=valores)
            self.combo_pass.set(valores[0])

    def buscar_crianca(self):
        termo = self.entry_busca_c.get().strip()
        if not termo: return
        
        conn = self._conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome_completo, cpf FROM passageiros WHERE nome_completo LIKE ? OR cpf LIKE ? LIMIT 20", (f"%{termo}%", f"%{termo}%"))
        resultados = cursor.fetchall()
        conn.close()

        self.criancas_encontradas.clear()
        if not resultados:
            self.combo_crianca.configure(values=["Nenhuma", "Nenhum encontrado"])
            self.combo_crianca.set("Nenhuma")
        else:
            valores = ["Nenhuma"]
            for r in resultados:
                linha = f"{r[1]} ({r[2] or 'Sem CPF'})"
                self.criancas_encontradas[linha] = r[0]
                valores.append(linha)
            self.combo_crianca.configure(values=valores)
            self.combo_crianca.set(valores[1])

    def desalocar(self, id_alocacao):
        if messagebox.askyesno("Confirmar", "Tem certeza que deseja desalocar esta poltrona?", parent=self):
            conn = self._conectar()
            try:
                conn.execute("DELETE FROM alocacao_poltronas WHERE id=?", (id_alocacao,))
                conn.commit()
                if self.on_close_callback: self.on_close_callback()
                self.destroy()
            except Exception as e:
                messagebox.showerror("Erro", str(e), parent=self)
            finally:
                conn.close()

    def salvar(self, id_alocacao, pass_id):
        # Validação do Passageiro (se novo insert)
        if not id_alocacao:
            sel = self.combo_pass.get()
            if sel not in self.passageiros_encontrados:
                messagebox.showwarning("Aviso", "Selecione um passageiro válido da busca.", parent=self)
                return
            pass_id = self.passageiros_encontrados[sel]

        crianca_id = None
        if not id_alocacao:
            sel_c = self.combo_crianca.get()
            if sel_c in self.criancas_encontradas:
                crianca_id = str(self.criancas_encontradas[sel_c])
        else:
            crianca_id = self.dados_alocacao[7]

        local = self.campos["local"].get()
        tipo_desc = self.campos["tipo_desc"].get()
        val_desc_str = self.campos["val_desc"].get().replace(",", ".")
        
        db_tipo = "valor" if tipo_desc == "R$" else ("porcentagem" if tipo_desc == "%" else None)
        db_val = 0.0
        if db_tipo:
            try:
                db_val = float(val_desc_str)
            except ValueError:
                messagebox.showwarning("Aviso", "Valor de desconto inválido.", parent=self)
                return

        conn = self._conectar()
        cursor = conn.cursor()
        
        try:
            if id_alocacao:
                cursor.execute("""
                    UPDATE alocacao_poltronas 
                    SET crianca_colo=?, local_embarque=?, tipo_desconto=?, valor_desconto=?
                    WHERE id=?
                """, (crianca_id, local, db_tipo, db_val, id_alocacao))
            else:
                cursor.execute("""
                    INSERT INTO alocacao_poltronas (passeio_id, passageiro_id, numero_poltrona, crianca_colo, local_embarque, tipo_desconto, valor_desconto)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (self.id_passeio, pass_id, self.num_poltrona, crianca_id, local, db_tipo, db_val))
            
            conn.commit()
            if self.on_close_callback: self.on_close_callback()
            self.destroy()
        except sqlite3.IntegrityError:
            messagebox.showerror("Aviso", "Este passageiro já está alocado em outra poltrona neste passeio!", parent=self)
        except Exception as e:
            messagebox.showerror("Erro", str(e), parent=self)
        finally:
            conn.close()


class MapaOnibusWindow(ctk.CTkToplevel):
    def __init__(self, master, id_passeio):
        super().__init__(master)
        self.id_passeio = id_passeio
        self.title("Mapa do Ônibus - Alocação de Poltronas")
        self.geometry("1100x700")
        self.configure(fg_color="#E4F7FE")  # Fundo Azul Gelo
        self.transient(master)
        
        # Centraliza a janela
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (1100 // 2)
        y = (self.winfo_screenheight() // 2) - (700 // 2)
        self.geometry(f"+{x}+{y}")
        
        # Cores
        self.cor_livre = "#27AE60"    # Verde
        self.cor_ocupado = "#7F8C8D"  # Cinza
        self.cor_header = "#192E33"   # Azul Escuro
        
        # Carregar dados iniciais
        self._carregar_dados_passeio()
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=2) # Ônibus
        self.grid_columnconfigure(1, weight=3) # Lista
        
        self._construir_onibus()
        self._construir_painel()
        
        self.carregar_alocacoes()

    def _conectar(self):
        return sqlite3.connect(DB_PATH)

    def _carregar_dados_passeio(self):
        conn = self._conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT destino, capacidade, locais_embarque, data_passeio FROM passeios WHERE id=?", (self.id_passeio,))
        dados = cursor.fetchone()
        conn.close()
        
        if dados:
            self.destino = dados[0]
            self.capacidade = dados[1] if dados[1] else 50
            locais_raw = dados[2]
            self.locais_embarque = [x.strip() for x in locais_raw.split(",")] if locais_raw else ["Padrão"]
            self.data_passeio = dados[3]
        else:
            self.capacidade = 50
            self.locais_embarque = ["Padrão"]
            self.destino = "Desconhecido"
            self.data_passeio = ""

    def _construir_onibus(self):
        frame_esq = ctk.CTkFrame(self, fg_color="white", corner_radius=15)
        frame_esq.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        ctk.CTkLabel(frame_esq, text="Frente do Ônibus", font=ctk.CTkFont(weight="bold", size=18), text_color=self.cor_header).pack(pady=(20,10))
        
        # Area rolável do ônibus
        self.scroll_onibus = ctk.CTkScrollableFrame(frame_esq, fg_color="transparent")
        self.scroll_onibus.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Dicionário para armazenar referência aos botões
        self.botoes_poltronas = {}
        
        linhas = math.ceil(self.capacidade / 4)
        
        # Criação do Grid
        # 0: Janela Esq, 1: Corredor Esq, 2: Espaço, 3: Corredor Dir, 4: Janela Dir
        for i in range(5):
            self.scroll_onibus.grid_columnconfigure(i, weight=1)
            
        for row in range(linhas):
            for col_logical in range(4):
                # Numeração clássica: 
                # Coluna 0 (Janela Esq): row*4 + 1
                # Coluna 1 (Corredor Esq): row*4 + 2
                # Coluna 2 (Corredor Dir): row*4 + 4
                # Coluna 3 (Janela Dir): row*4 + 3
                if col_logical == 0:
                    num = row * 4 + 1
                    col_visual = 0
                elif col_logical == 1:
                    num = row * 4 + 2
                    col_visual = 1
                elif col_logical == 2:
                    num = row * 4 + 4
                    col_visual = 3
                elif col_logical == 3:
                    num = row * 4 + 3
                    col_visual = 4
                    
                if num <= self.capacidade:
                    btn = ctk.CTkButton(
                        self.scroll_onibus,
                        text=f"{num:02d}",
                        width=50, height=50,
                        font=ctk.CTkFont(weight="bold", size=16),
                        fg_color=self.cor_livre,
                        hover_color="#3D7BA3",
                        corner_radius=8,
                        command=lambda n=num: self.clicar_poltrona(n)
                    )
                    btn.grid(row=row, column=col_visual, padx=5, pady=5)
                    self.botoes_poltronas[num] = btn
                    
            # Adiciona o corredor visual vazio
            ctk.CTkFrame(self.scroll_onibus, width=30, height=50, fg_color="transparent").grid(row=row, column=2)

    def _construir_painel(self):
        frame_dir = ctk.CTkFrame(self, fg_color="white", corner_radius=15)
        frame_dir.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=20)
        
        # Cabeçalho do Painel
        frame_head = ctk.CTkFrame(frame_dir, fg_color="transparent")
        frame_head.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(frame_head, text=f"📍 {self.destino}", font=ctk.CTkFont(size=22, weight="bold"), text_color=self.cor_header).pack(anchor="w")
        ctk.CTkLabel(frame_head, text=f"Data: {self.data_passeio}", font=ctk.CTkFont(size=14), text_color="#3D7BA3").pack(anchor="w")
        
        self.lbl_stats = ctk.CTkLabel(frame_head, text="Ocupação: 0/50", font=ctk.CTkFont(size=16, weight="bold"), text_color="#FF9940")
        self.lbl_stats.pack(anchor="e", side="right")

        # Tabela de Alocados
        frame_tabela = ctk.CTkFrame(frame_dir, fg_color="transparent")
        frame_tabela.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#3D7BA3", foreground="white")
        style.configure("Treeview", rowheight=25)
        
        colunas = ("Pol", "Passageiro", "Embarque", "WhatsApp")
        self.tree = ttk.Treeview(frame_tabela, columns=colunas, show="headings", style="Treeview")
        
        self.tree.heading("Pol", text="Pol")
        self.tree.column("Pol", width=40, anchor="center")
        self.tree.heading("Passageiro", text="Passageiro")
        self.tree.column("Passageiro", width=180)
        self.tree.heading("Embarque", text="Local de Embarque")
        self.tree.column("Embarque", width=120)
        self.tree.heading("WhatsApp", text="WhatsApp")
        self.tree.column("WhatsApp", width=100)
        
        self.tree.pack(fill="both", expand=True, side="left")
        
        scrollbar = ttk.Scrollbar(frame_tabela, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        # Função de wrapper com try-except para o PDF
        def on_gerar_pdf(tipo):
            try:
                gerar_relatorio_embarque(self.id_passeio, tipo=tipo)
                messagebox.showinfo("Sucesso", f"Relatório PDF ({tipo}) gerado com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", f"Ocorreu um erro ao gerar o PDF:\n{e}")

        # Frame de Botões
        frame_botoes = ctk.CTkFrame(frame_dir, fg_color="transparent")
        frame_botoes.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkButton(
            frame_botoes, text="📄 Relatório Completo (PDF)", 
            fg_color="#192E33", hover_color="#0F1C1F", height=45,
            font=ctk.CTkFont(weight="bold"),
            command=lambda: on_gerar_pdf("completo")
        ).pack(side="left", expand=True, fill="x", padx=(0, 5))

        ctk.CTkButton(
            frame_botoes, text="📋 Relatório Resumido", 
            fg_color="#3D7BA3", hover_color="#2A5A7A", height=45,
            font=ctk.CTkFont(weight="bold"),
            command=lambda: on_gerar_pdf("resumido")
        ).pack(side="right", expand=True, fill="x", padx=(5, 0))

    def carregar_alocacoes(self):
        # Reset grid colors
        for btn in self.botoes_poltronas.values():
            btn.configure(fg_color=self.cor_livre)
            
        # Reset Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        conn = self._conectar()
        cursor = conn.cursor()
        
        query = """
            SELECT a.id, a.numero_poltrona, p.nome_completo, p.whatsapp, a.local_embarque, a.passageiro_id, a.crianca_colo, a.tipo_desconto, a.valor_desconto, pc.nome_completo as crianca_nome, pc.whatsapp as crianca_whats
            FROM alocacao_poltronas a
            JOIN passageiros p ON a.passageiro_id = p.id
            LEFT JOIN passageiros pc ON a.crianca_colo = CAST(pc.id AS TEXT)
            WHERE a.passeio_id = ?
            ORDER BY a.numero_poltrona ASC
        """
        cursor.execute(query, (self.id_passeio,))
        alocacoes = cursor.fetchall()
        conn.close()
        
        self.dados_banco = {} # num_poltrona -> tuple of all data
        
        for row in alocacoes:
            id_aloc, num_pol, nome, whats, local, pass_id, crianca_id_raw, t_desc, v_desc, c_nome, c_whats = row
            
            # Atualiza Grid
            if num_pol in self.botoes_poltronas:
                self.botoes_poltronas[num_pol].configure(fg_color=self.cor_ocupado)
                
            # Atualiza Tabela (Adulto)
            self.tree.insert("", "end", values=(f"{num_pol:02d}", nome, local or "—", whats or "—"))
            
            # Atualiza Tabela (Criança de Colo) se existir
            if c_nome:
                self.tree.insert("", "end", values=(f"{num_pol:02d}", f"{c_nome} (Colo)", local or "—", c_whats or "—"))
            
            # Salva para uso no click
            self.dados_banco[num_pol] = (id_aloc, pass_id, nome, c_nome, local, t_desc, v_desc, crianca_id_raw)
            
        # Atualiza stats
        ocupadas = len(alocacoes)
        self.lbl_stats.configure(text=f"Ocupação: {ocupadas}/{self.capacidade}")

    def clicar_poltrona(self, num_poltrona):
        dados = self.dados_banco.get(num_poltrona)
        AlocarPoltronaWindow(
            master=self,
            id_passeio=self.id_passeio,
            num_poltrona=num_poltrona,
            locais_embarque=self.locais_embarque,
            dados_alocacao=dados,
            on_close_callback=self.carregar_alocacoes
        )
