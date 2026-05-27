"""
main.py
-------
Arquivo principal do sistema de gerenciamento da agência Pé Na Estrada Tour.
Responsável por inicializar a janela principal e a estrutura de navegação
da interface gráfica construída com CustomTkinter.

Fase 3 (revisão): Identidade visual oficial aplicada.
"""

import customtkinter as ctk
from PIL import Image
import os

from database import criar_tabelas

# --- Importação das páginas reais ---
from pages.passageiros import PassageirosFrame
from pages.passeios import PasseiosFrame

# ---------------------------------------------------------------------------
# Configuração global do tema
# ---------------------------------------------------------------------------
ctk.set_appearance_mode("light")       # Fundo principal claro (#E4F7FE)
ctk.set_default_color_theme("blue")

# ---------------------------------------------------------------------------
# Paleta de cores oficial — Pé Na Estrada Tour
# ---------------------------------------------------------------------------
CORES = {
    # Identidade oficial
    "sidebar_bg":       "#192E33",   # Azul muito escuro — fundo da sidebar
    "main_bg":          "#E4F7FE",   # Azul gelo claro   — fundo do main frame
    "azul_principal":   "#3D7BA3",   # Azul principal
    "laranja":          "#FF9940",   # Laranja vibrante  — hover / destaque

    # Derivados para uso na sidebar
    "sidebar_active":   "#3D7BA3",   # Fundo do botão ativo
    "sidebar_hover":    "#FF9940",   # Hover dos botões
    "btn_texto":        "#FFFFFF",   # Texto dos botões da sidebar
    "btn_ativo_txt":    "#FFFFFF",   # Texto do botão ativo

    # Texto no main frame (contraste sobre fundo claro)
    "texto_escuro":     "#192E33",   # Títulos e texto principal no main frame
    "texto_medio":      "#3D7BA3",   # Subtítulos e texto secundário
    "texto_sidebar":    "#B0CDD4",   # Texto suave dentro da sidebar

    # Separadores e utilitários
    "separador":        "#2A4A52",   # Linha divisória na sidebar
    "separador_main":   "#BDDDE8",   # Linha divisória no main frame
}

# ---------------------------------------------------------------------------
# Páginas disponíveis no menu lateral
# ---------------------------------------------------------------------------
PAGINAS = [
    {"nome": "Dashboard",   "icone": "🏠"},
    {"nome": "Passeios",    "icone": "🗺️"},
    {"nome": "Passageiros", "icone": "👥"},
    {"nome": "Financeiro",  "icone": "💰"},
]

# Diretório base do projeto (mesmo diretório deste arquivo)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ===========================================================================
# Classe principal da aplicação
# ===========================================================================

