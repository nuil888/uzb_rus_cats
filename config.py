import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "1001")

raw_admin_ids = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(i.strip()) for i in raw_admin_ids.split(",") if i.strip().isdigit()]

USERS_CHANNEL_ID = int(os.getenv("USERS_CHANNEL_ID", "0"))
CAT_CHANNEL_ID = int(os.getenv("CAT_CHANNEL_ID", "0"))

RAW_DB_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///bot.db")

if RAW_DB_URL.startswith("postgres://"):
    DB_URL = RAW_DB_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif RAW_DB_URL.startswith("postgresql://") and not RAW_DB_URL.startswith("postgresql+asyncpg://"):
    DB_URL = RAW_DB_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    DB_URL = RAW_DB_URL


# Города
CITIES_RU = [
    "🌹 Ташкент",
    "✨ Самарканд",
    "💎 Бухара",
    "🌸 Наманган",
    "🔥 Андижан",
    "🌙 Фергана",
    "💫 Карши",
    "🌺 Термез",
    "⭐ Навои",
    "🦋 Нукус",
    "🏙 Ургенч",
    "🌷 Джизак",
    "💖 Гулистан"
]


CITIES_UZ = [
    "🌹 Toshkent",
    "✨ Samarqand",
    "💎 Buxoro",
    "🌸 Namangan",
    "🔥 Andijon",
    "🌙 Farg'ona",
    "💫 Qarshi",
    "🌺 Termiz",
    "⭐ Navoiy",
    "🦋 Nukus",
    "🏙 Urganch",
    "🌷 Jizzax",
    "💖 Guliston"
]


CITY_MAP_UZ_TO_RU = dict(zip(CITIES_UZ, CITIES_RU))
CITY_MAP_RU_TO_UZ = dict(zip(CITIES_RU, CITIES_UZ))


