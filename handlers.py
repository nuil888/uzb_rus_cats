import logging
import re
from aiogram import Bot, F, Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.filters.command import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from config import (
    ADMIN_IDS,
    ADMIN_PASSWORD,
    CAT_CHANNEL_ID,
    CITIES_RU,
    CITIES_UZ,
    CITY_MAP_RU_TO_UZ,
    CITY_MAP_UZ_TO_RU,
    TEXTS,
    USERS_CHANNEL_ID,
)
from database import (
    db_add_cat,
    db_add_flat,
    db_add_user,
    db_change_user_balance,
    db_delete_cat,
    db_delete_flat,
    db_get_all_cats,
    db_get_all_flats,
    db_get_cat_by_id,
    db_get_cats_by_city,
    db_get_flat_by_id,
    db_get_flats_by_city,
    db_get_setting,
    db_get_stats,
    db_get_user,
    db_set_setting,
    db_update_cat_field,
    db_update_flat_field,
    db_update_user_field,
    db_update_user_lang,
)
from middlewares import REGISTERED_USERS_CACHE

router = Router()

class Registration(StatesGroup):
    lang = State()
    name = State()
    phone = State()
    city = State()

class AdminAuth(StatesGroup):
    password = State()

class QuickAddCat(StatesGroup):
    template = State()

class QuickAddFlat(StatesGroup):
    photos = State()
    template = State()

class EditCat(StatesGroup):
    cat_id = State()
    field = State()
    value = State()

class EditFlat(StatesGroup):
    flat_id = State()
    field = State()
    value = State()

class EditUser(StatesGroup):
    user_id = State()
    field = State()
    value = State()

class DeleteCat(StatesGroup):
    message_id = State()

class DeleteFlat(StatesGroup):
    message_id = State()

class AdminSettings(StatesGroup):
    change_support = State()
    change_req_type = State()
    change_req_value = State()

class DepositState(StatesGroup):
    amount = State()
    method = State()
    check_photo = State()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS if ADMIN_IDS else False

async def get_support_account() -> str:
    return await db_get_setting("support_account", "@your_support_username")

async def get_requisite(method: str) -> str:
    defaults = {
        "uzcard": "💳 <code>Не указано</code>",
        "rub": "💳 <code>Не указано</code>",
        "crypto": "💎 <code>Не указано</code>",
    }
    return await db_get_setting(f"req_{method}", defaults.get(method, "Не указано"))

def get_admin_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⚡ Добавить котенка", callback_data="admin_add_cat"),
                InlineKeyboardButton(text="🏠 Добавить квартиру", callback_data="admin_add_flat"),
            ],
            [
                InlineKeyboardButton(text="❌ Удалить котенка", callback_data="admin_del_cat"),
                InlineKeyboardButton(text="❌ Удалить квартиру", callback_data="admin_del_flat"),
            ],
            [
                InlineKeyboardButton(text="✏️ Изменить котенка", callback_data="admin_edit_cat"),
                InlineKeyboardButton(text="✏️ Изменить квартиру", callback_data="admin_edit_flat"),
            ],
            [
                InlineKeyboardButton(text="👤 Изменить юзера", callback_data="admin_edit_user"),
                InlineKeyboardButton(text="💳 Реквизиты", callback_data="admin_change_requisites"),
            ],
            [
                InlineKeyboardButton(text="⚙️ Поддержка", callback_data="admin_change_support"),
                InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
            ],
            [
                InlineKeyboardButton(text="📋 Котята", callback_data="admin_list_cats"),
                InlineKeyboardButton(text="📋 Квартиры", callback_data="admin_list_flats"),
            ],
            [InlineKeyboardButton(text="🚪 Выйти из админки", callback_data="admin_exit")],
        ]
    )

def get_cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_admin_action")]]
    )

def get_main_keyboard(lang: str = "ru") -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text=TEXTS[lang]["main_find"]), KeyboardButton(text=TEXTS[lang]["main_find_flat"])],
        [KeyboardButton(text=TEXTS[lang]["main_profile"]), KeyboardButton(text=TEXTS[lang]["btn_support"])],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_cities_inline_kb(prefix: str, add_back: bool = True, lang: str = "ru") -> InlineKeyboardMarkup:
    cities_list = CITIES_UZ if lang == "uz" else CITIES_RU
    builder = []
    row = []
    for city in cities_list:
        row.append(InlineKeyboardButton(text=f"🏙 {city}", callback_data=f"{prefix}:{city}"))
        if len(row) == 2:
            builder.append(row)
            row = []
    if row:
        builder.append(row)

    if add_back:
        builder.append([InlineKeyboardButton(text=TEXTS[lang]["btn_back"], callback_data="go_main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=builder)

# ================= REGISTRATION & PROFILE =================

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    user = await db_get_user(user_id)

    if user:
        REGISTERED_USERS_CACHE.add(user_id)
        lang = user["lang"]
        await message.answer(
            TEXTS[lang]["welcome_back"].format(name=user["name"]),
            reply_markup=get_main_keyboard(lang),
        )
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="set_lang:uz"),
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang:ru"),
            ]
        ]
    )
    await message.answer(TEXTS["ru"]["welcome"], reply_markup=kb)
    await state.set_state(Registration.lang)

@router.callback_query(Registration.lang, F.data.startswith("set_lang:"))
async def process_reg_lang(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    lang = callback.data.split(":")[1]
    await state.update_data(lang=lang)
    await callback.message.answer(TEXTS[lang]["reg_name"])
    await state.set_state(Registration.name)

@router.message(Registration.name)
async def process_name(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")

    await state.update_data(name=message.text)
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=TEXTS[lang]["btn_phone"], request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await message.answer(
        TEXTS[lang]["reg_phone"].format(name=message.text),
        reply_markup=kb,
    )
    await state.set_state(Registration.phone)

@router.message(Registration.phone, F.contact)
async def process_phone(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")

    await state.update_data(phone=message.contact.phone_number)
    await message.answer("...", reply_markup=ReplyKeyboardRemove())

    await message.answer(
        TEXTS[lang]["reg_city"],
        reply_markup=get_cities_inline_kb("reg_city", add_back=False, lang=lang),
    )
    await state.set_state(Registration.city)

@router.callback_query(Registration.city, F.data.startswith("reg_city:"))
async def process_reg_city(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    await callback.answer()
    selected_city = callback.data.split(":")[1]
    user_data = await state.get_data()
    user_id = callback.from_user.id
    lang = user_data.get("lang", "ru")

    city_db = CITY_MAP_UZ_TO_RU.get(selected_city, selected_city) if lang == "uz" else selected_city

    await db_add_user(
        user_id=user_id,
        name=user_data["name"],
        phone=user_data["phone"],
        city=city_db,
        lang=lang,
    )

    REGISTERED_USERS_CACHE.add(user_id)

    user_card = (
        "👤 <b>Новая регистрация!</b>\n\n"
        f"▪️ <b>Имя:</b> {user_data['name']}\n"
        f"▪️ <b>Телефон:</b> +{str(user_data['phone']).replace('+', '')}\n"
        f"▪️ <b>Город:</b> {city_db}\n"
        f"▪️ <b>Язык:</b> {lang.upper()}\n"
        f"▪️ <b>ID:</b> <code>{user_id}</code>\n"
        f"▪️ <b>Username:</b> @{callback.from_user.username or 'нет'}"
    )

    if USERS_CHANNEL_ID != 0:
        try:
            await bot.send_message(chat_id=USERS_CHANNEL_ID, text=user_card)
        except Exception as e:
            logging.error(f"Ошибка логирования: {e}")

    await state.clear()
    await callback.message.answer(
        TEXTS[lang]["reg_success"], reply_markup=get_main_keyboard(lang)
    )

@router.message(F.text.in_([TEXTS["ru"]["main_profile"], TEXTS["uz"]["main_profile"], "👤 Мой профиль", "👤 Mening profilim"]))
async def show_profile(message: Message):
    user_id = message.from_user.id
    user = await db_get_user(user_id)

    lang = user["lang"] if user else "ru"
    display_city = CITY_MAP_RU_TO_UZ.get(user["city"], user["city"]) if lang == "uz" and user else user["city"] if user else "Ташкент"

    profile_text = TEXTS[lang]["profile"].format(
        name=user["name"] if user else "Пользователь",
        phone=user["phone"] if user else "-",
        city=display_city,
        lang="O'zbekcha 🇺🇿" if lang == "uz" else "Русский 🇷🇺",
        balance=user["balance"] if user else 0,
        user_id=user_id,
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=TEXTS[lang]["deposit_btn"], callback_data="deposit_balance")],
            [InlineKeyboardButton(text=TEXTS[lang]["btn_change_lang"], callback_data="change_user_lang")],
        ]
    )
    await message.answer(profile_text, reply_markup=kb)

@router.message(F.text.in_([TEXTS["ru"]["btn_support"], TEXTS["uz"]["btn_support"], "💬 Поддержка", "💬 Qo'llab-quvvatlash"]))
async def show_support(message: Message):
    user = await db_get_user(message.from_user.id)
    lang = user["lang"] if user else "ru"
    support_acc = await get_support_account()
    clean_username = support_acc.replace("@", "").replace("https://t.me/", "")
    
    text = TEXTS[lang]["support_text"].format(support=support_acc)
    btn_text = TEXTS[lang]["support_btn"]

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=btn_text, url=f"https://t.me/{clean_username}")]
        ]
    )
    await message.answer(text, reply_markup=kb)