class App(ctk.CTk):
    """
    Janela principal do sistema Pé Na Estrada Tour.

    Gerencia o layout base (sidebar + frame principal) e
    o roteamento entre os módulos do sistema.
    """

    def __init__(self):
        super().__init__()

        # --- Configuração da janela ---
        self.title("Gerenciador - Pé Na Estrada Tour")
        self.geometry("1024x768")
        self.minsize(900, 600)
        self.configure(fg_color=CORES["main_bg"])

        # Estado de navegação
        self._pagina_ativa: str = ""
        self._botoes_nav: dict[str, ctk.CTkButton] = {}

        # Garante que o banco de dados esteja pronto
        criar_tabelas()

        # Monta a interface
        self._construir_layout()

        # Abre na página inicial
        self.navegar("Dashboard")

    # -----------------------------------------------------------------------
    # Layout
    # -----------------------------------------------------------------------

    def _construir_layout(self):
        """Define o grid principal: sidebar fixa + frame principal expansível."""
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)   # Sidebar: largura fixa
        self.grid_columnconfigure(1, weight=1)   # Main frame: expansível

        self._construir_sidebar()
        self._construir_frame_principal()

    def _construir_sidebar(self):
        """Constrói a barra lateral com logo, menu e rodapé."""

        self.sidebar = ctk.CTkFrame(
            self,
            width=210,
            corner_radius=0,
            fg_color=CORES["sidebar_bg"],
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(9, weight=1)  # Empurra rodapé para baixo

        # --- Logo ---
        self._carregar_logo()

        # --- Separador após o logo ---
        ctk.CTkFrame(
            self.sidebar,
            height=1,
            fg_color=CORES["separador"],
            corner_radius=0,
        ).grid(row=1, column=0, padx=16, pady=(4, 8), sticky="ew")

        # --- Label da seção de menu ---
        ctk.CTkLabel(
            self.sidebar,
            text="MENU",
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
            text_color=CORES["texto_sidebar"],
        ).grid(row=2, column=0, padx=20, pady=(0, 4), sticky="w")

        # --- Botões de navegação ---
        for i, pagina in enumerate(PAGINAS):
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"  {pagina['icone']}   {pagina['nome']}",
                font=ctk.CTkFont(family="Segoe UI", size=13),
                anchor="w",                          # Texto alinhado à esquerda
                height=44,
                corner_radius=8,
                fg_color="transparent",              # Fundo transparente por padrão
                text_color=CORES["btn_texto"],       # Texto branco
                hover_color=CORES["sidebar_hover"],  # Laranja no hover
                command=lambda nome=pagina["nome"]: self.navegar(nome),
            )
            btn.grid(row=3 + i, column=0, padx=10, pady=2, sticky="ew")
            self._botoes_nav[pagina["nome"]] = btn

        # --- Rodapé ---
        frame_rodape = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        frame_rodape.grid(row=9, column=0, padx=16, pady=16, sticky="sew")

        ctk.CTkFrame(
            frame_rodape, height=1, fg_color=CORES["separador"]
        ).pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            frame_rodape,
            text="v1.0.0  •  2025",
            font=ctk.CTkFont(size=10),
            text_color=CORES["texto_sidebar"],
        ).pack(side="bottom")

    def _carregar_logo(self):
        """
        Carrega e exibe a logo da agência no topo da sidebar.
        Se o arquivo 'logo.png' não for encontrado, exibe o nome
        da empresa como fallback em texto.
        """
        caminho_logo = os.path.join(BASE_DIR, "logo.png")

        frame_logo = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent",
        )
        frame_logo.grid(row=0, column=0, padx=0, pady=0, sticky="ew")

        if os.path.isfile(caminho_logo):
            # --- Logo via imagem PNG ---
            try:
                imagem = ctk.CTkImage(
                    light_image=Image.open(caminho_logo),
                    dark_image=Image.open(caminho_logo),
                    size=(150, 150),
                )
                ctk.CTkLabel(
                    frame_logo,
                    image=imagem,
                    text="",           # Sem texto — apenas a imagem
                    fg_color="transparent",
                ).pack(pady=(20, 8))

            except Exception as e:
                print(f"[AVISO] Não foi possível carregar logo.png: {e}")
                self._logo_texto_fallback(frame_logo)
        else:
            # --- Fallback: nome em texto quando logo.png não existe ---
            print("[AVISO] logo.png não encontrado — usando fallback de texto.")
            self._logo_texto_fallback(frame_logo)

    def _logo_texto_fallback(self, parent):
        """Exibe o nome da empresa em texto como substituto à logo."""
        ctk.CTkLabel(
            parent,
            text="✈️",
            font=ctk.CTkFont(size=40),
            text_color=CORES["laranja"],
        ).pack(pady=(22, 4))

        ctk.CTkLabel(
            parent,
            text="Pé Na Estrada",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=CORES["laranja"],
        ).pack()

        ctk.CTkLabel(
            parent,
            text="TOUR",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=CORES["texto_sidebar"],
        ).pack(pady=(0, 8))

    def _construir_frame_principal(self):
        """Constrói a área principal onde os módulos são exibidos."""
        self.frame_principal = ctk.CTkFrame(
            self,
            corner_radius=0,
            fg_color=CORES["main_bg"],
        )
        self.frame_principal.grid(row=0, column=1, sticky="nsew")
        self.frame_principal.grid_rowconfigure(0, weight=1)
        self.frame_principal.grid_columnconfigure(0, weight=1)

    # -----------------------------------------------------------------------
    # Roteamento / Navegação
    # -----------------------------------------------------------------------

    def navegar(self, nome_pagina: str):
        """
        Alterna o módulo exibido no frame principal.

        Limpa os widgets existentes e carrega o conteúdo
        correspondente à página selecionada no menu.

        Args:
            nome_pagina (str): Nome da página a ser exibida.
        """
        if nome_pagina == self._pagina_ativa:
            return

        self._pagina_ativa = nome_pagina
        self._atualizar_botao_ativo(nome_pagina)

        # Remove todos os widgets do frame principal
        for widget in self.frame_principal.winfo_children():
            widget.destroy()

        self._carregar_pagina(nome_pagina)

    def _atualizar_botao_ativo(self, nome_pagina: str):
        """
        Destaca visualmente o botão da página ativa na sidebar.
        Botões inativos voltam ao estilo padrão (transparente).

        Args:
            nome_pagina (str): Nome da página recém-ativada.
        """
        for nome, btn in self._botoes_nav.items():
            if nome == nome_pagina:
                btn.configure(
                    fg_color=CORES["sidebar_active"],   # Azul principal no ativo
                    text_color=CORES["btn_ativo_txt"],
                    hover_color=CORES["sidebar_active"],
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=CORES["btn_texto"],
                    hover_color=CORES["sidebar_hover"],
                )

    def _carregar_pagina(self, nome_pagina: str):
        """
        Renderiza o conteúdo da página no frame principal.

        Páginas com módulo implementado são carregadas diretamente.
        Páginas ainda em desenvolvimento exibem um placeholder.

        Args:
            nome_pagina (str): Nome da página a ser renderizada.
        """
        # --- Roteamento: mapeia nome → classe do módulo ---
        rotas: dict[str, type] = {
            "Passageiros": PassageirosFrame,
            "Passeios": PasseiosFrame,
            # Próximas fases:
            # "Dashboard":  DashboardPage,
            # "Financeiro": FinanceiroPage,
        }

        # Carrega o módulo real, se disponível
        if nome_pagina in rotas:
            pagina = rotas[nome_pagina](self.frame_principal)
            pagina.pack(fill="both", expand=True)
            return

        # --- Placeholder para páginas em desenvolvimento ---
        icone = next(
            (p["icone"] for p in PAGINAS if p["nome"] == nome_pagina), "📄"
        )

        container = ctk.CTkFrame(self.frame_principal, fg_color="transparent")
        container.place(relx=0.5, rely=0.5, anchor="center")

        # Ícone da página
        ctk.CTkLabel(
            container,
            text=icone,
            font=ctk.CTkFont(size=60),
        ).pack(pady=(0, 12))

        # Título "Módulo: <Nome>" — cor escura para contraste com o fundo claro
        ctk.CTkLabel(
            container,
            text=f"Módulo: {nome_pagina}",
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            text_color=CORES["texto_escuro"],          # #192E33 sobre #E4F7FE
        ).pack()

        # Subtítulo
        ctk.CTkLabel(
            container,
            text="Esta seção está em desenvolvimento.\nO conteúdo será carregado em breve.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=CORES["azul_principal"],        # #3D7BA3
            justify="center",
        ).pack(pady=(8, 24))

        # Badge de status
        ctk.CTkLabel(
            container,
            text="  EM DESENVOLVIMENTO  ",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=CORES["laranja"],
            fg_color=CORES["sidebar_bg"],
            corner_radius=20,
        ).pack()


# ===========================================================================
# Ponto de entrada
# ===========================================================================
if __name__ == "__main__":
    app = App()
    app.mainloop()
