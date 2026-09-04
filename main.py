import asyncio
from concurrent.futures import process
import logging
from os import name
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import database as db

BOT_TOKEN = "8774182658:AAEPy5Ai7ImZvncRSpjwxbOtk9Xh3L1pMIs"
ADMIN_GROUP_ID = -1004354827440

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- FSM States ---
class FormRegistrazione(StatesGroup):
    in_attesa_nome_mc = State()

class FormCongedo(StatesGroup):
    data_inizio = State()
    data_fine = State()
    motivo = State()

class FormSegnalazione(StatesGroup):
    motivo = State()

# --- Tastiere ---
def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👤 Il mio profilo", callback_data="profilo"),
            InlineKeyboardButton(text="📦 I miei pacchi", callback_data="pacchi")
        ],
        [
            InlineKeyboardButton(text="📦 Pacchi del team", callback_data="team_pacchi"),
            InlineKeyboardButton(text="📑 Inserimenti settimanali", callback_data="inserimenti")
        ],
        [
            InlineKeyboardButton(text="🏖 Richiedi congedo", callback_data="richiedi_congedo"),
            InlineKeyboardButton(text="📜 Le mie richieste", callback_data="mie_richieste")
        ],
        [
            InlineKeyboardButton(text="🧰 Richiedi rifornimento", callback_data="rifornimento"),
            InlineKeyboardButton(text="📦 I miei rifornimenti", callback_data="miei_rifornimenti")
        ],
        [InlineKeyboardButton(text="🚩 Segnala un collega", callback_data="segnala_collega")],
        [InlineKeyboardButton(text="❓ Guida", callback_data="guida")]
    ])

def get_back_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="« Indietro", callback_data="back_main")]
    ])

# --- Annullamento FSM ---
@dp.message(Command("annulla"))
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.clear()
    await message.reply("❌ Operazione annullata.", reply_markup=types.ReplyKeyboardRemove())