@router.callback_query(F.data == "change_user_lang")
async def change_user_lang_menu(callback: types.CallbackQuery):
    await callback.answer()
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="switch_lang:uz"),
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="switch_lang:ru"),
            ]
        ]
    )
    await callback.message.answer("Выберите новый язык / Yangi tilni tanlang:", reply_markup=kb)

@router.callback_query(F.data.startswith("switch_lang:"))
async def switch_user_lang(callback: types.CallbackQuery):
    await callback.answer()
    new_lang = callback.data.split(":")[1]
    user_id = callback.from_user.id

    await db_update_user_lang(user_id, new_lang)
    await callback.message.answer(
        TEXTS[new_lang]["lang_changed"],
        reply_markup=get_main_keyboard(new_lang),
    )

# ================= DEPOSIT SYSTEM (P2P) =================

@router.callback_query(F.data == "deposit_balance")
async def start_deposit(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer(
        "💳 <b>Введите сумму пополнения в сумах (только цифры):</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_deposit")]]),
    )
    await state.set_state(DepositState.amount)

@router.callback_query(F.data == "cancel_deposit")
async def cancel_deposit(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer("Пополнение отменено.")
    try:
        await callback.message.delete()
    except Exception:
        pass

@router.message(DepositState.amount)
async def process_deposit_amount(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) <= 0:
        await message.answer("❌ Пожалуйста, введите корректную сумму числом!")
        return
    
    await state.update_data(amount=int(message.text))
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇺🇿 Uzcard / Humo", callback_data="pay_method:uzcard")],
            [InlineKeyboardButton(text="🇷🇺 Карта РФ (МИР/Visa/MasterCard)", callback_data="pay_method:rub")],
            [InlineKeyboardButton(text="💎 Криптовалюта (USDT/TON)", callback_data="pay_method:crypto")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_deposit")]
        ]
    )
    await message.answer("<b>Выберите способ оплаты:</b>", reply_markup=kb)
    await state.set_state(DepositState.method)

@router.callback_query(DepositState.method, F.data.startswith("pay_method:"))
async def process_deposit_method(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    method = callback.data.split(":")[1]
    data = await state.get_data()
    amount = data["amount"]
    
    req_text = await get_requisite(method)
    await state.update_data(method=method)
    
    text = (
        f"💰 <b>Сумма к оплате:</b> <code>{amount:,} сум</code>\n\n"
        f"Переведите указанную сумму по реквизитам:\n\n"
        f"{req_text}\n\n"
        f"📸 <b>После оплаты отправьте СКРИНШОТ ЧЕКА сюда в чат.</b>"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_deposit")]])
    await callback.message.answer(text, reply_markup=kb)
    await state.set_state(DepositState.check_photo)

@router.message(DepositState.check_photo, F.photo)
async def process_deposit_check(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    amount = data["amount"]
    user_id = message.from_user.id
    photo_id = message.photo[-1].file_id
    
    user = await db_get_user(user_id)
    user_name = user["name"] if user else "Пользователь"
    
    caption = (
        f"💳 <b>НОВАЯ ЗАЯВКА НА ПОПОЛНЕНИЕ!</b>\n\n"
        f"👤 <b>Заказчик:</b> {user_name} (ID: <code>{user_id}</code>)\n"
        f"💰 <b>Сумма:</b> {amount:,} сум\n"
        f"📌 <b>Способ:</b> {data['method'].upper()}\n\n"
        f"📌 <b>Статус:</b> ⏳ <i>Ожидает проверки</i>"
    )
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"app_dep:{user_id}:{amount}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"rej_dep:{user_id}")
            ]
        ]
    )
    
    if USERS_CHANNEL_ID != 0:
        try:
            await bot.send_photo(chat_id=USERS_CHANNEL_ID, photo=photo_id, caption=caption, reply_markup=kb)
            await message.answer("✅ <b>Чек отправлен на проверку!</b>\nБаланс будет зачислен после подтверждения администратором.")
        except Exception as e:
            await message.answer(f"❌ Ошибка отправки чека в канал:\n<code>{e}</code>")
            logging.error(f"Ошибка логирования депозита: {e}")
    else:
        await message.answer("❌ Канал модерации не настроен.")
        
    await state.clear()

@router.callback_query(F.data.startswith("app_dep:"))
async def approve_deposit(callback: types.CallbackQuery, bot: Bot):
    _, user_id_str, amount_str = callback.data.split(":")
    user_id = int(user_id_str)
    amount = int(amount_str)
    
    success = await db_change_user_balance(user_id, amount)
    if success:
        user = await db_get_user(user_id)
        new_balance = user["balance"] if user else 0
        try:
            await bot.send_message(
                chat_id=user_id,
                text=f"🎉 <b>Ваш баланс пополнен на {amount:,} сум!</b>\nТекущий баланс: <b>{new_balance:,} сум</b>",
            )
        except Exception as e:
            logging.error(f"Ошибка уведомления клиента: {e}")
            
    updated_caption = callback.message.caption.replace("⏳ Ожидает проверки", f"✅ <b>ОДОБРЕНО (+{amount:,} сум)</b>")
    await callback.message.edit_caption(caption=updated_caption, reply_markup=None)
    await callback.answer("Баланс успешно зачислен!")

@router.callback_query(F.data.startswith("rej_dep:"))
async def reject_deposit(callback: types.CallbackQuery, bot: Bot):
    user_id = int(callback.data.split(":")[1])
    
    try:
        await bot.send_message(
            chat_id=user_id,
            text="❌ <b>Ваша заявка на пополнение отклонена.</b>\nЕсли возникли вопросы, обратитесь в поддержку.",
        )
    except Exception as e:
        logging.error(f"Ошибка уведомления клиента: {e}")
        
    updated_caption = callback.message.caption.replace("⏳ Ожидает проверки", "❌ <b>ОТКЛОНЕНО</b>")
    await callback.message.edit_caption(caption=updated_caption, reply_markup=None)
    await callback.answer("Заявка отклонена.")

# ================= CAROUSEL & CAT CATALOG =================

@router.message(F.text.in_([TEXTS["ru"]["main_find"], TEXTS["uz"]["main_find"], "🐱 Найти котенка", "🐱 Mushukcha topish"]))
async def search_cats_menu(message: Message):
    user = await db_get_user(message.from_user.id)
    lang = user["lang"] if user else "ru"
    await message.answer(
        TEXTS[lang]["select_city"],
        reply_markup=get_cities_inline_kb("search_city", lang=lang),
    )

