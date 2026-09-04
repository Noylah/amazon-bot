import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_GROUP_ID = int(os.getenv("ADMIN_GROUP_ID", "-1004354827440"))


def _parse_ids(value: str) -> set[int]:
    return {int(item.strip()) for item in value.split(",") if item.strip().isdigit()}


ADMIN_IDS = _parse_ids(os.getenv("ADMIN_IDS", ""))


if not BOT_TOKEN:
    raise RuntimeError("Imposta la variabile d'ambiente BOT_TOKEN prima di avviare il bot.")
