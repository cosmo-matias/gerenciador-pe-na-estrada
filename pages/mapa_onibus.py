"""
Módulo Fase 5 - Mapa do Ônibus e Alocação
-----------------------------------------
Implementa a janela do grid visual de poltronas, popup de alocação, e aba Financeira.
"""

import sqlite3
import os
import math
import datetime
import customtkinter as ctk
from tkinter import ttk, messagebox
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from gerador_pdf import gerar_relatorio_embarque, gerar_recibo_pagamento
DB_PATH = os.path.join(BASE_DIR, "sistema_viagens.db")

class LancarPagamentoWindow(ctk.CTkToplevel):
    def __init__(self, master, alocacao_id, nome, poltrona, saldo_devedor, on_success):
        super().__init__(master)
        self.title("Lançar Pagamento")
        self.geometry("400x380")
        self.configure(fg_color="#192E33")
        self.resizable(False, False)
        
        self.alocacao_id = alocacao_id
        self.saldo_devedor = saldo_devedor
        self.on_success = on_success
        
        self.transient(master)
        self.grab_set()

        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.winfo_screenheight() // 2) - (380 // 2)
        self.geometry(f"+{x}+{y}")

        ctk.CTkLabel(self, text="💰 Lançar Pagamento", font=ctk.CTkFont(size=20, weight="bold"), text_color="white").pack(pady=(20, 10))
        
        ctk.CTkLabel(self, text=f"Passageiro: {nome}", font=ctk.CTkFont(size=14), text_color="#BDDDE8").pack()
        ctk.CTkLabel(self, text=f"Poltrona: {poltrona:02d}", font=ctk.CTkFont(size=14), text_color="#BDDDE8").pack(pady=(0, 20))

        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        form_frame.pack(fill="x", padx=30)

        ctk.CTkLabel(form_frame, text="Valor do Pagamento (R$):", text_color="white", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        self.entry_valor = ctk.CTkEntry(form_frame, placeholder_text="0,00", fg_color="#2A4A52", border_color="#3D7BA3", text_color="white")
        self.entry_valor.pack(fill="x", pady=(5, 15))
        self.entry_valor.insert(0, f"{max(0, saldo_devedor):.2f}".replace(".", ","))

        ctk.CTkLabel(form_frame, text="Método de Pagamento:", text_color="white", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        self.combo_metodo = ctk.CTkOptionMenu(form_frame, values=["PIX", "Dinheiro", "Cartão"], fg_color="#3D7BA3", button_color="#2A5A7A")
        self.combo_metodo.pack(fill="x", pady=(5, 25))

        ctk.CTkButton(self, text="Confirmar Recebimento", fg_color="#27AE60", hover_color="#219653", height=40, font=ctk.CTkFont(weight="bold"), command=self.salvar_pagamento).pack(fill="x", padx=30)

    def _conectar(self):
        return sqlite3.connect(DB_PATH)

    def salvar_pagamento(self):
        val_str = self.entry_valor.get().replace("R$", "").replace(".", "").replace(",", ".").strip()
        try:
            valor_pago = float(val_desc) if 'val_desc' in locals() else float(val_str)
        except ValueError:
            messagebox.showwarning("Aviso", "Valor inválido.", parent=self)
            return

        if valor_pago <= 0:
            messagebox.showwarning("Aviso", "O valor pago deve ser maior que zero.", parent=self)
            return

        metodo = self.combo_metodo.get()
        data_hora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = self._conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO pagamentos (alocacao_id, valor_pago, data_hora_pagamento, metodo_pagamento)
                VALUES (?, ?, ?, ?)
            """, (self.alocacao_id, valor_pago, data_hora, metodo))
            
            id_pagamento = cursor.lastrowid
            conn.commit()
            
            try:
                gerar_recibo_pagamento(id_pagamento)
            except Exception as e:
                messagebox.showerror("Erro", f"Pagamento salvo, mas erro ao gerar recibo: {e}", parent=self)
                
            messagebox.showinfo("Sucesso", "Pagamento registrado com sucesso!", parent=self)
            self.on_success()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Erro", str(e), parent=self)
        finally:
            conn.close()

# ... (AlocarPoltronaWindow remains the same, I will paste it fully below)
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
        self.dados_alocacao = dados_alocacao 
        self.on_close_callback = on_close_callback
        
        self.transient(master)
        self.grab_set()

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
            ctk.CTkLabel(self.form_frame, text="Buscar Passageiro (Nome ou CPF):", text_color="white", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
            
            frame_busca = ctk.CTkFrame(self.form_frame, fg_color="transparent")
            frame_busca.pack(fill="x", pady=(0, 10))
            
            self.entry_busca = ctk.CTkEntry(frame_busca, fg_color="white", text_color="black", placeholder_text="Digite para buscar...")
            self.entry_busca.pack(side="left", fill="x", expand=True, padx=(0, 5))
            
            ctk.CTkButton(frame_busca, text="Buscar", width=80, fg_color="#3D7BA3", command=self.buscar_passageiro).pack(side="right")

            ctk.CTkLabel(self.form_frame, text="Selecione o Passageiro:", text_color="white").pack(anchor="w")
            self.combo_pass = ctk.CTkOptionMenu(self.form_frame, values=["Faça uma busca primeiro"], fg_color="#2A4A52", button_color="#3D7BA3")
            self.combo_pass.pack(fill="x", pady=(0, 15))
            self.passageiros_encontrados = {}

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
        self.title("Gerenciamento do Passeio")
        self.geometry("1200x800")
        self.configure(fg_color="#E4F7FE")  # Fundo Azul Gelo
        self.transient(master)
        self.resizable(True, True)
        
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (1200 // 2)
        y = (self.winfo_screenheight() // 2) - (800 // 2)
        self.geometry(f"+{x}+{y}")
        self.after(200, lambda: self.state('zoomed'))
        
        self.cor_livre = "#27AE60"    # Verde
        self.cor_ocupado = "#7F8C8D"  # Cinza
        self.cor_header = "#192E33"   # Azul Escuro
        
        self._carregar_dados_passeio()
        
        # Cabeçalho Geral
        frame_head = ctk.CTkFrame(self, fg_color="transparent")
        frame_head.pack(fill="x", padx=20, pady=(20, 0))
        ctk.CTkLabel(frame_head, text=f"📍 {self.destino}", font=ctk.CTkFont(size=24, weight="bold"), text_color=self.cor_header).pack(anchor="w")
        ctk.CTkLabel(frame_head, text=f"Data: {self.data_passeio}", font=ctk.CTkFont(size=14), text_color="#3D7BA3").pack(anchor="w")

        # Tabview
        self.tabview = ctk.CTkTabview(self, fg_color="white", segmented_button_selected_color="#3D7BA3", segmented_button_selected_hover_color="#2A5A7A", text_color="black")
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.aba_alocacao = self.tabview.add("Alocação de Poltronas")
        self.aba_financeiro = self.tabview.add("Financeiro")
        
        self.aba_alocacao.grid_rowconfigure(0, weight=1)
        self.aba_alocacao.grid_columnconfigure(0, weight=2)
        self.aba_alocacao.grid_columnconfigure(1, weight=3)
        
        self._construir_onibus(self.aba_alocacao)
        self._construir_painel_alocacao(self.aba_alocacao)
        self._construir_painel_financeiro(self.aba_financeiro)
        
        self.carregar_tudo()

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

    def carregar_tudo(self):
        self.carregar_alocacoes()
        self.carregar_financeiro()

    # =========================================================================================
    # ABA 1: ALOCAÇÃO DE POLTRONAS
    # =========================================================================================
    def _construir_onibus(self, parent):
        frame_esq = ctk.CTkFrame(parent, fg_color="#F8F9FA", corner_radius=15)
        frame_esq.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkLabel(frame_esq, text="Frente do Ônibus", font=ctk.CTkFont(weight="bold", size=18), text_color=self.cor_header).pack(pady=(20,10))
        
        self.scroll_onibus = ctk.CTkScrollableFrame(frame_esq, fg_color="transparent")
        self.scroll_onibus.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.botoes_poltronas = {}
        linhas = math.ceil(self.capacidade / 4)
        
        for i in range(5):
            self.scroll_onibus.grid_columnconfigure(i, weight=1)
            
        for row in range(linhas):
            for col_logical in range(4):
                if col_logical == 0: num, col_visual = row * 4 + 1, 0
                elif col_logical == 1: num, col_visual = row * 4 + 2, 1
                elif col_logical == 2: num, col_visual = row * 4 + 4, 3
                elif col_logical == 3: num, col_visual = row * 4 + 3, 4
                    
                if num <= self.capacidade:
                    btn = ctk.CTkButton(
                        self.scroll_onibus, text=f"{num:02d}", width=50, height=50,
                        font=ctk.CTkFont(weight="bold", size=16), fg_color=self.cor_livre, hover_color="#3D7BA3", corner_radius=8,
                        command=lambda n=num: self.clicar_poltrona(n)
                    )
                    btn.grid(row=row, column=col_visual, padx=5, pady=5)
                    self.botoes_poltronas[num] = btn
            ctk.CTkFrame(self.scroll_onibus, width=30, height=50, fg_color="transparent").grid(row=row, column=2)

    def _construir_painel_alocacao(self, parent):
        frame_dir = ctk.CTkFrame(parent, fg_color="#F8F9FA", corner_radius=15)
        frame_dir.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=10)
        
        self.lbl_stats = ctk.CTkLabel(frame_dir, text="Ocupação: 0/50", font=ctk.CTkFont(size=16, weight="bold"), text_color="#FF9940")
        self.lbl_stats.pack(anchor="e", padx=20, pady=(20, 5))

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
        
        def on_gerar_pdf(tipo):
            try:
                gerar_relatorio_embarque(self.id_passeio, tipo=tipo)
                messagebox.showinfo("Sucesso", f"Relatório PDF ({tipo}) gerado com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", f"Ocorreu um erro ao gerar o PDF:\n{e}")

        frame_botoes = ctk.CTkFrame(frame_dir, fg_color="transparent")
        frame_botoes.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkButton(
            frame_botoes, text="📄 Completo (PDF)", fg_color="#192E33", hover_color="#0F1C1F", height=45, font=ctk.CTkFont(weight="bold"), command=lambda: on_gerar_pdf("completo")
        ).pack(side="left", expand=True, fill="x", padx=(0, 5))

        ctk.CTkButton(
            frame_botoes, text="📋 Resumido", fg_color="#3D7BA3", hover_color="#2A5A7A", height=45, font=ctk.CTkFont(weight="bold"), command=lambda: on_gerar_pdf("resumido")
        ).pack(side="right", expand=True, fill="x", padx=(5, 0))

    def carregar_alocacoes(self):
        for btn in self.botoes_poltronas.values(): btn.configure(fg_color=self.cor_livre)
        for item in self.tree.get_children(): self.tree.delete(item)
            
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
        
        self.dados_banco = {}
        for row in alocacoes:
            id_aloc, num_pol, nome, whats, local, pass_id, crianca_id_raw, t_desc, v_desc, c_nome, c_whats = row
            if num_pol in self.botoes_poltronas: self.botoes_poltronas[num_pol].configure(fg_color=self.cor_ocupado)
            self.tree.insert("", "end", values=(f"{num_pol:02d}", nome, local or "—", whats or "—"))
            if c_nome: self.tree.insert("", "end", values=(f"{num_pol:02d}", f"{c_nome} (Colo)", local or "—", c_whats or "—"))
            self.dados_banco[num_pol] = (id_aloc, pass_id, nome, c_nome, local, t_desc, v_desc, crianca_id_raw)
            
        self.lbl_stats.configure(text=f"Ocupação: {len(alocacoes)}/{self.capacidade}")

    def clicar_poltrona(self, num_poltrona):
        dados = self.dados_banco.get(num_poltrona)
        AlocarPoltronaWindow(self, self.id_passeio, num_poltrona, self.locais_embarque, dados, self.carregar_tudo)

    # =========================================================================================
    # ABA 2: FINANCEIRO
    # =========================================================================================
    def _construir_painel_financeiro(self, parent):
        # Painel de Custos
        frame_custos = ctk.CTkFrame(parent, fg_color="transparent")
        frame_custos.pack(fill="x", padx=10, pady=(10, 0))
        
        ctk.CTkLabel(frame_custos, text="Custo Ônibus (R$):", text_color="#192E33", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        self.entry_custo_onibus = ctk.CTkEntry(frame_custos, width=100)
        self.entry_custo_onibus.pack(side="left", padx=5)
        
        ctk.CTkLabel(frame_custos, text="Custos Adicionais (R$):", text_color="#192E33", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        self.entry_custos_adicionais = ctk.CTkEntry(frame_custos, width=100)
        self.entry_custos_adicionais.pack(side="left", padx=5)
        
        ctk.CTkButton(frame_custos, text="Salvar Custos", width=120, fg_color="#3D7BA3", hover_color="#2A5A7A", command=self.salvar_custos).pack(side="left", padx=10)
        
        ctk.CTkButton(frame_custos, text="📄 Gerar Balanço", width=130, fg_color="#192E33", hover_color="#0F1C1F", command=self.gerar_balanco).pack(side="right", padx=10)

        # Cards de Resumo
        self.frame_resumo_fin = ctk.CTkFrame(parent, fg_color="transparent")
        self.frame_resumo_fin.pack(fill="x", padx=10, pady=10)
        self.frame_resumo_fin.grid_columnconfigure((0, 1, 2), weight=1)

        card_esperada = ctk.CTkFrame(self.frame_resumo_fin, fg_color="#3D7BA3", corner_radius=10)
        card_esperada.grid(row=0, column=0, sticky="ew", padx=10)
        ctk.CTkLabel(card_esperada, text="Receita Esperada", font=ctk.CTkFont(size=14), text_color="#BDDDE8").pack(pady=(15, 0))
        self.lbl_receita_esperada = ctk.CTkLabel(card_esperada, text="R$ 0,00", font=ctk.CTkFont(size=24, weight="bold"), text_color="white")
        self.lbl_receita_esperada.pack(pady=(0, 15))

        card_custos = ctk.CTkFrame(self.frame_resumo_fin, fg_color="#C0392B", corner_radius=10)
        card_custos.grid(row=0, column=1, sticky="ew", padx=10)
        ctk.CTkLabel(card_custos, text="Custos Totais", font=ctk.CTkFont(size=14), text_color="#F5B7B1").pack(pady=(15, 0))
        self.lbl_custos_totais = ctk.CTkLabel(card_custos, text="R$ 0,00", font=ctk.CTkFont(size=24, weight="bold"), text_color="white")
        self.lbl_custos_totais.pack(pady=(0, 15))

        card_lucro = ctk.CTkFrame(self.frame_resumo_fin, fg_color="#27AE60", corner_radius=10)
        card_lucro.grid(row=0, column=2, sticky="ew", padx=10)
        ctk.CTkLabel(card_lucro, text="Lucro Previsto", font=ctk.CTkFont(size=14), text_color="#E4F7FE").pack(pady=(15, 0))
        self.lbl_lucro_projetado = ctk.CTkLabel(card_lucro, text="R$ 0,00", font=ctk.CTkFont(size=24, weight="bold"), text_color="white")
        self.lbl_lucro_projetado.pack(pady=(0, 15))
        
        # Ponto de Equilíbrio
        self.lbl_ponto_equilibrio = ctk.CTkLabel(parent, text="Ponto de Equilíbrio: Calculando...", text_color="#192E33", font=ctk.CTkFont(weight="bold", size=14))
        self.lbl_ponto_equilibrio.pack(fill="x", padx=20, pady=(0, 10))

        # Filtro
        frame_filtro = ctk.CTkFrame(parent, fg_color="transparent")
        frame_filtro.pack(fill="x", padx=20, pady=(5, 0))
        ctk.CTkLabel(frame_filtro, text="Filtrar por Status:", text_color="#192E33", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 10))
        self.combo_filtro_fin = ctk.CTkOptionMenu(
            frame_filtro, values=["Todos", "Pendentes", "Quitados"], 
            fg_color="#3D7BA3", button_color="#2A5A7A", command=lambda _: self.renderizar_lista_financeira()
        )
        self.combo_filtro_fin.pack(side="left")

        # Cabeçalho da Lista
        header_frame = ctk.CTkFrame(parent, fg_color="#192E33", corner_radius=8)
        header_frame.pack(fill="x", padx=20, pady=(15, 0))
        
        pesos = [1, 3, 1, 1, 1, 1]
        for i, peso in enumerate(pesos):
            header_frame.grid_columnconfigure(i, weight=peso)
        
        headers = [
            ("Pol", "center"), ("Passageiro", "w"), ("Total", "center"), 
            ("Pago", "center"), ("Saldo", "center"), ("Ação", "center")
        ]
        
        for i, (h, anchor) in enumerate(headers):
            ctk.CTkLabel(header_frame, text=h, font=ctk.CTkFont(weight="bold"), text_color="white", anchor=anchor).grid(row=0, column=i, sticky="ew" if anchor=="center" else "w", padx=5, pady=8)

        # Área rolável para os passageiros
        self.scroll_fin = ctk.CTkScrollableFrame(parent, fg_color="#F8F9FA")
        self.scroll_fin.pack(fill="both", expand=True, padx=20, pady=(5, 20))

    def salvar_custos(self):
        try:
            c_onibus = float(self.entry_custo_onibus.get().replace("R$", "").replace(".", "").replace(",", ".").strip() or 0)
            c_adicional = float(self.entry_custos_adicionais.get().replace("R$", "").replace(".", "").replace(",", ".").strip() or 0)
        except ValueError:
            messagebox.showwarning("Aviso", "Valores de custo inválidos.", parent=self)
            return
            
        conn = self._conectar()
        conn.execute("UPDATE passeios SET custo_onibus=?, custos_adicionais=? WHERE id=?", (c_onibus, c_adicional, self.id_passeio))
        conn.commit()
        conn.close()
        self.carregar_financeiro()
        messagebox.showinfo("Sucesso", "Custos salvos com sucesso!", parent=self)
        
    def gerar_balanco(self):
        try:
            from gerador_pdf import gerar_balanco_financeiro
            gerar_balanco_financeiro(self.id_passeio)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar balanço: {e}", parent=self)

    def carregar_financeiro(self):
        conn = self._conectar()
        cursor = conn.cursor()
        
        cursor.execute("SELECT custo_onibus, custos_adicionais, valor_passeio FROM passeios WHERE id = ?", (self.id_passeio,))
        passeio = cursor.fetchone()
        self.custo_onibus = passeio[0] if passeio and passeio[0] else 0.0
        self.custos_adicionais = passeio[1] if passeio and passeio[1] else 0.0
        self.valor_base_passeio = passeio[2] if passeio and passeio[2] else 0.0
        
        self.entry_custo_onibus.delete(0, 'end')
        self.entry_custo_onibus.insert(0, f"{self.custo_onibus:.2f}".replace(".", ","))
        self.entry_custos_adicionais.delete(0, 'end')
        self.entry_custos_adicionais.insert(0, f"{self.custos_adicionais:.2f}".replace(".", ","))
        
        query = """
            SELECT 
                a.id as alocacao_id,
                a.numero_poltrona, 
                p.nome_completo,
                COALESCE(pass.valor_passeio, 0) as valor_base,
                a.tipo_desconto,
                a.valor_desconto,
                COALESCE(SUM(pag.valor_pago), 0) as total_pago
            FROM alocacao_poltronas a
            JOIN passageiros p ON a.passageiro_id = p.id
            JOIN passeios pass ON a.passeio_id = pass.id
            LEFT JOIN pagamentos pag ON a.id = pag.alocacao_id
            WHERE a.passeio_id = ?
            GROUP BY a.id, a.numero_poltrona, p.nome_completo, pass.valor_passeio, a.tipo_desconto, a.valor_desconto
            ORDER BY a.numero_poltrona ASC
        """
        cursor.execute(query, (self.id_passeio,))
        self.dados_financeiros = cursor.fetchall()
        conn.close()
        
        self.renderizar_lista_financeira()

    def renderizar_lista_financeira(self):
        for widget in self.scroll_fin.winfo_children():
            widget.destroy()
            
        filtro = self.combo_filtro_fin.get()
        receita_esperada = 0.0
        receita_arrecadada = 0.0
        pagantes_efetivos = 0

        for row in self.dados_financeiros:
            aloc_id, pol, nome, valor_base, tipo_desc, val_desc, total_pago = row
            
            valor_total = valor_base
            if tipo_desc == "valor":
                valor_total -= val_desc
            elif tipo_desc == "porcentagem":
                valor_total -= valor_total * (val_desc / 100)
            valor_total = max(0, valor_total)
            
            saldo = valor_total - total_pago
            
            status = "Pendente"
            if total_pago > 0 and total_pago < valor_total:
                status = "Parcial"
            elif total_pago >= valor_total:
                status = "Quitado"

            receita_esperada += valor_total
            receita_arrecadada += total_pago
            if valor_total > 0: pagantes_efetivos += 1

            if filtro == "Pendentes" and status == "Quitado": continue
            if filtro == "Quitados" and status != "Quitado": continue

            cor_bg = "white"
            row_frame = ctk.CTkFrame(self.scroll_fin, fg_color=cor_bg, corner_radius=5)
            row_frame.pack(fill="x", pady=2)
            
            pesos = [1, 3, 1, 1, 1, 1]
            for i, peso in enumerate(pesos):
                row_frame.grid_columnconfigure(i, weight=peso)

            ctk.CTkLabel(row_frame, text=f"{pol:02d}", text_color="black", anchor="center").grid(row=0, column=0, sticky="ew", padx=5, pady=8)
            ctk.CTkLabel(row_frame, text=nome, text_color="black", anchor="w").grid(row=0, column=1, sticky="ew", padx=5)
            ctk.CTkLabel(row_frame, text=f"R$ {valor_total:.2f}", text_color="black", anchor="center").grid(row=0, column=2, sticky="ew", padx=5)
            ctk.CTkLabel(row_frame, text=f"R$ {total_pago:.2f}", text_color="green" if total_pago > 0 else "black", anchor="center").grid(row=0, column=3, sticky="ew", padx=5)
            
            cor_saldo = "red" if saldo > 0 else "black"
            ctk.CTkLabel(row_frame, text=f"R$ {saldo:.2f}", text_color=cor_saldo, font=ctk.CTkFont(weight="bold"), anchor="center").grid(row=0, column=4, sticky="ew", padx=5)
            
            frame_acao = ctk.CTkFrame(row_frame, fg_color="transparent")
            frame_acao.grid(row=0, column=5, sticky="ew", padx=5)
            
            if status == "Quitado":
                ctk.CTkLabel(frame_acao, text="✅ Quitado", text_color="green", font=ctk.CTkFont(weight="bold")).pack(expand=True)
            else:
                ctk.CTkButton(
                    frame_acao, text="Lançar", width=80, height=25, fg_color="#FF9940", hover_color="#E07820",
                    command=lambda a=aloc_id, n=nome, p=pol, s=saldo: self.abrir_modal_pagamento(a, n, p, s)
                ).pack(expand=True)

        custos_totais = self.custo_onibus + self.custos_adicionais
        lucro = receita_esperada - custos_totais
        
        # Ponto de Equilíbrio
        if self.valor_base_passeio > 0:
            ponto_equilibrio = math.ceil(custos_totais / self.valor_base_passeio)
            if pagantes_efetivos >= ponto_equilibrio:
                texto_pe = f"✅ Viagem operando no lucro! (Mínimo: {ponto_equilibrio} passagens vendidas)"
                cor_pe = "green"
            else:
                faltam = ponto_equilibrio - pagantes_efetivos
                texto_pe = f"⚠️ Faltam {faltam} passagens para atingir o lucro. (Mínimo: {ponto_equilibrio})"
                cor_pe = "#C0392B"
        else:
            texto_pe = "Defina o valor base do passeio para calcular o ponto de equilíbrio."
            cor_pe = "#192E33"

        self.lbl_receita_esperada.configure(text=f"R$ {receita_esperada:.2f}".replace(".", ","))
        self.lbl_custos_totais.configure(text=f"R$ {custos_totais:.2f}".replace(".", ","))
        self.lbl_lucro_projetado.configure(text=f"R$ {lucro:.2f}".replace(".", ","))
        self.lbl_ponto_equilibrio.configure(text=texto_pe, text_color=cor_pe)

    def abrir_modal_pagamento(self, aloc_id, nome, poltrona, saldo_devedor):
        LancarPagamentoWindow(self, aloc_id, nome, poltrona, saldo_devedor, self.carregar_financeiro)