@router.callback_query(F.data == "go_main_menu")
async def go_main_menu(callback: types.CallbackQuery):
    await callback.answer()
    user = await db_get_user(callback.from_user.id)
    lang = user["lang"] if user else "ru"
    await callback.message.answer(TEXTS[lang]["main_menu_title"], reply_markup=get_main_keyboard(lang))

async def build_carousel_keyboard(city: str, index: int, total: int, cat_id: int, lang: str = "ru"):
    support_acc = await get_support_account()
    clean_username = support_acc.replace("@", "").replace("https://t.me/", "")
    
    action_row = [
        InlineKeyboardButton(text=TEXTS[lang]["btn_order"], callback_data=f"order_cat:{cat_id}"),
        InlineKeyboardButton(text=TEXTS[lang]["btn_contact"], url=f"https://t.me/{clean_username}"),
    ]
    
    buttons = [action_row]
    nav_row = []

    if index > 0:
        nav_row.append(InlineKeyboardButton(text=TEXTS[lang]["nav_prev"], callback_data=f"cat_nav:{city}:{index - 1}"))

    nav_row.append(InlineKeyboardButton(text=f"📍 {index + 1}/{total}", callback_data="ignore"))

    if index < total - 1:
        nav_row.append(InlineKeyboardButton(text=TEXTS[lang]["nav_next"], callback_data=f"cat_nav:{city}:{index + 1}"))

    buttons.append(nav_row)
    buttons.append([InlineKeyboardButton(text=TEXTS[lang]["btn_back_cities"], callback_data="back_to_cities")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def render_cat_card(callback: types.CallbackQuery, city: str, index: int, edit: bool = False):
    user = await db_get_user(callback.from_user.id)
    lang = user["lang"] if user else "ru"

    city_ru = CITY_MAP_UZ_TO_RU.get(city, city)
    display_city = CITY_MAP_RU_TO_UZ.get(city_ru, city_ru) if lang == "uz" else city_ru

    cats = await db_get_cats_by_city(city_ru)

    if not cats:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=TEXTS[lang]["btn_back_cities"], callback_data="back_to_cities")]]
        )
        msg_text = TEXTS[lang]["no_cats"].format(city=display_city)
        if edit:
            try:
                await callback.message.edit_text(msg_text, reply_markup=kb)
            except Exception:
                await callback.message.answer(msg_text, reply_markup=kb)
        else:
            await callback.message.answer(msg_text, reply_markup=kb)
        return

    index = max(0, min(index, len(cats) - 1))
    cat = cats[index]

    caption = TEXTS[lang]["cat_card"].format(
        name=cat["name"],
        age=cat["age"],
        nationality=cat["nationality"],
        price_walk=cat["price_walk"],
        price_hour=cat["price_hour"],
        price_night=cat["price_night"],
        city=display_city,
    )

    reply_markup = await build_carousel_keyboard(city, index, len(cats), cat_id=cat["id"], lang=lang)

    if edit:
        try:
            media = InputMediaPhoto(media=cat["photo"], caption=caption)
            await callback.message.edit_media(media=media, reply_markup=reply_markup)
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                await callback.message.answer_photo(photo=cat["photo"], caption=caption, reply_markup=reply_markup)
        except Exception:
            await callback.message.answer_photo(photo=cat["photo"], caption=caption, reply_markup=reply_markup)
    else:
        await callback.message.answer_photo(photo=cat["photo"], caption=caption, reply_markup=reply_markup)

@router.callback_query(F.data.startswith("search_city:"))
async def process_city_search(callback: types.CallbackQuery):
    await callback.answer()
    selected_city = callback.data.split(":")[1]
    await render_cat_card(callback, selected_city, index=0, edit=False)

@router.callback_query(F.data.startswith("cat_nav:"))
async def process_cat_nav(callback: types.CallbackQuery):
    await callback.answer()
    _, city, index_str = callback.data.split(":")
    await render_cat_card(callback, city, index=int(index_str), edit=True)

@router.callback_query(F.data == "ignore")
async def process_ignore(callback: types.CallbackQuery):
    await callback.answer()

@router.callback_query(F.data == "back_to_cities")
async def back_to_cities(callback: types.CallbackQuery):
    await callback.answer()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await search_cats_menu(callback.message)

# ================= CAROUSEL & FLAT CATALOG =================

@router.message(F.text.in_([TEXTS["ru"]["main_find_flat"], TEXTS["uz"]["main_find_flat"], "🏠 Найти квартиру", "🏠 Xonadon topish"]))
async def search_flats_menu(message: Message):
    user = await db_get_user(message.from_user.id)
    lang = user["lang"] if user else "ru"
    await message.answer(
        TEXTS[lang]["select_city"],
        reply_markup=get_cities_inline_kb("search_flat_city", lang=lang),
    )

async def build_flat_carousel_keyboard(city: str, index: int, total: int, flat_id: int, lang: str = "ru"):
    support_acc = await get_support_account()
    clean_username = support_acc.replace("@", "").replace("https://t.me/", "")
    
    action_row = [
        InlineKeyboardButton(text=TEXTS[lang]["btn_order"], callback_data=f"order_flat:{flat_id}"),
        InlineKeyboardButton(text=TEXTS[lang]["btn_contact"], url=f"https://t.me/{clean_username}"),
    ]
    
    buttons = [action_row]
    nav_row = []

    if index > 0:
        nav_row.append(InlineKeyboardButton(text=TEXTS[lang]["nav_prev"], callback_data=f"flat_nav:{city}:{index - 1}"))

    nav_row.append(InlineKeyboardButton(text=f"📍 {index + 1}/{total}", callback_data="ignore"))

    if index < total - 1:
        nav_row.append(InlineKeyboardButton(text=TEXTS[lang]["nav_next"], callback_data=f"flat_nav:{city}:{index + 1}"))

    buttons.append(nav_row)
    buttons.append([InlineKeyboardButton(text=TEXTS[lang]["btn_back_cities"], callback_data="back_to_flat_cities")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def render_flat_card(callback: types.CallbackQuery, city: str, index: int, bot: Bot, edit: bool = False):
    user = await db_get_user(callback.from_user.id)
    lang = user["lang"] if user else "ru"

    city_ru = CITY_MAP_UZ_TO_RU.get(city, city)
    display_city = CITY_MAP_RU_TO_UZ.get(city_ru, city_ru) if lang == "uz" else city_ru

    flats = await db_get_flats_by_city(city_ru)

    if not flats:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=TEXTS[lang]["btn_back_cities"], callback_data="back_to_flat_cities")]]
        )
        msg_text = TEXTS[lang]["no_flats"].format(city=display_city)
        if edit:
            try:
                await callback.message.edit_text(msg_text, reply_markup=kb)
            except Exception:
                await callback.message.answer(msg_text, reply_markup=kb)
        else:
            await callback.message.answer(msg_text, reply_markup=kb)
        return

    index = max(0, min(index, len(flats) - 1))
    flat = flats[index]

    caption = TEXTS[lang]["flat_card"].format(
        title=flat["title"],
        location=flat["location"],
        price_day=flat["price_day"],
        city=display_city,
    )

    reply_markup = await build_flat_carousel_keyboard(city, index, len(flats), flat_id=flat["id"], lang=lang)

    photos = flat["photos"]
    if len(photos) > 1:
        if edit:
            try:
                await callback.message.delete()
            except Exception:
                pass
        media_group = [InputMediaPhoto(media=p) for p in photos[:-1]]
        media_group.append(InputMediaPhoto(media=photos[-1], caption=caption))
        await bot.send_media_group(chat_id=callback.message.chat.id, media=media_group)
        await callback.message.answer("🏠 <b>Панель управления:</b>", reply_markup=reply_markup)
    else:
        photo = photos[0] if photos else "https://via.placeholder.com/300"
        if edit:
            try:
                media = InputMediaPhoto(media=photo, caption=caption)
                await callback.message.edit_media(media=media, reply_markup=reply_markup)
            except TelegramBadRequest as e:
                if "message is not modified" not in str(e):
                    await callback.message.answer_photo(photo=photo, caption=caption, reply_markup=reply_markup)
            except Exception:
                await callback.message.answer_photo(photo=photo, caption=caption, reply_markup=reply_markup)
        else:
            await callback.message.answer_photo(photo=photo, caption=caption, reply_markup=reply_markup)