# --- /menu Command ---
@dp.message(Command("menu", "start"))
async def cmd_menu(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user = db.get_user(user_id)
    if not user:
        await state.set_state(FormRegistrazione.in_attesa_nome_mc)
        try:
            await bot.send_message(user_id, "👋 Prima Registrazione**\n\nNome in game?")
            if message.chat.type != "private":
                await message.reply("📩 Ti ho inviato un messaggio in privato per completare la registrazione!")
        except Exception:
            await message.reply("⚠️ Per favore avvia prima il bot in privato (t.me/NomeBot) e rifai `/menu`.")
        return

    testo = (
        "═════════════════════════\n"
        "👤 **La tua scheda**\n\n"
        f"🪪 Utente: @{user[1]}\n"
        f"🏷 Ruolo: {user[3]}\n"
        f"📦 Pacchi totali inseriti: {user[7]}\n"
        "═════════════════════════\n\n"
        "👋 **Bentornato!**\n"
        "_Seleziona un'opzione dal menu._"
    )

    try:
        await bot.send_message(user_id, testo, parse_mode="Markdown", reply_markup=get_main_keyboard())
        if message.chat.type != "private":
            await message.reply("📩 Ti ho inviato il menu in privato!")
    except Exception:
        await message.reply("⚠️ Apri la chat privata con il bot per ricevere il menu.")

# --- Registrazione Nome MC ---
@dp.message(FormRegistrazione.in_attesa_nome_mc)
async def process_nome_mc(message: types.Message, state: FSMContext):
    nome_mc = message.text.strip()
    username = message.from_user.username or message.from_user.first_name
    db.register_user(message.from_user.id, username, message.from_user.first_name, nome_mc)
    await state.clear()
    await message.reply(f"✅ Registrazione completata! Nome Minecraft: `{nome_mc}`.\nUsa di nuovo `/menu`.")

# --- Callbacks Menu ---
@dp.callback_query(F.data == "profilo")
async def cb_profilo(callback: types.CallbackQuery):
    user = db.get_user(callback.from_user.id)
    testo = (
        "👤 **Il mio profilo**\n\n"
        f"Ruolo: {user[3]}\n"
        f"Contratto: `{user[4]}`\n"
        f"Data assunzione: {user[5]}\n"
        f"Periodo di prova: {user[6]} gg**\n"
        f"Nome Minecraft: `{user[7]}`\n"
        f"Pacchi totali inseriti: {user[8]}**\n"
        f"Warn: {user[11]}"
    )
    await callback.message.edit_text(testo, parse_mode="Markdown", reply_markup=get_back_keyboard())

@dp.callback_query(F.data == "pacchi")
async def cb_pacchi(callback: types.CallbackQuery):
    user = db.get_user(callback.from_user.id)
    testo = (
        f"📦 **I miei pacchi · settimana corrente**\n\n"
        f"I tuoi pacchi: {user[9]}\n"
        f"Le tue ore: ⏱️ {user[10]}\n"
        f"Media aziendale (non-admin): **19.9**\n"
        f"Rispetto alla media: 🔴 <40%\n"
        f"Totale team: **875"
    )
    await callback.message.edit_text(testo, parse_mode="Markdown", reply_markup=get_back_keyboard())

@dp.callback_query(F.data == "team_pacchi")
async def cb_team_pacchi(callback: types.CallbackQuery):
    testo = db.get_teampacchi_text()
    await callback.message.edit_text(testo, parse_mode="Markdown", reply_markup=get_back_keyboard())

@dp.callback_query(F.data == "back_main")
async def cb_back_main(callback: types.CallbackQuery):
    user = db.get_user(callback.from_user.id)
    testo = (
        "═════════════════════════\n"
        "👤 La tua scheda**\n\n"
        f"🪪 Utente: @{user[1]}\n"
        f"🏷 Ruolo: {user[3]}\n"
        f"📦 Pacchi totali inseriti: {user[7]}\n"
        "═════════════════════════\n\n"
        "👋 **Bentornato!**\n"
        "_Seleziona un'opzione dal menu._"
    )
    await callback.message.edit_text(testo, parse_mode="Markdown", reply_markup=get_main_keyboard())

# --- Flusso Congedo ---
@dp.callback_query(F.data == "richiedi_congedo")
async def cb_richiedi_congedo(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(FormCongedo.data_inizio)
    await callback.message.edit_text(
        "🏖 **Nuova richiesta di congedo · passo 1/3**\n\n"
        "Invia la **data di inizio in formato gg/mm/aaaa.\n"
        "_Digita /annulla per uscire._",
        parse_mode="Markdown"
    )

@dp.message(FormCongedo.data_inizio)
async def process_congedo_inizio(message: types.Message, state: FSMContext):
    await state.update_data(data_inizio=message.text.strip())
    await state.set_state(FormCongedo.data_fine)
    await message.reply(
        "🏖 Nuova richiesta di congedo · passo 2/3**\n\n"
        "Invia la **data di fine in formato gg/mm/aaaa.\n"
        "_Digita /annulla per uscire._",
        parse_mode="Markdown"
    )

@dp.message(FormCongedo.data_fine)
async def process_congedo_fine(message: types.Message, state: FSMContext):
    await state.update_data(data_fine=message.text.strip())
    await state.set_state(FormCongedo.motivo)
    await message.reply(
        "🏖 Nuova richiesta di congedo · passo 3/3**\n\n"
        "Invia la richiesta di congedo, spiegandone il **motivo.\n"
        "_Digita /annulla per uscire._",
        parse_mode="Markdown"
    )

@dp.message(FormCongedo.motivo)
async def process_congedo_motivo(message: types.Message, state: FSMContext):
    motivo = message.text.strip()
    data = await state.get_data()
    await state.clear()

    congedo_id = db.create_congedo(message.from_user.id, data['data_inizio'], data['data_fine'], motivo)
    await message.reply("✅ Richiesta di congedo inviata alla Direzione con successo!")

    # Invio al gruppo Admin
    kb_admin = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Accetta", callback_data=f"congedo_acc_{congedo_id}"),
        InlineKeyboardButton(text="❌ Rifiuta", callback_data=f"congedo_rif_{congedo_id}")
    ]])

    user_info = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
    testo_admin = (
        f"🏖 Nuova richiesta di congedo #{congedo_id}**\n"
        f"Da: ☢️ {message.from_user.first_name} ☢️ ({user_info})\n"
        f"Periodo: {data['data_inizio']} ➔ {data['data_fine']}\n"
        f"Motivo: _{motivo}_"
    )
    await bot.send_message(ADMIN_GROUP_ID, testo_admin, parse_mode="Markdown", reply_markup=kb_admin)

@dp.callback_query(F.data.startswith("congedo_"))
async def cb_gestione_congedo(callback: types.CallbackQuery):
    action, congedo_id = callback.data.split("_")[1], int(callback.data.split("_")[2])
    congedo = db.get_congedo(congedo_id)
    if not congedo:
        return

    stato = "accettata ✅" if action == "acc" else "rifiutata ❌"
    db.update_congedo_stato(congedo_id, "ACCETTATO" if action == "acc" else "RIFIUTATO")

    await callback.message.edit_text(f"{callback.message.text}\n\nEsito: {stato.upper()}", parse_mode="Markdown")

    # Notifica Utente
    testo_notifica = (
        f"🏖 La tua richiesta di congedo #{congedo_id} ({congedo[2]} ➔ {congedo[3]}) è stata {stato}."
    )
    try:
        await bot.send_message(congedo[1], testo_notifica)
    except Exception:
        pass

