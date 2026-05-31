import customtkinter as ctk
import tkinter.filedialog
import tkinter.messagebox as messagebox
import shutil
import os
from datetime import datetime

class ConfiguracoesFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        # Container principal
        self.container = ctk.CTkFrame(self, fg_color="#F8F9FA", corner_radius=15)
        self.container.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        self._construir_header()
        
        # Painel de Backup
        self._construir_painel_backup()
        
        # Informações do Sistema
        self._construir_info_sistema()

    def _construir_header(self):
        header_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        header_frame.pack(fill="x", padx=30, pady=(30, 20))
        
        ctk.CTkLabel(
            header_frame, text="Configurações e Segurança",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color="#192E33"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            header_frame, text="Gerencie seus backups e configurações de sistema.",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color="#3D7BA3"
        ).pack(anchor="w", pady=(5, 0))

    def _construir_painel_backup(self):
        painel = ctk.CTkFrame(self.container, fg_color="white", corner_radius=10)
        painel.pack(fill="x", padx=30, pady=10)
        
        ctk.CTkLabel(
            painel, text="Backup Manual",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color="#192E33"
        ).pack(anchor="w", padx=20, pady=(20, 5))
        
        ctk.CTkLabel(
            painel, text="Exporte um backup seguro de todos os seus dados operacionais e financeiros. É recomendado fazer isso regularmente.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#555555",
            wraplength=700, justify="left"
        ).pack(anchor="w", padx=20, pady=(0, 15))
        
        ctk.CTkButton(
            painel, text="📦 Exportar Backup do Banco de Dados",
            font=ctk.CTkFont(weight="bold", size=14),
            fg_color="#3D7BA3", hover_color="#2A5A7A", height=45,
            command=self.exportar_backup
        ).pack(anchor="w", padx=20, pady=(0, 20))

    def _construir_info_sistema(self):
        info_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        info_frame.pack(fill="x", side="bottom", padx=30, pady=30)
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, "sistema_viagens.db")
        
        ctk.CTkLabel(
            info_frame, text="Informações do Sistema",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#192E33"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            info_frame, text="Versão do Sistema: 1.0",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#555555"
        ).pack(anchor="w", pady=(10, 2))
        
        ctk.CTkLabel(
            info_frame, text=f"Localização do Banco de Dados Atual:\n{db_path}",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#777777", justify="left"
        ).pack(anchor="w")

    def exportar_backup(self):
        diretorio_destino = tkinter.filedialog.askdirectory(title="Selecione a pasta para salvar o backup")
        
        if not diretorio_destino:
            return # Usuário cancelou
            
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_origem = os.path.join(base_dir, "sistema_viagens.db")
        
        if not os.path.exists(db_origem):
            messagebox.showerror("Erro", "Arquivo de banco de dados não encontrado.")
            return
            
        agora = datetime.now().strftime("%Y-%m-%d_%H%M")
        nome_arquivo = f"backup_penaestrada_{agora}.db"
        db_destino = os.path.join(diretorio_destino, nome_arquivo)
        
        try:
            shutil.copy2(db_origem, db_destino)
            messagebox.showinfo("Sucesso", f"Backup exportado com sucesso!\n\nArquivo salvo em:\n{db_destino}")
        except Exception as e:
            messagebox.showerror("Erro de Cópia", f"Falha ao realizar o backup: {str(e)}")