@router.callback_query(F.data.startswith("search_flat_city:"))
async def process_flat_city_search(callback: types.CallbackQuery, bot: Bot):
    await callback.answer()
    selected_city = callback.data.split(":")[1]
    await render_flat_card(callback, selected_city, index=0, bot=bot, edit=False)

@router.callback_query(F.data.startswith("flat_nav:"))
async def process_flat_nav(callback: types.CallbackQuery, bot: Bot):
    await callback.answer()
    _, city, index_str = callback.data.split(":")
    await render_flat_card(callback, city, index=int(index_str), bot=bot, edit=True)

@router.callback_query(F.data == "back_to_flat_cities")
async def back_to_flat_cities(callback: types.CallbackQuery):
    await callback.answer()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await search_flats_menu(callback.message)

# ================= ORDER PROCESSING =================

@router.callback_query(F.data.startswith("order_cat:"))
async def process_order_rate_selection(callback: types.CallbackQuery):
    cat_id = int(callback.data.split(":")[1])
    cat = await db_get_cat_by_id(cat_id)
    user = await db_get_user(callback.from_user.id)
    lang = user["lang"] if user else "ru"

    if not cat:
        await callback.answer("Анкета не найдена / Anket mavjud emas.", show_alert=True)
        return

    text = (
        f"⏱ <b>Выберите тариф для заказа:</b>\n\n"
        f"📌 <b>Ходка:</b> <code>{cat['price_walk']:,} сум</code>\n"
        f"⏳ <b>1 час:</b> <code>{cat['price_hour']:,} сум</code>\n"
        f"🌌 <b>Ночь:</b> <code>{cat['price_night']:,} сум</code>"
        if lang == "ru" else
        f"⏱ <b>Buyurtma tarifini tanlang:</b>\n\n"
        f"📌 <b>Xotka:</b> <code>{cat['price_walk']:,} so'm</code>\n"
        f"⏳ <b>1 soat:</b> <code>{cat['price_hour']:,} so'm</code>\n"
        f"🌌 <b>Tun:</b> <code>{cat['price_night']:,} so'm</code>"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"📌 Ходка ({cat['price_walk']:,} сум)", callback_data=f"select_rate:{cat_id}:walk")],
            [InlineKeyboardButton(text=f"⏳ 1 час ({cat['price_hour']:,} сум)", callback_data=f"select_rate:{cat_id}:hour")],
            [InlineKeyboardButton(text=f"🌌 Ночь ({cat['price_night']:,} сум)", callback_data=f"select_rate:{cat_id}:night")],
            [InlineKeyboardButton(text=TEXTS[lang]["btn_back"], callback_data="back_to_cities")]
        ]
    )
    await callback.message.answer(text, reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("select_rate:"))
async def process_order_final(callback: types.CallbackQuery, bot: Bot):
    _, cat_id_str, rate_type = callback.data.split(":")
    cat_id = int(cat_id_str)
    user_id = callback.from_user.id

    user = await db_get_user(user_id)
    cat = await db_get_cat_by_id(cat_id)
    lang = user["lang"] if user else "ru"

    if not cat or not user:
        await callback.answer("Ошибка при оформлении заказа.", show_alert=True)
        return

    rates_map = {
        "walk": (cat["price_walk"], "📌 Ходка" if lang == "ru" else "📌 Xotka"),
        "hour": (cat["price_hour"], "⏳ 1 час" if lang == "ru" else "⏳ 1 soat"),
        "night": (cat["price_night"], "🌌 Ночь" if lang == "ru" else "🌌 Tun"),
    }
    price, rate_name = rates_map.get(rate_type, (cat["price_hour"], "⏳ 1 час"))

    # Atomic balance deduction
    deducted = await db_change_user_balance(user_id, -price)
    if not deducted:
        msg_no_money = (
            f"❌ <b>Недостаточно средств на балансе!</b>\n\n"
            f"📋 <b>Выбранный тариф:</b> {rate_name}\n"
            f"💳 <b>Сумма к оплате:</b> <code>{price:,} сум</code>\n"
            f"💰 <b>Ваш баланс:</b> <code>{user['balance']:,} сум</code>\n\n"
            f"Пополните баланс в профиле, чтобы оформить заказ."
            if lang == "ru" else
            f"❌ <b>Balansda mablag' yetarli emas!</b>\n\n"
            f"📋 <b>Tanlangan tarif:</b> {rate_name}\n"
            f"💳 <b>To'lov summasi:</b> <code>{price:,} so'm</code>\n"
            f"💰 <b>Sizning balansdingiz:</b> <code>{user['balance']:,} so'm</code>\n\n"
            f"Buyurtma berish uchun profilingizda balansni to'ldiring."
        )
        await callback.answer("Недостаточно средств / Mablag' yetarli emas", show_alert=True)
        await callback.message.answer(msg_no_money)
        return

    user_info = f"<b>+{user['phone']}</b> ({user['name']})"
    new_balance = user['balance'] - price

    order_card = (
        f"🛍 <b>НОВАЯ ЗАЯВКА НА ЗАКАЗ (КОТЕНОК)!</b>\n\n"
        f"🐱 <b>Анкета:</b> {cat['name']} (ID: <code>{cat['id']}</code>)\n"
        f"⏱ <b>Тариф:</b> {rate_name}\n"
        f"💳 <b>Сумма заказа:</b> <code>{price:,} сум</code>\n"
        f"💰 <b>Остаток у клиента:</b> <code>{new_balance:,} сум</code>\n\n"
        f"👤 <b>Заказчик:</b> {user_info}\n"
        f"🏙 <b>Город:</b> {cat['city']}\n"
        f"🌐 <b>Язык:</b> {lang.upper()}\n"
        f"🆔 <b>TG ID:</b> <code>{user_id}</code>\n\n"
        f"📌 <b>Статус:</b> ⏳ <i>Ожидает модерации</i>"
    )

    moderation_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Принять", callback_data=f"mod_accept:{user_id}"),
                InlineKeyboardButton(text="❌ Отклонить и вернуть 💰", callback_data=f"mod_reject:{user_id}:{price}"),
            ],
            [
                InlineKeyboardButton(text="💬 Написать клиенту", url=f"tg://user?id={user_id}")
            ]
        ]
    )

    if USERS_CHANNEL_ID != 0:
        try:
            await bot.send_message(chat_id=USERS_CHANNEL_ID, text=order_card, reply_markup=moderation_kb)
            
            confirm_msg = (
                f"✅ <b>Заказ успешно оформлен!</b>\n\n"
                f"📋 <b>Тариф:</b> {rate_name}\n"
                f"💳 <b>Списано:</b> <code>{price:,} сум</code>\n"
                f"💰 <b>Остаток на балансе:</b> <code>{new_balance:,} сум</code>\n\n"
                f"Ожидайте, администратор скоро свяжется с вами."
                if lang == "ru" else
                f"✅ <b>Buyurtma muvaffaqiyatli rasmiylashtirildi!</b>\n\n"
                f"📋 <b>Tarif:</b> {rate_name}\n"
                f"💳 <b>Yechildi:</b> <code>{price:,} so'm</code>\n"
                f"💰 <b>Qoldiq balans:</b> <code>{new_balance:,} so'm</code>\n\n"
                f"Kuting, administrator tez orada siz bilan bog'lanadi."
            )
            await callback.message.answer(confirm_msg)
            await callback.answer()
        except Exception as e:
            await db_change_user_balance(user_id, price)
            await callback.answer("Ошибка отправки заказа. Деньги возвращены на баланс.", show_alert=True)
            logging.error(f"Ошибка отправки модерации: {e}")
    else:
        await callback.answer(TEXTS[lang]["order_success"], show_alert=True)

