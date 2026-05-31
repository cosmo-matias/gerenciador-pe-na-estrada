import sqlite3
import os
import datetime
import customtkinter as ctk

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "sistema_viagens.db")

class FinanceiroFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.cor_texto = "#192E33"
        self.cor_azul = "#3D7BA3"
        self.cor_verde = "#27AE60"
        self.cor_vermelha = "#C0392B"
        
        ctk.CTkLabel(self, text="💰 Fluxo de Caixa Global", font=ctk.CTkFont(size=28, weight="bold"), text_color=self.cor_texto).pack(anchor="w", pady=(0, 20))
        
        self.stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_frame.pack(fill="x", pady=(0, 20))
        self.stats_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        self.lbl_faturamento = self._criar_card(self.stats_frame, 0, "Faturamento Total", "R$ 0,00", self.cor_verde)
        self.lbl_custos = self._criar_card(self.stats_frame, 1, "Custos Operacionais", "R$ 0,00", self.cor_vermelha)
        self.lbl_lucro = self._criar_card(self.stats_frame, 2, "Lucro Líquido Global", "R$ 0,00", self.cor_azul)
        
        # Central View
        self.main_view = ctk.CTkFrame(self, fg_color="transparent")
        self.main_view.pack(fill="both", expand=True)
        
        self._construir_tabela()
        self.carregar_dados()
        
    def _conectar(self):
        return sqlite3.connect(DB_PATH)
        
    def _criar_card(self, parent, col, titulo, valor, cor):
        card = ctk.CTkFrame(parent, fg_color=cor, corner_radius=15)
        card.grid(row=0, column=col, sticky="ew", padx=10)
        ctk.CTkLabel(card, text=titulo, font=ctk.CTkFont(size=16), text_color="#E4F7FE").pack(pady=(20, 5))
        lbl_valor = ctk.CTkLabel(card, text=valor, font=ctk.CTkFont(size=36, weight="bold"), text_color="white")
        lbl_valor.pack(pady=(0, 20))
        return lbl_valor
        
    def _construir_tabela(self):
        frame = ctk.CTkFrame(self.main_view, fg_color="#F8F9FA", corner_radius=15)
        frame.pack(fill="both", expand=True, padx=10)
        
        ctk.CTkLabel(frame, text="Performance de Viagens (Histórico)", font=ctk.CTkFont(size=20, weight="bold"), text_color=self.cor_texto).pack(anchor="w", padx=20, pady=20)
        
        # Cabeçalho da Lista
        header_frame = ctk.CTkFrame(frame, fg_color="#192E33", corner_radius=8)
        header_frame.pack(fill="x", padx=20, pady=(0, 0))
        
        pesos = [3, 2, 2, 2, 2]
        for i, peso in enumerate(pesos):
            header_frame.grid_columnconfigure(i, weight=peso)
        
        headers = [
            ("Destino", "w"), ("Data", "center"), ("Receita Realizada", "center"), 
            ("Custos Operacionais", "center"), ("Lucro", "center")
        ]
        
        for i, (h, anchor) in enumerate(headers):
            ctk.CTkLabel(header_frame, text=h, font=ctk.CTkFont(weight="bold"), text_color="white", anchor=anchor).grid(row=0, column=i, sticky="ew" if anchor=="center" else "w", padx=5, pady=8)
            
        self.scroll_tabela = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        self.scroll_tabela.pack(fill="both", expand=True, padx=20, pady=(5, 20))
        
    def carregar_dados(self):
        conn = self._conectar()
        cursor = conn.cursor()
        
        # Faturamento Total
        cursor.execute("SELECT COALESCE(SUM(valor_pago), 0) FROM pagamentos")
        faturamento_total = cursor.fetchone()[0]
        
        # Custos Operacionais Totais
        cursor.execute("SELECT COALESCE(SUM(custo_onibus + custos_adicionais), 0) FROM passeios")
        custos_totais = cursor.fetchone()[0]
        
        lucro_global = faturamento_total - custos_totais
        
        self.lbl_faturamento.configure(text=f"R$ {faturamento_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        self.lbl_custos.configure(text=f"R$ {custos_totais:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        self.lbl_lucro.configure(text=f"R$ {lucro_global:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        
        # Tabela de Performance
        query = """
            SELECT 
                p.destino, 
                p.data_passeio, 
                COALESCE((SELECT SUM(pag.valor_pago) FROM pagamentos pag JOIN alocacao_poltronas a ON pag.alocacao_id = a.id WHERE a.passeio_id = p.id), 0) AS receita,
                (p.custo_onibus + p.custos_adicionais) AS custos
            FROM passeios p
            ORDER BY p.data_passeio DESC
        """
        cursor.execute(query)
        viagens = cursor.fetchall()
        conn.close()
        
        for widget in self.scroll_tabela.winfo_children():
            widget.destroy()
            
        if not viagens:
            ctk.CTkLabel(self.scroll_tabela, text="Nenhum passeio encontrado no histórico.", text_color="#7F8C8D").pack(pady=20)
            return
            
        for idx, viagem in enumerate(viagens):
            destino, data_p, receita, custos = viagem
            lucro = receita - custos
            
            cor_bg = "white" if idx % 2 == 0 else "#F8F9FA"
            row_frame = ctk.CTkFrame(self.scroll_tabela, fg_color=cor_bg, corner_radius=5)
            row_frame.pack(fill="x", pady=2)
            
            pesos = [3, 2, 2, 2, 2]
            for i, peso in enumerate(pesos):
                row_frame.grid_columnconfigure(i, weight=peso)
                
            try:
                data_formatada = datetime.datetime.strptime(data_p, "%Y-%m-%d").strftime("%d/%m/%Y")
            except ValueError:
                data_formatada = data_p

            ctk.CTkLabel(row_frame, text=destino, text_color="black", anchor="w").grid(row=0, column=0, sticky="ew", padx=5, pady=8)
            ctk.CTkLabel(row_frame, text=data_formatada, text_color="black", anchor="center").grid(row=0, column=1, sticky="ew", padx=5)
            ctk.CTkLabel(row_frame, text=f"R$ {receita:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), text_color="#27AE60", anchor="center").grid(row=0, column=2, sticky="ew", padx=5)
            ctk.CTkLabel(row_frame, text=f"R$ {custos:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), text_color="#C0392B", anchor="center").grid(row=0, column=3, sticky="ew", padx=5)
            
            cor_lucro = "#27AE60" if lucro >= 0 else "#C0392B"
            ctk.CTkLabel(row_frame, text=f"R$ {lucro:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), text_color=cor_lucro, font=ctk.CTkFont(weight="bold"), anchor="center").grid(row=0, column=4, sticky="ew", padx=5)
