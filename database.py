import sqlite3
from datetime import datetime

DB_NAME = "azienda_roleplay.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        # Tabella Dipendenti
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dipendenti (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                ruolo TEXT DEFAULT 'Dipendente in prova',
                contratto INTEGER DEFAULT 279,
                data_assunzione TEXT,
                periodo_prova_gg INTEGER DEFAULT 7,
                nome_mc TEXT,
                pacchi_totali INTEGER DEFAULT 0,
                pacchi_settimana INTEGER DEFAULT 0,
                ore_settimana TEXT DEFAULT '—',
                warn INTEGER DEFAULT 0
            )
        ''')
        # Tabella Congedi
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS congedi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                data_inizio TEXT,
                data_fine TEXT,
                motivo TEXT,
                stato TEXT DEFAULT 'IN_ATTESA'
            )
        ''')
        # Tabella Testo Pacchi Team
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS impostazioni (
                chiave TEXT PRIMARY KEY,
                valore TEXT
            )
        ''')
        conn.commit()

def get_user(telegram_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM dipendenti WHERE telegram_id = ?", (telegram_id,))
        return cursor.fetchone()

def get_user_by_username(username: str):
    username = username.replace("@", "").strip()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM dipendenti WHERE LOWER(username) = LOWER(?)", (username,))
        return cursor.fetchone()

def get_all_users():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT telegram_id, nome_mc, username, ruolo FROM dipendenti")
        return cursor.fetchall()

def register_user(telegram_id: int, username: str, first_name: str, nome_mc: str):
    data_oggi = datetime.now().strftime("%Y-%m-%d")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO dipendenti 
            (telegram_id, username, first_name, ruolo, contratto, data_assunzione, periodo_prova_gg, nome_mc, pacchi_totali, pacchi_settimana, ore_settimana, warn)
            VALUES (?, ?, ?, 'Dipendente in prova', 279, ?, 14, ?, 0, 0, '—', 0)
        ''', (telegram_id, username, first_name, data_oggi, nome_mc))
        conn.commit()

def update_warn(telegram_id: int, delta: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE dipendenti SET warn = MAX(0, warn + ?) WHERE telegram_id = ?", (delta, telegram_id))
        conn.commit()

def set_periodo_prova(telegram_id: int, giorni: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE dipendenti SET periodo_prova_gg = ? WHERE telegram_id = ?", (giorni, telegram_id))
        conn.commit()

def create_congedo(telegram_id: int, inizio: str, fine: str, motivo: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO congedi (telegram_id, data_inizio, data_fine, motivo)
            VALUES (?, ?, ?, ?)
        ''', (telegram_id, inizio, fine, motivo))
        conn.commit()
        return cursor.lastrowid

def update_congedo_stato(congedo_id: int, stato: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE congedi SET stato = ? WHERE id = ?", (stato, congedo_id))
        conn.commit()

def get_congedo(congedo_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM congedi WHERE id = ?", (congedo_id,))
        return cursor.fetchone()

def set_teampacchi_text(testo: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO impostazioni (chiave, valore) VALUES ('pacchi_team', ?)", (testo,))
        conn.commit()

def get_teampacchi_text():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT valore FROM impostazioni WHERE chiave = 'pacchi_team'")
        res = cursor.fetchone()
        return res[0] if res else "📦 Nessun dato presente per i pacchi del team."