@router.callback_query(F.data.startswith("order_flat:"))
async def process_order_flat_final(callback: types.CallbackQuery, bot: Bot):
    flat_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    user = await db_get_user(user_id)
    flat = await db_get_flat_by_id(flat_id)
    lang = user["lang"] if user else "ru"

    if not flat or not user:
        await callback.answer("Квартира не найдена / Xonadon topilmadi.", show_alert=True)
        return

    price = flat["price_day"]

    deducted = await db_change_user_balance(user_id, -price)
    if not deducted:
        msg_no_money = (
            f"❌ <b>Недостаточно средств на балансе!</b>\n\n"
            f"🏠 <b>Объект:</b> {flat['title']}\n"
            f"💳 <b>Сумма к оплате:</b> <code>{price:,} сум</code>\n"
            f"💰 <b>Ваш баланс:</b> <code>{user['balance']:,} сум</code>\n\n"
            f"Пополните баланс в профиле, чтобы оформить заказ."
            if lang == "ru" else
            f"❌ <b>Balansda mablag' yetarli emas!</b>\n\n"
            f"🏠 <b>Ob'yekt:</b> {flat['title']}\n"
            f"💳 <b>To'lov summasi:</b> <code>{price:,} so'm</code>\n"
            f"💰 <b>Sizning balansdingiz:</b> <code>{user['balance']:,} so'm</code>\n\n"
            f"Buyurtma berish uchun profilingizda balansni to'ldiring."
        )
        await callback.answer("Недостаточно средств / Mablag' yetarli emas", show_alert=True)
        await callback.message.answer(msg_no_money)
        return

    new_balance = user['balance'] - price
    user_info = f"<b>+{user['phone']}</b> ({user['name']})"

    order_card = (
        f"🛍 <b>НОВАЯ ЗАЯВКА НА ЗАКАЗ (КВАРТИРА)!</b>\n\n"
        f"🏠 <b>Квартира:</b> {flat['title']} (ID: <code>{flat['id']}</code>)\n"
        f"📍 <b>Локация:</b> {flat['location']}\n"
        f"💳 <b>Сумма заказа:</b> <code>{price:,} сум</code>\n"
        f"💰 <b>Остаток у клиента:</b> <code>{new_balance:,} сум</code>\n\n"
        f"👤 <b>Заказчик:</b> {user_info}\n"
        f"🏙 <b>Город:</b> {flat['city']}\n"
        f"🌐 <b>Язык:</b> {lang.upper()}\n"
        f"🆔 <b>TG ID:</b> <code>{user_id}</code>\n\n"
        f"📌 <b>Статус:</b> ⏳ <i>Ожидает модерации</i>"
    )

    moderation_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Принять", callback_data=f"mod_accept:{user_id}"),
                InlineKeyboardButton(text="❌ Отклонить и вернуть 💰", callback_data=f"mod_reject:{user_id}:{price}"),
            ],
            [
                InlineKeyboardButton(text="💬 Написать клиенту", url=f"tg://user?id={user_id}")
            ]
        ]
    )

    if USERS_CHANNEL_ID != 0:
        try:
            await bot.send_message(chat_id=USERS_CHANNEL_ID, text=order_card, reply_markup=moderation_kb)
            
            confirm_msg = (
                f"✅ <b>Заказ успешно оформлен!</b>\n\n"
                f"🏠 <b>Квартира:</b> {flat['title']}\n"
                f"💳 <b>Списано:</b> <code>{price:,} сум</code>\n"
                f"💰 <b>Остаток на балансе:</b> <code>{new_balance:,} сум</code>\n\n"
                f"Ожидайте, администратор скоро свяжется с вами."
                if lang == "ru" else
                f"✅ <b>Buyurtma muvaffaqiyatli rasmiylashtirildi!</b>\n\n"
                f"🏠 <b>Xonadon:</b> {flat['title']}\n"
                f"💳 <b>Yechildi:</b> <code>{price:,} so'm</code>\n"
                f"💰 <b>Qoldiq balans:</b> <code>{new_balance:,} so'm</code>\n\n"
                f"Kuting, administrator tez orada siz bilan bog'lanadi."
            )
            await callback.message.answer(confirm_msg)
            await callback.answer()
        except Exception as e:
            await db_change_user_balance(user_id, price)
            await callback.answer("Ошибка отправки заказа. Деньги возвращены на баланс.", show_alert=True)
            logging.error(f"Ошибка отправки модерации: {e}")
    else:
        await callback.answer(TEXTS[lang]["order_success"], show_alert=True)

@router.callback_query(F.data.startswith("mod_accept:"))
async def accept_order(callback: types.CallbackQuery, bot: Bot):
    user_id = int(callback.data.split(":")[1])

    user = await db_get_user(user_id)
    lang = user["lang"] if user else "ru"

    msg_to_client = (
        "🎉 <b>Sizning buyurtmangiz tasdiqlandi!</b>\nTez orada operatorimiz siz bilan bog'lanadi."
        if lang == "uz" else
        "🎉 <b>Ваша заявка одобрена!</b>\nНаш менеджер свяжется с вами в ближайшее время."
    )

    try:
        await bot.send_message(chat_id=user_id, text=msg_to_client)
    except Exception as e:
        logging.error(f"Не удалось отправить статус клиенту: {e}")

    updated_text = callback.message.text.replace("⏳ Ожидает модерации", "✅ <b>ОДОБРЕНО</b>")
    await callback.message.edit_text(updated_text, reply_markup=None)
    await callback.answer("Заявка одобрена!")

@router.callback_query(F.data.startswith("mod_reject:"))
async def reject_order(callback: types.CallbackQuery, bot: Bot):
    parts = callback.data.split(":")
    user_id = int(parts[1])
    refund_amount = int(parts[2]) if len(parts) > 2 else 0

    user = await db_get_user(user_id)
    lang = user["lang"] if user else "ru"

    if refund_amount > 0 and user:
        await db_change_user_balance(user_id, refund_amount)

    msg_to_client = (
        f"Afsuski, <b>sizning buyurtmangiz rad etildi</b>.\n💰 Balansga {refund_amount:,} so'm qaytarildi."
        if lang == "uz" else
        f"К сожалению, <b>ваша заявка была отклонена</b>.\n💰 На ваш баланс возвращено {refund_amount:,} сум."
    )

    try:
        await bot.send_message(chat_id=user_id, text=msg_to_client)
    except Exception as e:
        logging.error(f"Не удалось отправить статус клиенту: {e}")

    updated_text = callback.message.text.replace("⏳ Ожидает модерации", f"❌ <b>ОТКЛОНЕНО (Возвращено {refund_amount:,} сум)</b>")
    await callback.message.edit_text(updated_text, reply_markup=None)
    await callback.answer("Заявка отклонена, средства возвращены.")

# ================= ADMIN PANEL =================

@router.message(Command("admin"))
@router.message(Command("simsim"))
async def cmd_admin(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id

    if is_admin(user_id):
        await message.answer("🔑 <b>Панель Администратора</b>\nВыберите действие:", reply_markup=get_admin_main_kb())
    else:
        await message.answer("🔑 <b>Введите пароль для входа в админ-панель:</b>")
        await state.set_state(AdminAuth.password)

@router.message(AdminAuth.password)
async def process_admin_password(message: Message, state: FSMContext):
    if message.text == ADMIN_PASSWORD:
        await state.clear()
        await message.answer("✅ Доступ разрешен!")
        await message.answer("🔑 <b>Панель Администратора</b>\nВыберите действие:", reply_markup=get_admin_main_kb())
    else:
        await message.answer("❌ <b>Неверный пароль!</b> Доступ запрещен.")
        await state.clear()

@router.callback_query(F.data == "admin_change_requisites")
async def start_change_requisites(callback: types.CallbackQuery):
    await callback.answer()
    uzcard = await get_requisite("uzcard")
    rub = await get_requisite("rub")
    crypto = await get_requisite("crypto")
    
    text = (
        "💳 <b>Настройка реквизитов оплаты:</b>\n\n"
        f"🇺🇿 <b>Uzcard/Humo:</b>\n{uzcard}\n\n"
        f"🇷🇺 <b>Карта РФ:</b>\n{rub}\n\n"
        f"💎 <b>Криптовалюта:</b>\n{crypto}\n\n"
        "Выберите, какие реквизиты хотите изменить:"
    )
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇺🇿 Изменить Uzcard/Humo", callback_data="set_req:uzcard")],
            [InlineKeyboardButton(text="🇷🇺 Изменить Карту РФ", callback_data="set_req:rub")],
            [InlineKeyboardButton(text="💎 Изменить Крипту", callback_data="set_req:crypto")],
            [InlineKeyboardButton(text="🔙 Назад в админку", callback_data="cancel_admin_action")]
        ]
    )
    await callback.message.edit_text(text, reply_markup=kb)

