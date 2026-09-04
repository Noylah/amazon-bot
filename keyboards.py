from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="👤 Il mio profilo", callback_data="profile"), InlineKeyboardButton(text="📦 I miei pacchi", callback_data="packages")],
        [InlineKeyboardButton(text="📦 Pacchi del team", callback_data="team_packages"), InlineKeyboardButton(text="📑 Inserimenti settimanali", callback_data="weekly")],
        [InlineKeyboardButton(text="🏖 Richiedi congedo", callback_data="request_leave"), InlineKeyboardButton(text="📜 Le mie richieste", callback_data="my_leaves")],
        [InlineKeyboardButton(text="🧰 Richiedi rifornimento", callback_data="supplies"), InlineKeyboardButton(text="📦 I miei rifornimenti", callback_data="my_supplies")],
        [InlineKeyboardButton(text="🚩 Segnala un collega", callback_data="report")],
        [InlineKeyboardButton(text="❓ Guida", callback_data="guide")],
    ]
    if is_admin:
        rows.append([InlineKeyboardButton(text="🛠 Pannello admin", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_keyboard(callback_data: str = "back_main") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="« Indietro", callback_data=callback_data)]])


def leave_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Attivi", callback_data="leaves_active"), InlineKeyboardButton(text="📚 Passati", callback_data="leaves_past")],
        [InlineKeyboardButton(text="« Indietro", callback_data="back_main")],
    ])


def admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Registra dipendente", callback_data="admin_register")],
        [InlineKeyboardButton(text="📑 Inserisci pacchi settimana", callback_data="admin_weekly")],
        [InlineKeyboardButton(text="🏖 Gestisci congedi", callback_data="admin_leaves")],
        [InlineKeyboardButton(text="« Indietro", callback_data="back_main")],
    ])
