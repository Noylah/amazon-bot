import sqlite3
from datetime import date, datetime, timedelta

DB_NAME = "azienda_roleplay.db"

def get_connection():
    connection = sqlite3.connect(DB_NAME)
    connection.row_factory = sqlite3.Row
    return connection

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dipendenti (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                ruolo TEXT DEFAULT 'Dipendente in Prova',
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
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS impostazioni (
                chiave TEXT PRIMARY KEY,
                valore TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS registrazioni_pendenti (
                username TEXT PRIMARY KEY, nome_mc TEXT NOT NULL, contratto INTEGER NOT NULL,
                periodo_prova_gg INTEGER NOT NULL, created_at TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inserimenti_settimanali (
                id INTEGER PRIMARY KEY AUTOINCREMENT, telegram_id INTEGER NOT NULL,
                nome_mc TEXT NOT NULL, settimana TEXT NOT NULL, valore INTEGER NOT NULL,
                operazione TEXT NOT NULL, created_at TEXT NOT NULL
            )
        ''')
        cursor.execute("UPDATE dipendenti SET ruolo = 'Dipendente in Prova' WHERE ruolo = 'Dipendente in prova'")
        conn.commit()

def set_role(telegram_id: int, ruolo: str) -> bool:
    with get_connection() as conn:
        cursor = conn.execute("UPDATE dipendenti SET ruolo = ? WHERE telegram_id = ?", (ruolo, telegram_id))
        conn.commit()
        return cursor.rowcount == 1

def set_role_by_username(username: str, ruolo: str) -> bool:
    username = username.replace("@", "").strip().lower()
    with get_connection() as conn:
        cursor = conn.execute("UPDATE dipendenti SET ruolo = ? WHERE LOWER(username) = ?", (ruolo, username))
        conn.commit()
        return cursor.rowcount == 1

def apply_ceo_username(username: str) -> bool:
    if not username:
        return False
    return set_role_by_username(username, "C.E.O.")

def get_user(telegram_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM dipendenti WHERE telegram_id = ?", (telegram_id,))
        return cursor.fetchone()

def get_user_by_mc(nome_mc: str):
    with get_connection() as conn:
        return conn.execute("SELECT * FROM dipendenti WHERE LOWER(nome_mc) = LOWER(?)", (nome_mc.strip(),)).fetchone()

def get_user_by_username(username: str):
    username = username.replace("@", "").strip()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM dipendenti WHERE LOWER(username) = LOWER(?)", (username,))
        return cursor.fetchone()

def get_all_users():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM dipendenti ORDER BY LOWER(nome_mc)")
        return cursor.fetchall()

def create_pending_registration(username: str, nome_mc: str, contratto: int, giorni: int):
    username = username.replace("@", "").strip().lower()
    with get_connection() as conn:
        conn.execute("""INSERT INTO registrazioni_pendenti(username, nome_mc, contratto, periodo_prova_gg, created_at)
            VALUES (?, ?, ?, ?, ?) ON CONFLICT(username) DO UPDATE SET nome_mc=excluded.nome_mc,
            contratto=excluded.contratto, periodo_prova_gg=excluded.periodo_prova_gg, created_at=excluded.created_at""",
            (username, nome_mc.strip(), contratto, giorni, datetime.now().isoformat(timespec="seconds")))
        conn.commit()

def activate_pending_registration(telegram_id: int, username: str | None, first_name: str):
    if not username:
        return None
    username = username.replace("@", "").strip().lower()
    with get_connection() as conn:
        pending = conn.execute("SELECT * FROM registrazioni_pendenti WHERE username = ?", (username,)).fetchone()
        if not pending:
            return None
        conn.execute("""INSERT INTO dipendenti(telegram_id, username, first_name, ruolo, contratto,
            data_assunzione, periodo_prova_gg, nome_mc) VALUES (?, ?, ?, 'Dipendente in prova', ?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET username=excluded.username, first_name=excluded.first_name,
            contratto=excluded.contratto, periodo_prova_gg=excluded.periodo_prova_gg, nome_mc=excluded.nome_mc""",
            (telegram_id, username, first_name, pending["contratto"], date.today().isoformat(), pending["periodo_prova_gg"], pending["nome_mc"]))
        conn.execute("DELETE FROM registrazioni_pendenti WHERE username = ?", (username,))
        conn.commit()
    return get_user(telegram_id)

def register_user(telegram_id: int, username: str, first_name: str, nome_mc: str):
    data_oggi = datetime.now().strftime("%Y-%m-%d")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO dipendenti 
            (telegram_id, username, first_name, ruolo, contratto, data_assunzione, periodo_prova_gg, nome_mc, pacchi_totali, pacchi_settimana, ore_settimana, warn)
            VALUES (?, ?, ?, 'Dipendente in Prova', 279, ?, 14, ?, 0, 0, '—', 0)
        ''', (telegram_id, username, first_name, data_oggi, nome_mc))
        conn.commit()

def record_weekly_entry(nome_mc: str, valore: int, incremento: bool):
    user = get_user_by_mc(nome_mc)
    if not user:
        return None
    nuovo_valore = user["pacchi_settimana"] + valore if incremento else valore
    delta_totale = valore if incremento else max(0, valore - user["pacchi_settimana"])
    with get_connection() as conn:
        conn.execute("UPDATE dipendenti SET pacchi_settimana = ?, pacchi_totali = pacchi_totali + ? WHERE telegram_id = ?", (nuovo_valore, delta_totale, user["telegram_id"]))
        conn.execute("INSERT INTO inserimenti_settimanali(telegram_id, nome_mc, settimana, valore, operazione, created_at) VALUES (?, ?, ?, ?, ?, ?)", (user["telegram_id"], user["nome_mc"], week_key(), nuovo_valore, "+" if incremento else "=", datetime.now().isoformat(timespec="seconds")))
        conn.commit()
    return get_user(user["telegram_id"])

def week_key():
    today = date.today()
    return (today - timedelta(days=today.weekday())).isoformat()

def get_user_leaves(telegram_id: int, active: bool):
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM congedi WHERE telegram_id = ? ORDER BY id DESC", (telegram_id,)).fetchall()
    today = date.today()
    result = []
    for row in rows:
        try:
            start_date = datetime.strptime(row["data_inizio"], "%d/%m/%Y").date()
            end_date = datetime.strptime(row["data_fine"], "%d/%m/%Y").date()
        except ValueError:
            continue
        is_active = row["stato"] == "ACCETTATO" and start_date <= today <= end_date
        is_past = row["stato"] == "ACCETTATO" and end_date < today
        if (is_active if active else is_past):
            result.append(row)
    return result

def get_pending_leaves():
    with get_connection() as conn:
        return conn.execute("SELECT c.*, d.nome_mc, d.username FROM congedi c LEFT JOIN dipendenti d ON d.telegram_id = c.telegram_id WHERE c.stato = 'IN_ATTESA' ORDER BY c.id").fetchall()

def get_all_leaves(active: bool):
    users = {row["telegram_id"]: row["nome_mc"] for row in get_all_users()}
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM congedi ORDER BY data_inizio DESC").fetchall()
    today = date.today()
    result = []
    for row in rows:
        try:
            start_date = datetime.strptime(row["data_inizio"], "%d/%m/%Y").date()
            end_date = datetime.strptime(row["data_fine"], "%d/%m/%Y").date()
        except ValueError:
            continue
        is_active = row["stato"] == "ACCETTATO" and start_date <= today <= end_date
        is_past = row["stato"] == "ACCETTATO" and end_date < today
        if (is_active if active else is_past):
            result.append((row, users.get(row["telegram_id"], "Utente")))
    return result

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