@router.callback_query(F.data.startswith("set_req:"))
async def process_set_req_choice(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    req_type = callback.data.split(":")[1]
    await state.update_data(req_type=req_type)
    
    prompts = {
        "uzcard": "Пришлите новые реквизиты для Uzcard/Humo (номер карты и ФИО):",
        "rub": "Пришлите новые реквизиты для карт РФ (номер карты/СБП, банк и ФИО):",
        "crypto": "Пришлите новые реквизиты для Криптовалюты (адрес кошелька и сеть):"
    }
    await callback.message.answer(prompts[req_type], reply_markup=get_cancel_kb())
    await state.set_state(AdminSettings.change_req_value)

@router.message(AdminSettings.change_req_value)
async def process_set_req_value(message: Message, state: FSMContext):
    data = await state.get_data()
    req_type = data["req_type"]
    new_value = message.text.strip()
    
    await db_set_setting(f"req_{req_type}", new_value)
    await message.answer(f"✅ <b>Реквизиты для {req_type.upper()} успешно обновлены!</b>", reply_markup=get_admin_main_kb())
    await state.clear()

@router.callback_query(F.data == "admin_change_support")
async def start_change_support(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    current = await get_support_account()
    text = (
        f"⚙️ <b>Текущий аккаунт поддержки:</b> <code>{current}</code>\n\n"
        f"Пришлите новый юзернейм в формате <code>@username</code> или ссылку:"
    )
    await callback.message.answer(text, reply_markup=get_cancel_kb())
    await state.set_state(AdminSettings.change_support)

@router.message(AdminSettings.change_support)
async def process_change_support(message: Message, state: FSMContext):
    new_support = message.text.strip()

    if not new_support.startswith("@") and "t.me/" not in new_support:
        await message.answer("❌ Укажите юзернейм через @ (например, <code>@my_support</code>)!")
        return

    await db_set_setting("support_account", new_support)
    await message.answer(
        f"✅ <b>Контакты поддержки успешно обновлены!</b>\nНовый контакт: <b>{new_support}</b>",
        reply_markup=get_admin_main_kb(),
    )
    await state.clear()

@router.callback_query(F.data == "back_to_admin")
@router.callback_query(F.data == "cancel_admin_action")
async def back_to_admin_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    await callback.message.answer("🔑 <b>Панель Администратора</b>\nВыберите действие:", reply_markup=get_admin_main_kb())

@router.callback_query(F.data == "admin_exit")
async def admin_exit(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer("Вы вышли из админ-панели.")
    user = await db_get_user(callback.from_user.id)
    lang = user["lang"] if user else "ru"
    await callback.message.answer("Вы вернулись в режим обычного пользователя.", reply_markup=get_main_keyboard(lang))

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: types.CallbackQuery):
    await callback.answer()
    users_count, cats_count, flats_count = await db_get_stats()
    text = (
        f"📊 <b>Статистика системы:</b>\n\n"
        f"👥 Зарегистрировано пользователей: <b>{users_count}</b>\n"
        f"🐱 Активных анкет котят: <b>{cats_count}</b>\n"
        f"🏠 Активных квартир: <b>{flats_count}</b>"
    )
    await callback.message.edit_text(text, reply_markup=get_cancel_kb())

@router.callback_query(F.data == "admin_edit_user")
async def start_edit_user(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("Введите <b>Telegram ID пользователя</b>, которому хотите изменить данные:", reply_markup=get_cancel_kb())
    await state.set_state(EditUser.user_id)

@router.message(EditUser.user_id)
async def process_edit_user_id(message: Message, state: FSMContext):
    try:
        user_id = int(message.text.strip())
        user = await db_get_user(user_id)
        if not user:
            await message.answer("❌ Пользователь с таким ID не найден!", reply_markup=get_cancel_kb())
            return

        await state.update_data(user_id=user_id)
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="💰 Изменить баланс", callback_data="edit_u_field:balance"),
                    InlineKeyboardButton(text="🏙 Изменить город", callback_data="edit_u_field:city"),
                ],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_admin_action")],
            ]
        )
        await message.answer(
            f"Найдена запись:\n👤 <b>{user['name']}</b>\n💰 Баланс: {user['balance']:,} сум\n🏙 Город: {user['city']}\n\nЧто хотите изменить?",
            reply_markup=kb,
        )
    except ValueError:
        await message.answer("Введите корректный числовой ID!")

@router.callback_query(F.data.startswith("edit_u_field:"))
async def process_user_field_choice(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    field = callback.data.split(":")[1]
    await state.update_data(field=field)

    field_prompts = {
        "balance": "новую сумму баланса (только цифры):",
        "city": f"новый город из списка ({', '.join(CITIES_RU)}):",
    }
    await callback.message.answer(f"Введите {field_prompts[field]}", reply_markup=get_cancel_kb())
    await state.set_state(EditUser.value)

@router.message(EditUser.value)
async def process_edit_user_value(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = data["user_id"]
    field = data["field"]
    value = message.text.strip()

    if field == "balance":
        if not value.isdigit():
            await message.answer("❌ Ошибка! Баланс должен состоять только из цифр.")
            return
        value = int(value)

    if field == "city":
        matched_city = next((c for c in CITIES_RU if c.lower() == value.lower()), None)
        if not matched_city:
            await message.answer(f"❌ Город должен быть из списка: {', '.join(CITIES_RU)}")
            return
        value = matched_city

    await db_update_user_field(user_id, field, value)
    await message.answer(f"✅ Данные пользователя <code>{user_id}</code> успешно обновлены!", reply_markup=get_admin_main_kb())
    await state.clear()

# --- АДМИНКА КОТЯТА ---

@router.callback_query(F.data == "admin_edit_cat")
async def start_edit_cat(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("Введите <b>ID анкеты котенка</b>, которую хотите изменить:", reply_markup=get_cancel_kb())
    await state.set_state(EditCat.cat_id)

@router.message(EditCat.cat_id)
async def process_edit_cat_id(message: Message, state: FSMContext):
    try:
        cat_id = int(message.text)
        cat = await db_get_cat_by_id(cat_id)
        if not cat:
            await message.answer("❌ Анкета с таким ID не найдена!", reply_markup=get_cancel_kb())
            return

        await state.update_data(cat_id=cat_id)
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🚶‍♂️ Цену за ходку", callback_data="edit_field:price_walk"),
                    InlineKeyboardButton(text="⏱ Цену за час", callback_data="edit_field:price_hour"),
                ],
                [
                    InlineKeyboardButton(text="🌙 Цену за ночь", callback_data="edit_field:price_night"),
                    InlineKeyboardButton(text="🌐 Национальность", callback_data="edit_field:nationality"),
                ],
                [
                    InlineKeyboardButton(text="🐱 Имя", callback_data="edit_field:name"),
                    InlineKeyboardButton(text="🏙 Город", callback_data="edit_field:city"),
                ],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_admin_action")],
            ]
        )
        await message.answer(
            f"Найдена анкета: <b>{cat['name']}</b> (Город: {cat['city']}, {cat['price_hour']:,} сум/ч)\n\nЧто хотите изменить?",
            reply_markup=kb,
        )
    except ValueError:
        await message.answer("Введите числовой ID!")

