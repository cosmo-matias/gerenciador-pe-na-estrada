import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "sistema_viagens.db")

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE passeios RENAME COLUMN local TO locais_embarque;")
    except sqlite3.OperationalError:
        print("Column local already renamed or does not exist")

    try:
        cursor.execute("ALTER TABLE passeios ADD COLUMN local_destino TEXT;")
    except sqlite3.OperationalError:
        print("Column local_destino already exists")
    
    conn.commit()
    conn.close()
    print("Migration done.")

if __name__ == "__main__":
    migrate()