# --- Flusso Segnalazione ---
@dp.callback_query(F.data == "segnala_collega")
async def cb_segnala_collega(callback: types.CallbackQuery):
    users = db.get_all_users()
    buttons = []
    for u in users:
        if u[0] != callback.from_user.id:
            buttons.append([InlineKeyboardButton(text=f"🚩 {u[1]} · {u[3]}", callback_data=f"target_segnala_{u[0]}")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(
        "🚩 **Segnala un collega**\n\nSeleziona il collega che vuoi segnalare. La segnalazione sarà inviata in privato alla Direzione.",
        parse_mode="Markdown",
        reply_markup=kb
    )

@dp.callback_query(F.data.startswith("target_segnala_"))
async def cb_select_target(callback: types.CallbackQuery, state: FSMContext):
    target_id = int(callback.data.split("_")[2])
    target_user = db.get_user(target_id)
    await state.update_data(target_id=target_id)
    await state.set_state(FormSegnalazione.motivo)

    await callback.message.edit_text(
        f"🚩 **Segnalazione**\n\n"
        f"Collega selezionato: {target_user[7]}\n\n"
        f"Scrivi ora il **motivo della segnalazione (max 800 caratteri).\n"
        f"_Digita /annulla per uscire._",
        parse_mode="Markdown"
    )

@dp.message(FormSegnalazione.motivo)
async def process_segnalazione_motivo(message: types.Message, state: FSMContext):
    motivo = message.text.strip()[:800]
    data = await state.get_data()
    target_user = db.get_user(data['target_id'])
    await state.clear()

    await message.reply("✅ Segnalazione inviata alla Direzione.")

    # Invio al gruppo Admin
    reporter_info = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
    target_info = f"@{target_user[1]}" if target_user[1] else target_user[2]

    testo_report = (
        "═════════════════════════\n"
        "🚩 NUOVA SEGNALAZIONE**\n\n"
        f"👤 Segnalato: {target_user[7]} ({target_info})\n"
        f"👰 Da: {message.from_user.first_name} ({reporter_info})\n\n"
        f"📝 Motivo:\n_{motivo}_\n"
        "═════════════════════════"
    )
    await bot.send_message(ADMIN_GROUP_ID, testo_report, parse_mode="Markdown")

# --- Comandi Admin ---
@dp.message(Command("warn"))
async def cmd_warn(message: types.Message, command: CommandObject):
    target_user = None
    if message.reply_to_message:
        target_user = db.get_user(message.reply_to_message.from_user.id)
    elif command.args:
        target_user = db.get_user_by_username(command.args)

    if not target_user:
        await message.reply("⚠️ Usa il comando in risposta a un messaggio o specificando l'username (es. `/warn @nome`).")
        return

    db.update_warn(target_user[0], 1)
    await message.reply(f"⚠️ Warn aggiunto a @{target_user[1]}! Warn totali: {target_user[11] + 1}")

@dp.message(Command("unwarn"))
async def cmd_unwarn(message: types.Message, command: CommandObject):
    target_user = None
    if message.reply_to_message:
        target_user = db.get_user(message.reply_to_message.from_user.id)
    elif command.args:
        target_user = db.get_user_by_username(command.args)

    if not target_user:
        await message.reply("⚠️ Usa il comando in risposta a un messaggio o specificando l'username (es. `/unwarn @nome`).")
        return

    db.update_warn(target_user[0], -1)
    await message.reply(f"✅ Warn rimosso a @{target_user[1]}!")

@dp.message(Command("setprova"))
async def cmd_setprova(message: types.Message, command: CommandObject):
    if not command.args or not message.reply_to_message:
        await message.reply("⚠️ Rispondi all'utente indicando i giorni di prova (es: `/setprova 30`).")
        return

    giorni = int(command.args) if command.args.isdigit() else 14
    target_user = db.get_user(message.reply_to_message.from_user.id)
    db.set_periodo_prova(target_user[0], giorni)
    await message.reply(f"📅 Periodo di prova di @{target_user[1]} aggiornato a {giorni} giorni**.")

@dp.message(Command("setteampacchi"))
async def cmd_setteampacchi(message: types.Message, command: CommandObject):
    if not command.args:
        await message.reply("⚠️ Inserisci il testo del messaggio pacchi team. Es: /setteampacchi testo....")
        return
    db.set_teampacchi_text(command.args)
    await message.reply("✅ Messaggio 'Pacchi del team' aggiornato con successo.")

async def main():
    db.init_db()
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())