from aiogram.dispatcher.filters.state import State, StatesGroup

class AdminStates(StatesGroup):
    waiting_for_sura_name = State()
    waiting_for_audio = State()
    waiting_for_text_images = State()
    waiting_for_ad = State()
    confirm_send = State()


class FeedbackState(StatesGroup):
    waiting_for_feedback = State()
