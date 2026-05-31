import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "sistema_viagens.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE passeios ADD COLUMN custo_onibus REAL DEFAULT 0.0")
    print("Coluna custo_onibus adicionada.")
except sqlite3.OperationalError:
    print("Coluna custo_onibus já existe.")

try:
    cursor.execute("ALTER TABLE passeios ADD COLUMN custos_adicionais REAL DEFAULT 0.0")
    print("Coluna custos_adicionais adicionada.")
except sqlite3.OperationalError:
    print("Coluna custos_adicionais já existe.")

conn.commit()
conn.close()