@router.callback_query(F.data.startswith("edit_field:"))
async def process_field_choice(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    field = callback.data.split(":")[1]
    await state.update_data(field=field)

    field_names = {
        "price_walk": "новую цену за ходку (только цифры)",
        "price_hour": "новую цену за 1 час (только цифры)",
        "price_night": "новую цену за ночь (только цифры)",
        "nationality": "национальность",
        "name": "новое имя котенка",
        "city": f"новый город ({', '.join(CITIES_RU)})",
    }
    await callback.message.answer(f"Введите {field_names[field]}:", reply_markup=get_cancel_kb())
    await state.set_state(EditCat.value)

@router.message(EditCat.value)
async def process_edit_value(message: Message, state: FSMContext):
    data = await state.get_data()
    cat_id = data["cat_id"]
    field = data["field"]
    value = message.text.strip()

    if field in ["price_walk", "price_hour", "price_night"]:
        if not value.isdigit():
            await message.answer("❌ Ошибка! Цена должна состоять только из цифр.")
            return
        value = int(value)

    if field == "city":
        matched_city = next((c for c in CITIES_RU if c.lower() == value.lower()), None)
        if not matched_city:
            await message.answer(f"❌ Город должен быть из списка: {', '.join(CITIES_RU)}")
            return
        value = matched_city

    await db_update_cat_field(cat_id, field, value)
    await message.answer(f"✅ Анкета ID <code>{cat_id}</code> успешно обновлена!", reply_markup=get_admin_main_kb())
    await state.clear()

@router.callback_query(F.data == "admin_add_cat")
async def start_quick_add_cat(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    text = (
        "📸 <b>Отправьте ФОТОГРАФИЮ котенка</b>, а в описание вставьте текст по шаблону:\n\n"
        "<code>"
        "Имя: Пушок\n"
        "Возраст: 2 месяца\n"
        "Национальность: Британская\n"
        "Город: Ташкент\n"
        "Цена ходка: 20000\n"
        "Цена час: 40000\n"
        "Цена ночь: 150000"
        "</code>"
    )
    await callback.message.answer(text, reply_markup=get_cancel_kb())
    await state.set_state(QuickAddCat.template)

@router.message(QuickAddCat.template, F.photo)
async def process_quick_add_cat(message: Message, state: FSMContext, bot: Bot):
    caption = message.caption or ""

    name_match = re.search(r"Имя:\s*(.+)", caption, re.IGNORECASE)
    age_match = re.search(r"Возраст:\s*(.+)", caption, re.IGNORECASE)
    nat_match = re.search(r"Национальность:\s*(.+)", caption, re.IGNORECASE)
    city_match = re.search(r"Город:\s*(.+)", caption, re.IGNORECASE)
    price_w_match = re.search(r"Цена ходка:\s*(\d+)", caption, re.IGNORECASE)
    price_h_match = re.search(r"Цена час:\s*(\d+)", caption, re.IGNORECASE)
    price_n_match = re.search(r"Цена ночь:\s*(\d+)", caption, re.IGNORECASE)

    if not (name_match and age_match and nat_match and city_match and price_w_match and price_h_match and price_n_match):
        await message.answer("❌ <b>Ошибка формата!</b> Заполните согласно шаблону (Имя, Возраст, Национальность, Город, Цена ходка, Цена час, Цена ночь).")
        return

    name = name_match.group(1).strip()
    age = age_match.group(1).strip()
    nationality = nat_match.group(1).strip()
    city = city_match.group(1).strip().capitalize()
    price_walk = int(price_w_match.group(1))
    price_hour = int(price_h_match.group(1))
    price_night = int(price_n_match.group(1))
    photo_id = message.photo[-1].file_id

    matched_city = next((c for c in CITIES_RU if c.lower() == city.lower()), None)
    if not matched_city:
        await message.answer(f"❌ Город <b>'{city}'</b> не найден!\nДоступные: {', '.join(CITIES_RU)}")
        return

    channel_caption = (
        "╭────── 🐾 <b>ПРОФИЛЬ</b> ──────╮\n"
        "│\n"
        f"├─ 👤 <b>Имя:</b> <code>{name}</code>\n"
        f"├─ 🎂 <b>Возраст:</b> <code>{age}</code>\n"
        f"├─ 🌐 <b>Национальность:</b> <code>{nationality}</code>\n"
        "│\n"
        "├─ 💰 <b>Тарифы:</b>\n"
        f"│  ├─ 📌 <b>Ходка:</b> <code>{price_walk:,} сум</code>\n"
        f"│  ├─ ⏳ <b>1 час:</b> <code>{price_hour:,} сум</code>\n"
        f"│  └─ 🌌 <b>Ночь:</b> <code>{price_night:,} сум</code>\n"
        "│\n"
        "╰─────────────────────────╯\n\n"
        f"🏙 <b>Город:</b> #{matched_city}"
    )

    support_acc = await get_support_account()
    clean_username = support_acc.replace("@", "").replace("https://t.me/", "")
    channel_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💬 Написать / Связаться", url=f"https://t.me/{clean_username}")]
        ]
    )

    msg_id = None
    if CAT_CHANNEL_ID != 0:
        try:
            sent_msg = await bot.send_photo(
                chat_id=CAT_CHANNEL_ID,
                photo=photo_id,
                caption=channel_caption,
                reply_markup=channel_kb,
            )
            msg_id = sent_msg.message_id
        except Exception as e:
            logging.error(f"Ошибка публикации в канал: {e}")

    await db_add_cat(
        msg_id=msg_id or 0,
        photo=photo_id,
        name=name,
        age=age,
        nationality=nationality,
        city=matched_city,
        price_walk=price_walk,
        price_hour=price_hour,
        price_night=price_night,
    )
    await message.answer("✅ <b>Анкета котенка успешно добавлена!</b>", reply_markup=get_admin_main_kb())
    await state.clear()

@router.callback_query(F.data == "admin_del_cat")
async def start_del_cat(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("Введите <b>ID анкеты котенка</b> для удаления:", reply_markup=get_cancel_kb())
    await state.set_state(DeleteCat.message_id)

@router.message(DeleteCat.message_id)
async def process_del_cat(message: Message, state: FSMContext, bot: Bot):
    try:
        msg_id = int(message.text)
        if CAT_CHANNEL_ID != 0:
            try:
                await bot.delete_message(chat_id=CAT_CHANNEL_ID, message_id=msg_id)
            except Exception:
                pass
        await db_delete_cat(msg_id)
        await message.answer(f"✅ Анкета ID <code>{msg_id}</code> удалена!", reply_markup=get_admin_main_kb())
    except Exception as e:
        await message.answer(f"❌ Ошибка удаления: {e}")

    await state.clear()

@router.callback_query(F.data == "admin_list_cats")
async def admin_list_cats(callback: types.CallbackQuery):
    await callback.answer()
    all_cats = await db_get_all_cats()
    if not all_cats:
        await callback.message.answer("База анкет котят пуста.")
        return

    for cat in all_cats:
        cat_id = cat.msg_id or cat.id
        text = (
            f"🆔 <b>ID:</b> <code>{cat_id}</code>\n"
            f"🐱 <b>Имя:</b> {cat.name}\n"
            f"🌐 <b>Нац:</b> {cat.nationality or 'Не указано'}\n"
            f"🏙 <b>Город:</b> {cat.city}\n"
            f"💰 <b>Цены (ходка/час/ночь):</b> {cat.price_walk:,} / {cat.price_hour:,} / {cat.price_night:,} сум"
        )
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🗑 Удалить эту анкету", callback_data=f"quick_del_cat:{cat_id}")]]
        )
        await callback.message.answer_photo(photo=cat.photo, caption=text, reply_markup=kb)

@router.callback_query(F.data.startswith("quick_del_cat:"))
async def quick_del_cat(callback: types.CallbackQuery, bot: Bot):
    msg_id = int(callback.data.split(":")[1])
    if CAT_CHANNEL_ID != 0:
        try:
            await bot.delete_message(chat_id=CAT_CHANNEL_ID, message_id=msg_id)
        except Exception:
            pass

    await db_delete_cat(msg_id)
    await callback.answer("✅ Анкета успешно удалена!", show_alert=True)
    try:
        await callback.message.delete()
    except Exception:
        pass

