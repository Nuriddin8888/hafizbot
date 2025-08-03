from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton



admin_panel = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Sura qo‘shish",callback_data="add_sura"),
        ],
        [
            InlineKeyboardButton(text="👥 Foydalanuvchilarni ko‘rish",callback_data="show_users"),
        ],
        [
            InlineKeyboardButton("📢 Reklama yuborish", callback_data="advertise")
        ]
    ]
)


confirm_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton("✅ Ha", callback_data="send_ad"),
        ],
        [
            InlineKeyboardButton("❌ Yo‘q", callback_data="cancel_ad")
        ]
    ]
)



MAX_SURAS_PER_PAGE = 5

def get_sura_pagination_keyboard(sura_names, current_page, total_pages):
    keyboard = InlineKeyboardMarkup(row_width=1)

    for name in sura_names:
        keyboard.add(InlineKeyboardButton(text=name, callback_data=f"sura:{name}"))

    nav_buttons = []
    if current_page > 1:
        nav_buttons.append(InlineKeyboardButton("◀️", callback_data=f"page:{current_page - 1}"))
    nav_buttons.append(InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="ignore"))
    if current_page < total_pages:
        nav_buttons.append(InlineKeyboardButton("▶️", callback_data=f"page:{current_page + 1}"))

    keyboard.row(*nav_buttons)
    return keyboard



def get_sura_page_buttons(sura_name, current_page, total_pages):
    keyboard = InlineKeyboardMarkup()
    buttons = []
    if current_page > 1:
        buttons.append(InlineKeyboardButton("◀️", callback_data=f"matn:{sura_name}:{current_page - 1}"))
    buttons.append(InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="ignore"))
    if current_page < total_pages:
        buttons.append(InlineKeyboardButton("▶️", callback_data=f"matn:{sura_name}:{current_page + 1}"))
    keyboard.row(*buttons)
    return keyboard


def get_users_page_keyboard(current_page, total_pages):
    buttons = []

    if current_page > 1:
        buttons.append(InlineKeyboardButton("◀️", callback_data=f"admin_users:{current_page - 1}"))

    buttons.append(InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="ignore"))

    if current_page < total_pages:
        buttons.append(InlineKeyboardButton("▶️", callback_data=f"admin_users:{current_page + 1}"))

    return InlineKeyboardMarkup().row(*buttons)