TEXTS = {

    "ru": {

        "welcome":
        "🐾 Добро пожаловать в <b>«Котенки»</b>\n\n"
        "✨ Здесь начинается мир красивых эмоций,\n"
        "приятных встреч и особенного настроения.\n\n"
        "Выбери язык и познакомься с нами 💕",


        "reg_name":
        "🐱 Рады видеть тебя в <b>«Котенки»</b>\n\n"
        "Познакомимся поближе ✨\n"
        "Введите ваше <b>имя</b>:",


        "reg_phone":
        "💕 Очень приятно, {name}!\n\n"
        "Оставь свой номер телефона,\n"
        "чтобы мы могли быть с тобой на связи 🐾",


        "btn_phone":
        "📱 Отправить номер",


        "reg_city":
        "🌹 Отлично!\n\n"
        "Теперь выбери свой город.\n"
        "Там тебя ждут наши особенные котята ✨",


        "reg_success":
        "🎉 Регистрация завершена!\n\n"
        "Добро пожаловать в мир <b>«Котенки»</b> 🐾",


        "main_find":
        "🐱 Найти котенка",


        "main_find_flat":
        "🏡 Найти уютное место",


        "main_profile":
        "💎 Мой профиль",


        "btn_support":
        "💌 Помощь",


        "welcome_back":
        "✨ С возвращением, {name}!\n\n"
        "Твои котята уже ждут тебя 🐾",


        "select_city":
        "📍 Выбери город\n\n"
        "В каждом городе тебя ждут особенные знакомства ✨",


        "no_cats":
        "😿 В городе <b>{city}</b>\n"
        "сейчас нет доступных котят.\n\n"
        "Попробуй выбрать другой город 🐾",


        "no_flats":
        "🏡 В городе <b>{city}</b>\n"
        "пока нет доступных мест.\n\n"
        "Попробуй другой вариант ✨",


                "btn_order":
        "🐾 Выбрать котенка",


        "btn_contact":
        "💌 Связаться",


        "btn_back_cities":
        "🌍 Другой город",


        "btn_change_lang":
        "🌐 Сменить язык",


        "lang_changed":
        "✨ Язык изменён на Русский 🇷🇺",


        "deposit_btn":
        "💎 Пополнить баланс",


        "deposit_disabled":
        "🐾 Сейчас эта возможность недоступна.\n"
        "Попробуй немного позже ✨",


        "order_success":
        "💕 Отличный выбор!\n\n"
        "Твой запрос принят 🐾\n\n"
        "Наш менеджер скоро свяжется с тобой "
        "и поможет организовать всё красиво ✨",


        "nav_prev":
        "⬅️ Назад",


        "nav_next":
        "Дальше ➡️",


        "btn_back":
        "🔙 Вернуться",


        "currency":
        "сум",


        "main_menu_title":
        "🐾 Главное меню «Котенки»",


        "not_registered":
        "🐱 Чтобы открыть весь мир «Котенки»,\n"
        "нужно пройти небольшую регистрацию ✨\n\n"
        "Нажми /start",


        "support_text":
        "💌 <b>Мы рядом</b>\n\n"
        "Есть вопрос или нужна помощь?\n"
        "Наша команда поможет подобрать лучший вариант 🐾\n\n"
        "👉 <b>{support}</b>",


        "support_btn":
        "💌 Написать нам",


        "profile":
        (
            "💎 <b>Твой профиль</b>\n\n"
            "🐾 <b>Имя:</b> {name}\n"
            "📱 <b>Телефон:</b> +{phone}\n"
            "📍 <b>Город:</b> {city}\n"
            "🌐 <b>Язык:</b> {lang}\n\n"
            "💰 <b>Баланс:</b> {balance:,} сум\n"
            "🆔 <b>ID:</b> <code>{user_id}</code>\n\n"
            "✨ Здесь хранится твоя история в «Котенки»"
        ),


        "cat_card":
        (
            "╭────── 🐾 <b>КОТЕНОК</b> ──────╮\n"
            "│\n"
            "├─ 🌸 <b>Имя:</b> <code>{name}</code>\n"
            "├─ 🎂 <b>Возраст:</b> <code>{age}</code>\n"
            "├─ ✨ <b>Особенность:</b> <code>{nationality}</code>\n"
            "│\n"
            "├─ 💎 <b>Форматы:</b>\n"
            "│\n"
            "├─ 🐾 <b>Встреча:</b> <code>{price_walk:,} сум</code>\n"
            "├─ ⏳ <b>Час:</b> <code>{price_hour:,} сум</code>\n"
            "└─ 🌙 <b>Ночь:</b> <code>{price_night:,} сум</code>\n"
            "│\n"
            "╰─────────────────────────╯\n\n"
            "📍 <b>Город:</b> #{city}\n\n"
            "💕 Каждая встреча — это особенное настроение"
        ),


        "flat_card":
        (
            "╭────── 🏡 <b>УЮТНОЕ МЕСТО</b> ──────╮\n"
            "│\n"
            "├─ ✨ <b>Название:</b> <code>{title}</code>\n"
            "├─ 📍 <b>Локация:</b> <code>{location}</code>\n"
            "│\n"
            "├─ 💎 <b>Стоимость:</b>\n"
            "└─ ☀️ <b>День:</b> <code>{price_day:,} сум</code>\n"
            "│\n"
            "╰─────────────────────────╯\n\n"
            "📍 <b>Город:</b> #{city}\n\n"
            "✨ Атмосфера для красивых моментов"
        ),
    },


        "uz": {

        "welcome":
        "🐾 <b>«Mushukchalar»</b> olamiga xush kelibsiz\n\n"
        "✨ Bu yerda chiroyli hislar,\n"
        "yoqimli suhbatlar va maxsus lahzalar boshlanadi.\n\n"
        "Tilni tanlang va biz bilan tanishing 💕",


        "reg_name":
        "🐱 <b>«Mushukchalar»</b> sizni kutmoqda\n\n"
        "Keling, tanishamiz ✨\n"
        "<b>Ismingizni</b> kiriting:",


        "reg_phone":
        "💕 Juda xursandmiz, {name}!\n\n"
        "Siz bilan bog'lanishimiz uchun\n"
        "telefon raqamingizni yuboring 🐾",


        "btn_phone":
        "📱 Telefon raqamni yuborish",


        "reg_city":
        "🌸 Ajoyib!\n\n"
        "Endi shahringizni tanlang.\n"
        "U yerda sizni maxsus mushukchalar kutmoqda ✨",


        "reg_success":
        "🎉 Ro'yxatdan o'tish tugadi!\n\n"
        "<b>«Mushukchalar»</b> dunyosiga xush kelibsiz 🐾",


        "main_find":
        "🐱 Mushukcha topish",


        "main_find_flat":
        "🏡 Shinam joy topish",


        "main_profile":
        "💎 Mening profilim",


        "btn_support":
        "💌 Yordam",


        "welcome_back":
        "✨ Qaytganingizdan xursandmiz, {name}!\n\n"
        "Mushukchalaringiz sizni kutmoqda 🐾",


        "select_city":
        "📍 Shaharni tanlang\n\n"
        "Har bir shaharda sizni maxsus mushukchalar kutmoqda ✨",


        "no_cats":
        "😿 <b>{city}</b> shahrida\n"
        "hozircha mushukchalar mavjud emas.\n\n"
        "Boshqa shaharni tanlab ko'ring 🐾",


        "no_flats":
        "🏡 <b>{city}</b> shahrida\n"
        "hozircha joylar mavjud emas.\n\n"
        "Boshqa variantni sinab ko'ring ✨",


        "btn_order":
        "🐾 Mushukchani tanlash",


        "btn_contact":
        "💌 Bog'lanish",


        "btn_back_cities":
        "🌍 Boshqa shahar",


        "btn_change_lang":
        "🌐 Tilni almashtirish",


        "lang_changed":
        "✨ Til o'zbek tiliga o'zgartirildi 🇺🇿",


        "deposit_btn":
        "💎 Balansni to'ldirish",


        "deposit_disabled":
        "🐾 Hozircha bu imkoniyat mavjud emas.\n"
        "Keyinroq urinib ko'ring ✨",


        "order_success":
        "💕 Ajoyib tanlov!\n\n"
        "So'rovingiz qabul qilindi 🐾\n\n"
        "Menejerimiz tez orada siz bilan bog'lanadi "
        "va barcha tafsilotlarni tushuntiradi ✨",


        "nav_prev":
        "⬅️ Orqaga",


        "nav_next":
        "Oldinga ➡️",


        "btn_back":
        "🔙 Qaytish",


        "currency":
        "so'm",


        "main_menu_title":
        "🐾 «Mushukchalar» menyusi",


        "not_registered":
        "🐱 Barcha imkoniyatlarni ochish uchun\n"
        "kichik ro'yxatdan o'tishni yakunlang ✨\n\n"
        "/start ni bosing",


        "support_text":
        "💌 <b>Biz doimo yoningizdamiz</b>\n\n"
        "Savollaringiz bo'lsa yoki yordam kerak bo'lsa,\n"
        "jamoamiz sizga yordam beradi 🐾\n\n"
        "👉 <b>{support}</b>",


        "support_btn":
        "💌 Bizga yozish",


        "profile":
        (
            "💎 <b>Sizning profilingiz</b>\n\n"
            "🐾 <b>Ism:</b> {name}\n"
            "📱 <b>Telefon:</b> +{phone}\n"
            "📍 <b>Shahar:</b> {city}\n"
            "🌐 <b>Til:</b> {lang}\n\n"
            "💰 <b>Balans:</b> {balance:,} so'm\n"
            "🆔 <b>ID:</b> <code>{user_id}</code>\n\n"
            "✨ Sizning «Mushukchalar» tarixingiz shu yerda"
        ),


        "cat_card":
        (
            "╭────── 🐾 <b>MUSHUKCHA</b> ──────╮\n"
            "│\n"
            "├─ 🌸 <b>Ism:</b> <code>{name}</code>\n"
            "├─ 🎂 <b>Yoshi:</b> <code>{age}</code>\n"
            "├─ ✨ <b>Xususiyati:</b> <code>{nationality}</code>\n"
            "│\n"
            "├─ 💎 <b>Formatlar:</b>\n"
            "│\n"
            "├─ 🐾 <b>Uchrashuv:</b> <code>{price_walk:,} so'm</code>\n"
            "├─ ⏳ <b>Bir soat:</b> <code>{price_hour:,} so'm</code>\n"
            "└─ 🌙 <b>Tun:</b> <code>{price_night:,} so'm</code>\n"
            "│\n"
            "╰─────────────────────────╯\n\n"
            "📍 <b>Shahar:</b> #{city}\n\n"
            "💕 Har bir lahza o'zgacha bo'lishi mumkin"
        ),


        "flat_card":
        (
            "╭────── 🏡 <b>SHINAM JOY</b> ──────╮\n"
            "│\n"
            "├─ ✨ <b>Nomi:</b> <code>{title}</code>\n"
            "├─ 📍 <b>Joylashuv:</b> <code>{location}</code>\n"
            "│\n"
            "├─ 💎 <b>Narxi:</b>\n"
            "└─ ☀️ <b>Bir kun:</b> <code>{price_day:,} so'm</code>\n"
            "│\n"
            "╰─────────────────────────╯\n\n"
            "📍 <b>Shahar:</b> #{city}\n\n"
            "✨ Chiroyli lahzalar uchun maxsus atmosfera"
        ),
    },
}
