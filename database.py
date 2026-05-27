"""
database.py
-----------
Módulo responsável pela inicialização e configuração do banco de dados SQLite
do sistema de gerenciamento de agência de viagens.

Contém as funções de conexão e criação das tabelas principais:
  - passageiros
  - passeios
  - alocacao_poltronas
"""

import sqlite3
import os

# ---------------------------------------------------------------------------
# Configuração do caminho do banco de dados
# O arquivo .db será criado na mesma pasta deste script.
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "sistema_viagens.db")


def conectar() -> sqlite3.Connection:
    """
    Estabelece e retorna uma conexão com o banco de dados SQLite.

    Habilita o suporte a chaves estrangeiras (FOREIGN KEYS), que no SQLite
    precisa ser ativado manualmente a cada nova conexão.

    Returns:
        sqlite3.Connection: Objeto de conexão ativa com o banco de dados.
    """
    conn = sqlite3.connect(DB_PATH)

    # Habilita o suporte a integridade referencial (chaves estrangeiras)
    conn.execute("PRAGMA foreign_keys = ON;")

    # Configura o retorno das linhas como objetos acessíveis por nome de coluna
    conn.row_factory = sqlite3.Row

    return conn


def criar_tabelas() -> None:
    """
    Cria as tabelas do banco de dados caso ainda não existam.

    Tabelas criadas:
        1. passageiros       — Cadastro de passageiros da agência.
        2. passeios          — Registro de passeios/excursões disponíveis.
        3. alocacao_poltronas — Relação entre passageiros e assentos em passeios.

    Utiliza 'IF NOT EXISTS' para garantir idempotência: executar esta função
    múltiplas vezes não causará erros nem perda de dados.
    """
    conn = conectar()

    try:
        cursor = conn.cursor()

        # -------------------------------------------------------------------
        # Tabela 1: passageiros
        # Armazena os dados cadastrais de cada passageiro.
        # -------------------------------------------------------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS passageiros (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_completo   TEXT    NOT NULL,
                data_nascimento TEXT,
                rg              TEXT,
                cpf             TEXT    UNIQUE,
                whatsapp        TEXT
            );
        """)

        # -------------------------------------------------------------------
        # Tabela 2: passeios
        # Armazena as informações de cada excursão/passeio oferecido.
        # -------------------------------------------------------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS passeios (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                destino        TEXT    NOT NULL,
                locais_embarque TEXT,
                local_destino  TEXT,
                data_passeio   TEXT    NOT NULL,
                hora_saida     TEXT,
                hora_retorno   TEXT,
                capacidade     INTEGER,             -- Valores esperados: 30 ou 50
                valor_passeio  REAL,                -- Preço base do passeio
                status         TEXT    DEFAULT 'A realizar'
                                        CHECK(status IN ('A realizar', 'Finalizado', 'Cancelado'))
            );
        """)

        # -------------------------------------------------------------------
        # Tabela 3: alocacao_poltronas
        # Tabela relacional que associa um passageiro a uma poltrona
        # específica dentro de um determinado passeio.
        # -------------------------------------------------------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alocacao_poltronas (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                passeio_id       INTEGER NOT NULL,
                passageiro_id    INTEGER NOT NULL,
                numero_poltrona  INTEGER NOT NULL,
                crianca_colo     TEXT,               -- Nome da criança, se houver, ou NULL
                local_embarque   TEXT,
                tipo_desconto    TEXT
                                    CHECK(tipo_desconto IN ('porcentagem', 'valor', NULL)),
                valor_desconto   REAL,               -- Quantidade do desconto concedido

                -- Chaves estrangeiras com ação em cascata para DELETE
                FOREIGN KEY (passeio_id)    REFERENCES passeios(id)    ON DELETE CASCADE,
                FOREIGN KEY (passageiro_id) REFERENCES passageiros(id) ON DELETE CASCADE,

                -- Garante que um passageiro não ocupe duas poltronas no mesmo passeio
                UNIQUE (passeio_id, passageiro_id),

                -- Garante que uma poltrona não seja atribuída duas vezes no mesmo passeio
                UNIQUE (passeio_id, numero_poltrona)
            );
        """)

        # Confirma todas as alterações no banco de dados
        conn.commit()
        print(f"[OK] Banco de dados inicializado com sucesso em: {DB_PATH}")
        print("[OK] Tabelas 'passageiros', 'passeios' e 'alocacao_poltronas' verificadas/criadas.")

    except sqlite3.Error as e:
        # Em caso de erro, desfaz quaisquer alterações parciais
        conn.rollback()
        print(f"[ERRO] Falha ao criar as tabelas: {e}")
        raise

    finally:
        # Garante que a conexão seja sempre fechada, mesmo em caso de exceção
        conn.close()


# ---------------------------------------------------------------------------
# Ponto de entrada para teste direto do script
# Execute: python database.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 55)
    print("  Sistema de Viagens — Inicialização do Banco de Dados")
    print("=" * 55)
    criar_tabelas()
    print("=" * 55)
