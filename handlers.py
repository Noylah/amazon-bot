import re
from datetime import date, datetime

from aiogram import F, Router, types
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import database as db
from config import ADMIN_GROUP_ID, CEO_USERNAME, ROLE_LEVELS, ROLES
from keyboards import admin_keyboard, back_keyboard, leave_keyboard, main_keyboard
from states import AdminRegistrationStates, LeaveStates, ReportStates, WeeklyEntryStates

router = Router()


def user_role(user_id: int) -> str | None:
    user = db.get_user(user_id)
    return user["ruolo"] if user else None


def can_manage(user_id: int) -> bool:
    return ROLE_LEVELS.get(user_role(user_id), 0) >= ROLE_LEVELS["Manager di Linea"]


def can_assign_roles(user_id: int) -> bool:
    return ROLE_LEVELS.get(user_role(user_id), 0) >= ROLE_LEVELS["Assistente Esecutivo"]


def display_name(user) -> str:
    return user["nome_mc"] if user else "Utente"


def main_text(user) -> str:
    return f"👤 <b>La tua scheda</b>\n\n🪪 Telegram: @{user['username']}\n🏷 Ruolo: {user['ruolo']}\n📦 Pacchi totali: {user['pacchi_totali']}\n\nSeleziona un'opzione dal menu."


def markdown_escape(value: str) -> str:
    return value.replace("_", "\\_").replace("*", "\\*")


@router.message(Command("annulla"))
async def cancel(message: types.Message, state: FSMContext):
    if await state.get_state():
        await state.clear()
        await message.answer("❌ Operazione annullata.")


