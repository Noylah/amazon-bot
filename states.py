from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    minecraft_name = State()


class LeaveStates(StatesGroup):
    start_date = State()
    end_date = State()
    reason = State()


class ReportStates(StatesGroup):
    reason = State()


class AdminRegistrationStates(StatesGroup):
    telegram_username = State()
    minecraft_name = State()
    contract = State()
    probation_days = State()


class WeeklyEntryStates(StatesGroup):
    entries = State()
