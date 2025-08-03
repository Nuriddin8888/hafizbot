from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.exceptions import BotBlocked, ChatNotFound
import logging


from config import BOT_TOKEN, ADMIN_IDS
from database import add_sura, setup_database, add_user, get_all_sura_names, get_sura_by_name, get_all_users, update_user_status
from buttons.inline import admin_panel, get_sura_pagination_keyboard, get_sura_page_buttons, get_users_page_keyboard, confirm_kb
from state import AdminStates, FeedbackState


bot = Bot(token=BOT_TOKEN, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

logging.basicConfig(level=logging.INFO)


@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    full_name = message.from_user.full_name
    username = message.from_user.username

    add_user(user_id, full_name, username)

    welcome_text = f"""🌟 Assalomu alaykum, <b><a href='tg://user?id={user_id}'>{full_name}</a></b>\n
🤖 Men Qur'on suralarini yodlashda sizga yordam beruvchi botman.

📖 “Bismillahir Rohmanir Rohiym” bilan boshlaymizmi?

👇 Quyidagi menyudan suralarni tanlang"""


    await message.answer(welcome_text)
    await send_sura_page(message.chat.id, page=1)




@dp.message_handler(commands=['admin'])
async def admin_handler(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    full_name = message.from_user.full_name
    text = f"🤖 Assalomu alaykum, hurmatli admin {full_name}!\n\nQuyidagi menyudan kerakli bo‘limni tanlang:"
    
    await message.answer(text, reply_markup=admin_panel)



@dp.callback_query_handler(lambda c: c.data.startswith("show_users") or c.data.startswith("admin_users:"))
async def handle_user_pagination(callback_query: types.CallbackQuery):
    if callback_query.data == "show_users":
        page = 1
    else:
        page = int(callback_query.data.split(":")[1])

    users = get_all_users()

    if not users:
        await callback_query.message.answer("👤 Foydalanuvchilar topilmadi.")
        return

    total_pages = (len(users) + MAX_SURAS_PER_PAGE - 1) // MAX_SURAS_PER_PAGE
    start = (page - 1) * MAX_SURAS_PER_PAGE
    end = start + MAX_SURAS_PER_PAGE
    current_users = users[start:end]

    text = f"👥 <b>Foydalanuvchilar ro'yxati</b>\n<b>Umumiy soni:</b> {len(users)}\n\n"

    for user in current_users:
        user_id, full_name, username, status = user
        status_emoji = "✅" if status else "❌"
        text += (
            f"🆔: <code>{user_id}</code>\n"
            f"👤: {full_name}\n"
            f"🔗: @{username if username else 'Nomaʼlum'}\n"
            f"📶: {status_emoji} {'Faol' if status else 'Bloklangan'}\n\n"
        )

    keyboard = get_users_page_keyboard(page, total_pages)

    if callback_query.data == "show_users":
        await callback_query.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

    await callback_query.answer()



@dp.callback_query_handler(lambda c: c.data == "advertise")
async def start_advertising(callback_query: types.CallbackQuery):
    await callback_query.message.answer("📨 Reklama uchun rasm/video va caption yuboring:")
    await AdminStates.waiting_for_ad.set()
    await callback_query.answer()



@dp.message_handler(content_types=["photo", "video"], state=AdminStates.waiting_for_ad, user_id=ADMIN_IDS)
async def get_advertising_media(message: types.Message, state: FSMContext):
    data = {
        "file_id": message.photo[-1].file_id if message.photo else message.video.file_id,
        "caption": message.caption,
        "type": "photo" if message.photo else "video"
    }
    await state.update_data(advert=data)

    if data["type"] == "photo":
        await message.answer_photo(data["file_id"], caption=data["caption"], reply_markup=confirm_kb)
    else:
        await message.answer_video(data["file_id"], caption=data["caption"], reply_markup=confirm_kb)

    await AdminStates.confirm_send.set()



@dp.callback_query_handler(lambda c: c.data == "send_ad", state=AdminStates.confirm_send)
async def confirm_send_ad(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("📤 Reklama yuborilmoqda...")
    await callback_query.answer()

    data = await state.get_data()
    advert = data.get("advert")
    users = get_all_users() 

    sent, failed = 0, 0
    for user in users:
        user_id = user[0]
        try:
            if advert["type"] == "photo":
                await bot.send_photo(user_id, advert["file_id"], caption=advert["caption"])
            else:
                await bot.send_video(user_id, advert["file_id"], caption=advert["caption"])
            update_user_status(user_id, True)
            sent += 1
        except (BotBlocked, ChatNotFound):
            update_user_status(user_id, False)
            failed += 1

    await callback_query.message.answer(f"✅ Yuborildi: {sent} ta\n❌ Bloklaganlar: {failed} ta")
    await state.finish()



@dp.callback_query_handler(lambda c: c.data == "cancel_ad", state=AdminStates.confirm_send)
async def cancel_ad(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("❌ Reklama yuborish bekor qilindi.")
    await callback_query.answer()
    await state.finish()





@dp.callback_query_handler(lambda c: c.data == "add_sura")
async def process_add_sura(callback_query: types.CallbackQuery):
    await callback_query.answer()
    await callback_query.message.answer("📥 Iltimos, suraning nomini yozing:")
    await AdminStates.waiting_for_sura_name.set()


@dp.message_handler(state=AdminStates.waiting_for_sura_name)
async def get_sura_name(message: types.Message, state: FSMContext):
    await state.update_data(sura_name=message.text)
    await message.answer("🎵 Endi suraning audio faylini (mp3) yuboring:")
    await AdminStates.waiting_for_audio.set()


@dp.message_handler(content_types=types.ContentType.AUDIO, state=AdminStates.waiting_for_audio)
async def process_audio(message: types.Message, state: FSMContext):
    await state.update_data(audio_file_id=message.audio.file_id, image_file_ids=[])
    await message.answer("🖼 Endi suraning matnini rasm ko'rinishida yuboring (1 yoki bir nechta rasm). Yuborib bo‘lgach '✅ Tugatdim' deb yozing.")
    await AdminStates.waiting_for_text_images.set()



@dp.message_handler(content_types=types.ContentType.PHOTO, state=AdminStates.waiting_for_text_images)
async def get_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    image_file_ids = data.get("image_file_ids", [])
    image_file_ids.append(message.photo[-1].file_id)
    await state.update_data(image_file_ids=image_file_ids)
    await message.reply("✅ Rasm qabul qilindi. Yana rasm yuboring yoki '✅ Tugatdim' deb yozing.")


@dp.message_handler(lambda m: m.text.lower().startswith("✅"), state=AdminStates.waiting_for_text_images)
async def finish_sura(message: types.Message, state: FSMContext):
    data = await state.get_data()
    name = data.get("sura_name")
    audio_file_id = data.get("audio_file_id")
    image_file_ids = data.get("image_file_ids", [])

    if not image_file_ids:
        return await message.answer("⚠️ Kamida 1 ta rasm yuborishingiz kerak.")

    add_sura(name=name, audio_file_id=audio_file_id, image_file_ids=image_file_ids)

    await message.answer(f"✅ <b>{name}</b> surasi muvaffaqiyatli saqlandi!", parse_mode="HTML")
    await state.finish()




MAX_SURAS_PER_PAGE = 5



@dp.message_handler(commands=['suralar'])
async def show_sura_list(message: types.Message):
    await send_sura_page(message.chat.id, page=1)


async def send_sura_page(chat_id, page):
    suralar = get_all_sura_names()
    total_pages = (len(suralar) + MAX_SURAS_PER_PAGE - 1) // MAX_SURAS_PER_PAGE

    if page < 1 or page > total_pages:
        return

    start = (page - 1) * MAX_SURAS_PER_PAGE
    end = start + MAX_SURAS_PER_PAGE
    current_suras = suralar[start:end]

    keyboard = get_sura_pagination_keyboard(current_suras, page, total_pages)
    await bot.send_message(chat_id, "Quyidagi suralardan birini tanlang:", reply_markup=keyboard)



async def send_sura(callback_query: types.CallbackQuery):
    sura_name = callback_query.data.split(":")[1]
    audio_id, image_ids = get_sura_by_name(sura_name)

    if not audio_id:
        await callback_query.answer("Surani topib bo'lmadi.", show_alert=True)
        return

    await callback_query.message.answer_audio(audio=audio_id, caption=f"<b>{sura_name}</b> surasi", parse_mode="HTML")

    if image_ids:
        caption = f"📖 <b>{sura_name}</b> surasi matni\n1 / {len(image_ids)} bet"
        keyboard = get_sura_page_buttons(sura_name, 1, len(image_ids))
        await callback_query.message.answer_photo(photo=image_ids[0], caption=caption, parse_mode="HTML", reply_markup=keyboard)

    await callback_query.answer()




@dp.callback_query_handler(lambda c: c.data.startswith("sura:"))
async def send_sura(callback_query: types.CallbackQuery):
    sura_name = callback_query.data.split(":")[1]
    audio_id, image_ids = get_sura_by_name(sura_name)

    if not audio_id:
        await callback_query.answer("Surani topib bo'lmadi.", show_alert=True)
        return

    await callback_query.message.answer_audio(audio=audio_id, caption=f"<b>{sura_name}</b> surasi", parse_mode="HTML")

    if image_ids:
        caption = f"📖 <b>{sura_name}</b> surasi matni\n1 / {len(image_ids)} bet"
        keyboard = get_sura_page_buttons(sura_name, 1, len(image_ids))
        await callback_query.message.answer_photo(photo=image_ids[0], caption=caption, parse_mode="HTML", reply_markup=keyboard)

    await callback_query.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("matn:"))
async def paginate_sura_text(callback_query: types.CallbackQuery):
    _, sura_name, page = callback_query.data.split(":")
    page = int(page)

    _, image_ids = get_sura_by_name(sura_name)
    total_pages = len(image_ids)

    if page < 1 or page > total_pages:
        await callback_query.answer("Bunday bet yo‘q.")
        return

    caption = f"📖 <b>{sura_name}</b> surasi matni\n{page} / {total_pages} bet"
    keyboard = get_sura_page_buttons(sura_name, page, total_pages)

    await callback_query.message.edit_media(
        media=types.InputMediaPhoto(media=image_ids[page - 1], caption=caption, parse_mode="HTML"),
        reply_markup=keyboard
    )
    await callback_query.answer()


@dp.callback_query_handler(lambda c: c.data == "ignore")
async def ignore_callback(callback_query: types.CallbackQuery):
    await callback_query.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("page:"))
async def change_sura_page(callback_query: types.CallbackQuery):
    page = int(callback_query.data.split(":")[1])
    suralar = get_all_sura_names()
    total_pages = (len(suralar) + MAX_SURAS_PER_PAGE - 1) // MAX_SURAS_PER_PAGE

    start = (page - 1) * MAX_SURAS_PER_PAGE
    end = start + MAX_SURAS_PER_PAGE
    current_suras = suralar[start:end]

    keyboard = get_sura_pagination_keyboard(current_suras, page, total_pages)

    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text="Quyidagi suralardan birini tanlang:",
        reply_markup=keyboard
    )
    await callback_query.answer()



@dp.message_handler(commands=['help'])
async def help_handler(message: types.Message):
    text = (
        "🤖 *HafizBot* ga xush kelibsiz!\n\n"
        "📝 Bu bot orqali siz quyidagi imkoniyatlarga ega bo‘lasiz:\n"
        "✅ Admin tomonidan yuborilgan reklama va e’lonlarni olish.\n"
        "✅ O‘z fikr va takliflaringizni adminlarga yuborish.\n\n"
        "ℹ️ Botdan foydalanish juda oddiy:\n"
        "1️⃣ /start - botni ishga tushirish\n"
        "1️⃣ /suralar - barcha suralar ro'yxatini olish\n"
        "2️⃣ /help - yordam olish\n"
        "3️⃣ /feedback - taklif yoki muammo yuborish\n\n"
        "🎉 HafizBot sizga qulay va tezkor xizmat ko‘rsatishga tayyor!\n\n"
        "🙏 Doimo biz bilan bo‘ling va fikrlaringizni ulashing!"
    )

    await message.answer(text, parse_mode="Markdown")



@dp.message_handler(commands=['feedback'])
async def feedback_command(message: types.Message):
    await message.answer(
        "📝 *Yangi fikr!*\n\n"
        "Botimizdan foydalanishda qandaydir noqulaylik yoki takliflaringiz bo‘lsa, iltimos yozing.\n"
        "Sizning fikringiz biz uchun juda muhim! 💎",
        parse_mode="Markdown"
    )
    await FeedbackState.waiting_for_feedback.set()

@dp.message_handler(state=FeedbackState.waiting_for_feedback, content_types=types.ContentTypes.TEXT)
async def process_feedback(message: types.Message, state: FSMContext):
    user = message.from_user
    feedback_text = message.text

    feedback_message = (
        f"📝 *Yangi fikr!*\n\n"
        f"👤 Foydalanuvchi: {user.full_name} (@{user.username or 'username yo‘q'})\n"
        f"🆔 ID: {user.id}\n"
        f"💬 Xabar: {feedback_text}"
    )

    for admin_id in ADMIN_IDS:
        await bot.send_message(admin_id, feedback_message)

    await message.answer("✅ Fikringiz uchun rahmat! Tez orada jamoamiz javob beradi 🙏")
    await state.finish()





async def on_start_up(dp):
    for admin_id in ADMIN_IDS:
        await bot.send_message(chat_id=admin_id, text='Bot ishga tushdi!')

async def on_shutdown(dp):
    for admin_id in ADMIN_IDS:
        await bot.send_message(chat_id=admin_id, text='Bot o\'chdi!')



if __name__ == '__main__':
    setup_database()
    executor.start_polling(dp, skip_updates=True, on_startup=on_start_up, on_shutdown=on_shutdown)