# --- АДМИНКА КВАРТИРЫ ---

@router.callback_query(F.data == "admin_add_flat")
async def start_quick_add_flat(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    text = (
        "📸 <b>Шаг 1: Отправьте ФОТОГРАФИИ квартиры (от 1 до 10 штук).</b>\n\n"
        "Когда отправите все фото, напишите слово <b>ГОТОВО</b> в ответное сообщение."
    )
    await callback.message.answer(text, reply_markup=get_cancel_kb())
    await state.set_state(QuickAddFlat.photos)
    await state.update_data(photos=[])

@router.message(QuickAddFlat.photos, F.photo)
async def process_flat_photos_collect(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    await message.answer(f"✅ Фото добавлено! (Всего: {len(photos)}). Отправьте еще или напишите <b>ГОТОВО</b>.")

@router.message(QuickAddFlat.photos, F.text.lower() == "готово")
async def process_flat_photos_done(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])

    if not photos:
        await message.answer("❌ Вы не отправляли фотографии! Отправьте хотя бы 1 фото.", reply_markup=get_cancel_kb())
        return

    text = (
        "📝 <b>Шаг 2: Вставьте текстовое описание по шаблону:</b>\n\n"
        "<code>"
        "Название: Люкс 2-комнатная квартира\n"
        "Локация: Центр, ул. Амира Тимура 12\n"
        "Город: Ташкент\n"
        "Цена день: 500000"
        "</code>"
    )
    await message.answer(text, reply_markup=get_cancel_kb())
    await state.set_state(QuickAddFlat.template)

@router.message(QuickAddFlat.template)
async def process_quick_add_flat_template(message: Message, state: FSMContext):
    caption = message.text or ""
    data = await state.get_data()
    photos = data.get("photos", [])

    title_match = re.search(r"Название:\s*(.+)", caption, re.IGNORECASE)
    loc_match = re.search(r"Локация:\s*(.+)", caption, re.IGNORECASE)
    city_match = re.search(r"Город:\s*(.+)", caption, re.IGNORECASE)
    price_d_match = re.search(r"Цена день:\s*(\d+)", caption, re.IGNORECASE)

    if not (title_match and loc_match and city_match and price_d_match):
        await message.answer("❌ <b>Ошибка формата!</b> Заполните согласно шаблону (Название, Локация, Город, Цена день).")
        return

    title = title_match.group(1).strip()
    location = loc_match.group(1).strip()
    city = city_match.group(1).strip().capitalize()
    price_day = int(price_d_match.group(1))

    matched_city = next((c for c in CITIES_RU if c.lower() == city.lower()), None)
    if not matched_city:
        await message.answer(f"❌ Город <b>'{city}'</b> не найден!\nДоступные: {', '.join(CITIES_RU)}")
        return

    await db_add_flat(
        msg_id=0,
        photos=photos,
        title=title,
        location=location,
        city=matched_city,
        price_day=price_day
    )
    await message.answer("✅ <b>Объект квартиры успешно добавлен!</b>", reply_markup=get_admin_main_kb())
    await state.clear()

@router.callback_query(F.data == "admin_del_flat")
async def start_del_flat(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("Введите <b>ID объекта квартиры</b> для удаления:", reply_markup=get_cancel_kb())
    await state.set_state(DeleteFlat.message_id)

@router.message(DeleteFlat.message_id)
async def process_del_flat(message: Message, state: FSMContext):
    try:
        flat_id = int(message.text)
        await db_delete_flat(flat_id)
        await message.answer(f"✅ Квартира ID <code>{flat_id}</code> удалена!", reply_markup=get_admin_main_kb())
    except Exception as e:
        await message.answer(f"❌ Ошибка удаления: {e}")

    await state.clear()

@router.callback_query(F.data == "admin_edit_flat")
async def start_edit_flat(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("Введите <b>ID объекта квартиры</b>, который хотите изменить:", reply_markup=get_cancel_kb())
    await state.set_state(EditFlat.flat_id)

@router.message(EditFlat.flat_id)
async def process_edit_flat_id(message: Message, state: FSMContext):
    try:
        flat_id = int(message.text)
        flat = await db_get_flat_by_id(flat_id)
        if not flat:
            await message.answer("❌ Квартира с таким ID не найдена!", reply_markup=get_cancel_kb())
            return

        await state.update_data(flat_id=flat_id)
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="☀️ Цену за день", callback_data="edit_f_field:price_day"),
                    InlineKeyboardButton(text="📍 Локацию", callback_data="edit_f_field:location"),
                ],
                [
                    InlineKeyboardButton(text="📌 Название", callback_data="edit_f_field:title"),
                    InlineKeyboardButton(text="🏙 Город", callback_data="edit_f_field:city"),
                ],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_admin_action")],
            ]
        )
        await message.answer(
            f"Найдена квартира: <b>{flat['title']}</b> (Город: {flat['city']}, {flat['price_day']:,} сум/день)\n\nЧто хотите изменить?",
            reply_markup=kb,
        )
    except ValueError:
        await message.answer("Введите числовой ID!")

@router.callback_query(F.data.startswith("edit_f_field:"))
async def process_flat_field_choice(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    field = callback.data.split(":")[1]
    await state.update_data(field=field)

    field_names = {
        "price_day": "новую цену за день (только цифры)",
        "location": "новое описание локации",
        "title": "новое название квартиры",
        "city": f"новый город ({', '.join(CITIES_RU)})",
    }
    await callback.message.answer(f"Введите {field_names[field]}:", reply_markup=get_cancel_kb())
    await state.set_state(EditFlat.value)

@router.message(EditFlat.value)
async def process_edit_flat_value(message: Message, state: FSMContext):
    data = await state.get_data()
    flat_id = data["flat_id"]
    field = data["field"]
    value = message.text.strip()

    if field == "price_day":
        if not value.isdigit():
            await message.answer("❌ Ошибка! Цена должна состоять только из цифр.")
            return
        value = int(value)

    if field == "city":
        matched_city = next((c for c in CITIES_RU if c.lower() == value.lower()), None)
        if not matched_city:
            await message.answer(f"❌ Город должен быть из списка: {', '.join(CITIES_RU)}")
            return
        value = matched_city

    await db_update_flat_field(flat_id, field, value)
    await message.answer(f"✅ Квартира ID <code>{flat_id}</code> успешно обновлена!", reply_markup=get_admin_main_kb())
    await state.clear()

@router.callback_query(F.data == "admin_list_flats")
async def admin_list_flats(callback: types.CallbackQuery):
    await callback.answer()
    all_flats = await db_get_all_flats()
    if not all_flats:
        await callback.message.answer("База квартир пуста.")
        return

    for flat in all_flats:
        flat_id = flat.msg_id or flat.id
        photos_list = [p.strip() for p in flat.photos.split(",") if p.strip()] if flat.photos else []
        first_photo = photos_list[0] if photos_list else "https://via.placeholder.com/300"
        
        text = (
            f"🆔 <b>ID:</b> <code>{flat_id}</code>\n"
            f"📌 <b>Название:</b> {flat.title}\n"
            f"📍 <b>Локация:</b> {flat.location}\n"
            f"🏙 <b>Город:</b> {flat.city}\n"
            f"☀️ <b>Цена за день:</b> {flat.price_day:,} сум"
        )
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🗑 Удалить эту квартиру", callback_data=f"quick_del_flat:{flat_id}")]]
        )
        await callback.message.answer_photo(photo=first_photo, caption=text, reply_markup=kb)

@router.callback_query(F.data.startswith("quick_del_flat:"))
async def quick_del_flat(callback: types.CallbackQuery):
    flat_id = int(callback.data.split(":")[1])
    await db_delete_flat(flat_id)
    await callback.answer("✅ Квартира успешно удалена!", show_alert=True)
    try:
        await callback.message.delete()
    except Exception:
        pass
