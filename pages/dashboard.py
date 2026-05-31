import customtkinter as ctk
import sqlite3
import os
import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "sistema_viagens.db")

class DashboardFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.cor_texto = "#192E33"
        self.cor_azul = "#3D7BA3"
        self.cor_laranja = "#FF9940"
        
        ctk.CTkLabel(self, text="🏠 Dashboard Estratégico", font=ctk.CTkFont(size=28, weight="bold"), text_color=self.cor_texto).pack(anchor="w", pady=(0, 20))
        
        self.stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_frame.pack(fill="x", pady=(0, 20))
        self.stats_frame.grid_columnconfigure((0, 1), weight=1)
        
        self.card_passeios = self._criar_card(self.stats_frame, 0, "🗺️ Passeios Ativos", "0", self.cor_azul)
        self.card_passageiros = self._criar_card(self.stats_frame, 1, "👥 Total de Passageiros", "0", "#27AE60")
        
        # Central View
        self.main_view = ctk.CTkFrame(self, fg_color="transparent")
        self.main_view.pack(fill="both", expand=True)
        self.main_view.grid_columnconfigure(0, weight=3)
        self.main_view.grid_columnconfigure(1, weight=1)
        
        self._construir_proximos_passeios()
        self._construir_atalhos()
        
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
        
    def _construir_proximos_passeios(self):
        frame = ctk.CTkFrame(self.main_view, fg_color="#F8F9FA", corner_radius=15)
        frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        ctk.CTkLabel(frame, text="Próximos Passeios", font=ctk.CTkFont(size=20, weight="bold"), text_color=self.cor_texto).pack(anchor="w", padx=20, pady=20)
        
        self.scroll_passeios = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        self.scroll_passeios.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
    def _construir_atalhos(self):
        frame = ctk.CTkFrame(self.main_view, fg_color="#F8F9FA", corner_radius=15)
        frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        ctk.CTkLabel(frame, text="Acesso Rápido", font=ctk.CTkFont(size=20, weight="bold"), text_color=self.cor_texto).pack(anchor="w", padx=20, pady=20)
        
        ctk.CTkButton(
            frame, text="➕ Cadastrar Passeio", font=ctk.CTkFont(weight="bold"), 
            height=50, fg_color=self.cor_laranja, hover_color="#E07820",
            command=lambda: self.master.master.navegar("Passeios", acao_pos_navegacao=lambda p: p.abrir_formulario())
        ).pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkButton(
            frame, text="➕ Cadastrar Passageiro", font=ctk.CTkFont(weight="bold"), 
            height=50, fg_color=self.cor_azul, hover_color="#2A5A7A",
            command=lambda: self.master.master.navegar("Passageiros", acao_pos_navegacao=lambda p: p.abrir_formulario())
        ).pack(fill="x", padx=20)

    def abrir_mapa_onibus(self, id_passeio):
        from pages.mapa_onibus import MapaOnibusWindow
        MapaOnibusWindow(self, id_passeio)

    def carregar_passeios(self):
        # Alias para caso o MapaOnibusWindow tente recarregar os dados no parent ao fechar
        self.carregar_dados()

    def carregar_dados(self):
        conn = self._conectar()
        cursor = conn.cursor()
        
        # Count active passeios
        cursor.execute("SELECT COUNT(*) FROM passeios WHERE status='A realizar'")
        total_ativos = cursor.fetchone()[0]
        self.card_passeios.configure(text=str(total_ativos))
        
        # Count passengers
        cursor.execute("SELECT COUNT(*) FROM passageiros")
        total_pass = cursor.fetchone()[0]
        self.card_passageiros.configure(text=str(total_pass))
        
        # Fetch upcoming passeios with occupancy
        # O SQLite usa o formato YYYY-MM-DD para datas, o que permite ordenar corretamente.
        query = """
            SELECT p.id, p.destino, p.data_passeio, p.capacidade, COUNT(a.id) as ocupados
            FROM passeios p
            LEFT JOIN alocacao_poltronas a ON p.id = a.passeio_id
            WHERE p.status = 'A realizar'
            GROUP BY p.id
            ORDER BY p.data_passeio ASC
            LIMIT 10
        """
        cursor.execute(query)
        proximos = cursor.fetchall()
        conn.close()
        
        for widget in self.scroll_passeios.winfo_children():
            widget.destroy()
            
        if not proximos:
            ctk.CTkLabel(self.scroll_passeios, text="Nenhum passeio programado no momento.", text_color="#7F8C8D").pack(pady=20)
            return
            
        for passeio in proximos:
            id_p, destino, data_p, capacidade, ocupados = passeio
            if not capacidade: capacidade = 50
            
            p_frame = ctk.CTkFrame(self.scroll_passeios, fg_color="white", corner_radius=8, cursor="hand2")
            p_frame.pack(fill="x", pady=5)
            
            click_cmd = lambda e, p=id_p: self.abrir_mapa_onibus(p)
            p_frame.bind("<Button-1>", click_cmd)
            
            header = ctk.CTkFrame(p_frame, fg_color="transparent", cursor="hand2")
            header.pack(fill="x", padx=15, pady=(10, 5))
            header.bind("<Button-1>", click_cmd)
            
            lbl_dest = ctk.CTkLabel(header, text=f"📍 {destino}", font=ctk.CTkFont(weight="bold", size=16), text_color=self.cor_texto, cursor="hand2")
            lbl_dest.pack(side="left")
            lbl_dest.bind("<Button-1>", click_cmd)
            
            try:
                data_formatada = datetime.datetime.strptime(data_p, "%Y-%m-%d").strftime("%d/%m/%Y")
            except ValueError:
                data_formatada = data_p
                
            lbl_data = ctk.CTkLabel(header, text=f"📅 {data_formatada}", font=ctk.CTkFont(size=14), text_color=self.cor_azul, cursor="hand2")
            lbl_data.pack(side="right")
            lbl_data.bind("<Button-1>", click_cmd)
            
            prog_frame = ctk.CTkFrame(p_frame, fg_color="transparent", cursor="hand2")
            prog_frame.pack(fill="x", padx=15, pady=(0, 10))
            prog_frame.bind("<Button-1>", click_cmd)
            
            lbl_lot = ctk.CTkLabel(prog_frame, text=f"Lotação: {ocupados}/{capacidade}", font=ctk.CTkFont(size=12), text_color="#7F8C8D", cursor="hand2")
            lbl_lot.pack(side="right")
            lbl_lot.bind("<Button-1>", click_cmd)
            
            prog_bar = ctk.CTkProgressBar(prog_frame, height=10, fg_color="#E4F7FE", progress_color=self.cor_laranja if ocupados >= capacidade else self.cor_azul)
            prog_bar.pack(side="left", fill="x", expand=True, padx=(0, 10))
            if hasattr(prog_bar, "_canvas"):
                prog_bar._canvas.bind("<Button-1>", click_cmd)
            prog_bar.set(ocupados / capacidade if capacidade > 0 else 0)
