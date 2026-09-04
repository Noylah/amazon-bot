import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_GROUP_ID = int(os.getenv("ADMIN_GROUP_ID", "-1004354827440"))
CEO_USERNAME = os.getenv("CEO_USERNAME", "").lstrip("@").strip().lower()

ROLES = (
    "C.E.O.",
    "Dirigente Operativo",
    "Assistente Esecutivo",
    "Manager di Linea",
    "Dipendente",
    "Dipendente in Prova",
)

ROLE_LEVELS = {role: len(ROLES) - index for index, role in enumerate(ROLES)}


if not BOT_TOKEN:
    raise RuntimeError("Imposta la variabile d'ambiente BOT_TOKEN prima di avviare il bot.")