@router.message(Command("start", "menu"))
async def menu(message: types.Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    if not user:
        user = db.activate_pending_registration(message.from_user.id, message.from_user.username, message.from_user.first_name)
    if not user:
        await state.clear()
        await message.answer("⏳ Il tuo account non è ancora registrato. Chiedi a un admin di inserirti nel pannello.")
        return
    if CEO_USERNAME and user["username"].lower() == CEO_USERNAME:
        db.apply_ceo_username(CEO_USERNAME)
        user = db.get_user(message.from_user.id)
    await message.answer(main_text(user), parse_mode="HTML", reply_markup=main_keyboard(can_manage(message.from_user.id)))


@router.callback_query(F.data == "back_main")
async def back_main(callback: types.CallbackQuery):
    user = db.get_user(callback.from_user.id)
    if not user:
        await callback.answer("Account non registrato", show_alert=True)
        return
    await callback.answer()
    await callback.message.edit_text(main_text(user), parse_mode="HTML", reply_markup=main_keyboard(can_manage(callback.from_user.id)))


@router.callback_query(F.data == "profile")
async def profile(callback: types.CallbackQuery):
    user = db.get_user(callback.from_user.id)
    await callback.answer()
    await callback.message.edit_text(
        f"👤 <b>Il mio profilo</b>\n\nRuolo: {user['ruolo']}\nContratto: {user['contratto']}\nAssunzione: {user['data_assunzione']}\nPeriodo di prova: {user['periodo_prova_gg']} giorni\nMinecraft: <code>{user['nome_mc']}</code>\nPacchi settimana: {user['pacchi_settimana']}\nPacchi totali: {user['pacchi_totali']}\nWarn: {user['warn']}",
        parse_mode="HTML", reply_markup=back_keyboard())


@router.callback_query(F.data == "packages")
async def packages(callback: types.CallbackQuery):
    user = db.get_user(callback.from_user.id)
    await callback.answer()
    await callback.message.edit_text(f"📦 <b>I miei pacchi questa settimana</b>\n\n{user['nome_mc']}: <b>{user['pacchi_settimana']}</b>\nTotale storico: {user['pacchi_totali']}", parse_mode="HTML", reply_markup=back_keyboard())


@router.callback_query(F.data == "weekly")
async def weekly(callback: types.CallbackQuery):
    if not can_manage(callback.from_user.id):
        await callback.answer("Questa sezione è riservata ai Manager di Linea e ai ruoli superiori.", show_alert=True)
        return
    users = db.get_all_users()
    lines = ["📑 <b>Inserimenti settimanali</b>", ""]
    lines += [f"• {user['nome_mc']}: <b>{user['pacchi_settimana']}</b> pacchi" for user in users]
    lines.append(f"\nTotale team: <b>{sum(user['pacchi_settimana'] for user in users)}</b>")
    await callback.answer()
    await callback.message.edit_text("\n".join(lines), parse_mode="HTML", reply_markup=back_keyboard())


@router.callback_query(F.data == "team_packages")
async def team_packages(callback: types.CallbackQuery):
    if not can_manage(callback.from_user.id):
        await callback.answer("Questa sezione è riservata ai Manager di Linea e ai ruoli superiori.", show_alert=True)
        return
    await callback.answer()
    await callback.message.edit_text(db.get_teampacchi_text(), reply_markup=back_keyboard())


@router.callback_query(F.data == "admin_panel")
async def admin_panel(callback: types.CallbackQuery):
    if not can_manage(callback.from_user.id):
        await callback.answer("Solo gli admin possono accedere.", show_alert=True)
        return
    await callback.answer()
    await callback.message.edit_text("🛠 <b>Pannello admin</b>\n\nScegli l'operazione da eseguire.", parse_mode="HTML", reply_markup=admin_keyboard())


@router.callback_query(F.data == "admin_register")
async def admin_register_start(callback: types.CallbackQuery, state: FSMContext):
    if not can_manage(callback.from_user.id):
        await callback.answer("Accesso negato", show_alert=True)
        return
    await callback.answer()
    await state.set_state(AdminRegistrationStates.telegram_username)
    await callback.message.edit_text("➕ <b>Nuovo dipendente</b>\n\nInvia la @username Telegram.", parse_mode="HTML")


@router.message(AdminRegistrationStates.telegram_username)
async def admin_register_username(message: types.Message, state: FSMContext):
    if not can_manage(message.from_user.id):
        return
    username = message.text.strip()
    if not re.fullmatch(r"@?[A-Za-z0-9_]{5,32}", username):
        await message.answer("Username non valido. Invia ad esempio <code>@Nick</code>.", parse_mode="HTML")
        return
    await state.update_data(username=username.lstrip("@"))
    await state.set_state(AdminRegistrationStates.minecraft_name)
    await message.answer("Invia il nick Minecraft.")


@router.message(AdminRegistrationStates.minecraft_name)
async def admin_register_mc(message: types.Message, state: FSMContext):
    await state.update_data(minecraft_name=message.text.strip())
    await state.set_state(AdminRegistrationStates.contract)
    await message.answer("Invia il numero di contratto (solo numeri).")


@router.message(AdminRegistrationStates.contract)
async def admin_register_contract(message: types.Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("Il contratto deve essere un numero.")
        return
    await state.update_data(contract=int(message.text.strip()))
    await state.set_state(AdminRegistrationStates.probation_days)
    await message.answer("Invia i giorni di prova.")


@router.message(AdminRegistrationStates.probation_days)
async def admin_register_days(message: types.Message, state: FSMContext):
    if not message.text.strip().isdigit() or int(message.text.strip()) <= 0:
        await message.answer("Inserisci un numero di giorni maggiore di zero.")
        return
    data = await state.update_data(probation_days=int(message.text.strip()))
    await state.clear()
    db.create_pending_registration(data["username"], data["minecraft_name"], data["contract"], data["probation_days"])
    await message.answer(f"✅ Registrazione salvata per @{data['username']}. Diventerà dipendente quando avvierà il bot con /start.")


@router.callback_query(F.data == "admin_weekly")
async def admin_weekly_start(callback: types.CallbackQuery, state: FSMContext):
    if not can_manage(callback.from_user.id):
        await callback.answer("Accesso negato", show_alert=True)
        return
    await callback.answer()
    await state.set_state(WeeklyEntryStates.entries)
    await callback.message.edit_text("📑 Invia uno o più inserimenti, uno per riga:\n\n<code>Nick - +50</code> aumenta di 50.\n<code>Nick - 120</code> imposta il totale settimanale a 120.", parse_mode="HTML")


@router.callback_query(F.data == "admin_roles")
async def admin_roles(callback: types.CallbackQuery):
    if not can_assign_roles(callback.from_user.id):
        await callback.answer("Il tuo ruolo non può modificare i ruoli.", show_alert=True)
        return
    roles = "\n".join(f"• {role}" for role in ROLES)
    await callback.answer()
    await callback.message.edit_text(
        f"🏷 <b>Gestione ruoli</b>\n\nRuoli disponibili:\n{roles}\n\nUsa il comando:\n<code>/setruolo @username | ruolo</code>",
        parse_mode="HTML", reply_markup=back_keyboard("admin_panel"))


@router.message(WeeklyEntryStates.entries)
async def admin_weekly_save(message: types.Message, state: FSMContext):
    if not can_manage(message.from_user.id):
        return
    entries = []
    for raw_line in message.text.splitlines():
        match = re.fullmatch(r"\s*(.+?)\s*-\s*(\+?\d+)\s*", raw_line)
        if not match:
            await message.answer(f"Formato non valido: <code>{raw_line}</code>", parse_mode="HTML")
            return
        name, raw_value = match.groups()
        entries.append((name, int(raw_value.lstrip("+")), raw_value.startswith("+")))
    results = []
    for name, value, increment in entries:
        user = db.record_weekly_entry(name, value, increment)
        results.append(f"✅ {name}: {user['pacchi_settimana']}" if user else f"❌ Minecraft non trovato: {name}")
    await state.clear()
    await message.answer("\n".join(results))


@router.callback_query(F.data == "request_leave")
async def leave_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(LeaveStates.start_date)
    await callback.message.edit_text("🏖 Invia la data di inizio nel formato <code>gg/mm/aaaa</code>.", parse_mode="HTML")


def valid_date(value: str) -> bool:
    try:
        datetime.strptime(value, "%d/%m/%Y")
        return True
    except ValueError:
        return False


def parse_leave_date(value: str) -> date | None:
    try:
        return datetime.strptime(value, "%d/%m/%Y").date()
    except ValueError:
        return None


@router.message(LeaveStates.start_date)
async def leave_start_date(message: types.Message, state: FSMContext):
    start_date = parse_leave_date(message.text.strip())
    if start_date is None:
        await message.answer("Data non valida. Usa il formato gg/mm/aaaa.")
        return
    if start_date < date.today():
        await message.answer("La data di inizio non può essere passata.")
        return
    await state.update_data(start_date=message.text.strip())
    await state.set_state(LeaveStates.end_date)
    await message.answer("Invia la data di fine nel formato <code>gg/mm/aaaa</code>.", parse_mode="HTML")


@router.message(LeaveStates.end_date)
async def leave_end_date(message: types.Message, state: FSMContext):
    data = await state.get_data()
    end_date = parse_leave_date(message.text.strip())
    start_date = parse_leave_date(data["start_date"])
    if end_date is None:
        await message.answer("Data non valida. Usa il formato gg/mm/aaaa.")
        return
    if end_date < date.today():
        await message.answer("La data di fine non può essere passata.")
        return
    if start_date is None or end_date < start_date:
        await message.answer("La data di fine non può precedere la data di inizio.")
        return
    await state.update_data(end_date=message.text.strip())
    await state.set_state(LeaveStates.reason)
    await message.answer("Scrivi il motivo del congedo.")


@router.message(LeaveStates.reason)
async def leave_reason(message: types.Message, state: FSMContext):
    data = await state.get_data()
    leave_id = db.create_congedo(message.from_user.id, data["start_date"], data["end_date"], message.text.strip())
    await state.clear()
    await message.answer("✅ Richiesta inviata alla Direzione.")
    buttons = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Accetta", callback_data=f"leave_accept_{leave_id}"), InlineKeyboardButton(text="❌ Rifiuta", callback_data=f"leave_reject_{leave_id}")]])
    await message.bot.send_message(ADMIN_GROUP_ID, f"🏖 Nuova richiesta #{leave_id}\nDa: {message.from_user.first_name}\nPeriodo: {data['start_date']} - {data['end_date']}\nMotivo: {message.text}", reply_markup=buttons)


@router.callback_query(F.data == "my_leaves")
async def my_leaves(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.edit_text("🏖 <b>Le mie richieste</b>\n\nScegli una vista.", parse_mode="HTML", reply_markup=leave_keyboard())


@router.callback_query(F.data.in_({"leaves_active", "leaves_past"}))
async def list_leaves(callback: types.CallbackQuery):
    active = callback.data == "leaves_active"
    leaves = db.get_user_leaves(callback.from_user.id, active)
    title = "🟢 Congedi attivi" if active else "📚 Congedi passati"
    lines = [f"<b>{title}</b>", ""]
    lines += [f"• {leave['data_inizio']} - {leave['data_fine']} | {leave['stato']}\n  {leave['motivo']}" for leave in leaves] or ["Nessun congedo da mostrare."]
    await callback.answer()
    await callback.message.edit_text("\n".join(lines), parse_mode="HTML", reply_markup=leave_keyboard())


@router.callback_query(F.data.startswith("leave_"))
async def manage_leave(callback: types.CallbackQuery):
    if not can_manage(callback.from_user.id):
        await callback.answer("Solo gli admin possono gestire i congedi.", show_alert=True)
        return
    action, leave_id = callback.data.split("_")[1:]
    leave = db.get_congedo(int(leave_id))
    if not leave or leave["stato"] != "IN_ATTESA":
        await callback.answer("Richiesta già gestita.", show_alert=True)
        return
    status = "ACCETTATO" if action == "accept" else "RIFIUTATO"
    db.update_congedo_stato(int(leave_id), status)
    await callback.answer("Aggiornato")
    await callback.message.edit_text(f"{callback.message.text}\n\nEsito: <b>{status}</b>", parse_mode="HTML")
    await callback.bot.send_message(leave["telegram_id"], f"🏖 La richiesta di congedo #{leave_id} è stata {status.lower()}.")


@router.callback_query(F.data == "admin_leaves")
async def admin_leaves(callback: types.CallbackQuery):
    if not can_manage(callback.from_user.id):
        await callback.answer("Accesso negato", show_alert=True)
        return
    pending = db.get_pending_leaves()
    lines = ["🏖 <b>Congedi in attesa</b>", ""]
    lines += [f"#{leave['id']} {leave['nome_mc']}: {leave['data_inizio']} - {leave['data_fine']}\n{leave['motivo']}" for leave in pending] or ["Nessuna richiesta in attesa."]
    await callback.answer()
    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Attivi del team", callback_data="team_leaves_active"), InlineKeyboardButton(text="📚 Passati del team", callback_data="team_leaves_past")],
        [InlineKeyboardButton(text="« Indietro", callback_data="admin_panel")],
    ])
    await callback.message.edit_text("\n".join(lines), parse_mode="HTML", reply_markup=buttons)


@router.callback_query(F.data.in_({"team_leaves_active", "team_leaves_past"}))
async def team_leaves(callback: types.CallbackQuery):
    if not can_manage(callback.from_user.id):
        await callback.answer("Accesso negato", show_alert=True)
        return
    active = callback.data == "team_leaves_active"
    leaves = db.get_all_leaves(active)
    title = "🟢 Congedi attivi del team" if active else "📚 Congedi passati del team"
    lines = [f"<b>{title}</b>", ""]
    lines += [f"• {name}: {leave['data_inizio']} - {leave['data_fine']} | {leave['stato']}\n  {leave['motivo']}" for leave, name in leaves] or ["Nessun congedo da mostrare."]
    await callback.answer()
    await callback.message.edit_text("\n".join(lines), parse_mode="HTML", reply_markup=back_keyboard("admin_leaves"))


@router.callback_query(F.data.in_({"supplies", "my_supplies", "guide", "report"}))
async def not_implemented(callback: types.CallbackQuery):
    await callback.answer("Sezione in preparazione", show_alert=True)


@router.message(Command("setruolo"))
async def set_role_command(message: types.Message, command: CommandObject):
    if not can_assign_roles(message.from_user.id):
        await message.answer("Solo i ruoli esecutivi possono modificare i ruoli.")
        return
    parts = command.args.split(" ", 1) if command.args else []
    if len(parts) != 2:
        await message.answer("Usa /setruolo @username | ruolo")
        return
    target = db.get_user_by_username(parts[0])
    role = next((item for item in ROLES if item.lower() == parts[1].strip().lower()), None)
    actor_level = ROLE_LEVELS[user_role(message.from_user.id)]
    if not target or not role:
        await message.answer("Utente o ruolo non valido. Usa il pannello admin per vedere i ruoli disponibili.")
        return
    if ROLE_LEVELS[role] >= actor_level and target["telegram_id"] != message.from_user.id:
        await message.answer("Non puoi assegnare a un altro utente un ruolo pari o superiore al tuo.")
        return
    db.set_role(target["telegram_id"], role)
    await message.answer(f"✅ @{target['username']} ora ha il ruolo: {role}.")


@router.message(Command("warn", "unwarn", "setprova", "setteampacchi"))
async def admin_commands(message: types.Message, command: CommandObject):
    if not can_manage(message.from_user.id):
        await message.answer("Solo gli admin possono usare questo comando.")
        return
    if command.command == "setteampacchi":
        if not command.args:
            await message.answer("Usa /setteampacchi seguito dal testo.")
        else:
            db.set_teampacchi_text(command.args)
            await message.answer("✅ Testo aggiornato.")
        return
    args = command.args.split() if command.args else []
    target = db.get_user_by_username(args[0]) if args else None
    if not target:
        await message.answer("Indica un username Telegram, ad esempio /warn @nome.")
        return
    if command.command == "warn":
        db.update_warn(target["telegram_id"], 1)
    elif command.command == "unwarn":
        db.update_warn(target["telegram_id"], -1)
    else:
        if len(args) != 2 or not args[1].isdigit():
            await message.answer("Usa /setprova @nome 30.")
            return
        db.set_periodo_prova(target["telegram_id"], int(args[1]))
    await message.answer("✅ Operazione completata.")
