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

CITIES_RU = [
    "Ташкент", "Самарканд", "Бухара", "Наманган", "Андижан",
    "Фергана", "Карши", "Термез", "Навои", "Нукус",
    "Ургенч", "Джизак", "Гулистан"
]

CITIES_UZ = [
    "Toshkent", "Samarqand", "Buxoro", "Namangan", "Andijon",
    "Farg'ona", "Qarshi", "Termiz", "Navoiy", "Nukus",
    "Urganch", "Jizzax", "Guliston"
]

CITY_MAP_UZ_TO_RU = dict(zip(CITIES_UZ, CITIES_RU))
CITY_MAP_RU_TO_UZ = dict(zip(CITIES_RU, CITIES_UZ))

TEXTS = {
    "ru": {
        "welcome": "Здравствуйте! Выберите язык / Assalomu alaykum! Tilni tanlang:",
        "reg_name": "Привет! Добро пожаловать в сервис аренды 🏠🐱\n\nВведите ваше <b>имя</b>:",
        "reg_phone": "Приятно познакомиться, {name}! Нажмите кнопку ниже, чтобы отправить номер телефона:",
        "btn_phone": "📱 Поделиться номером",
        "reg_city": "Отлично! Теперь выберите ваш город:",
        "reg_success": "Регистрация успешно завершена! 🎉",
        "main_find": "🐱 Найти котенка",
        "main_find_flat": "🏠 Найти квартиру",
        "main_profile": "👤 Мой профиль",
        "btn_support": "💬 Поддержка",
        "welcome_back": "С возвращением, {name}! 👋",
        "select_city": "Выберите город для поиска:",
        "no_cats": "😔 В городе <b>{city}</b> пока нет свободных котят.",
        "no_flats": "😔 В городе <b>{city}</b> пока нет свободных квартир.",
        "btn_order": "🛒 Заказать",
        "btn_contact": "💬 Написать",
        "btn_back_cities": "🏙 Выбрать другой город",
        "btn_change_lang": "🌐 Изменить язык / Tilni o'zgartirish",
        "lang_changed": "Язык успешно изменен на Русский! 🇷🇺",
        "deposit_btn": "💳 Пополнить баланс",
        "deposit_disabled": "Функция пополнения баланса временно недоступна.",
        "order_success": "✅ Ваш заказ принят! Менеджер свяжется с вами в ближайшее время.",
        "nav_prev": "⬅️ Назад",
        "nav_next": "Вперед ➡️",
        "btn_back": "🔙 Назад",
        "currency": "сум",
        "main_menu_title": "Главное меню",
        "not_registered": "⛔ Для доступа к функциям бота необходимо пройти регистрацию. Нажмите /start",
        "support_text": "💬 <b>Служба поддержки</b>\n\nЕсли у вас возникли вопросы, напишите нашему оператору:\n👉 <b>{support}</b>",
        "support_btn": "✉️ Написать оператору",
        "profile": (
            "👤 <b>Ваш профиль:</b>\n\n"
            "▫️ <b>Имя:</b> {name}\n"
            "▫️ <b>Телефон:</b> +{phone}\n"
            "▫️ <b>Город:</b> {city}\n"
            "▫️ <b>Язык:</b> {lang}\n"
            "💰 <b>Баланс:</b> {balance:,} сум\n"
            "🆔 <b>ID:</b> <code>{user_id}</code>"
        ),
        "cat_card": (
            "╭────── 🐾 <b>ПРОФИЛЬ</b> ──────╮\n"
            "│\n"
            "├─ 👤 <b>Имя:</b> <code>{name}</code>\n"
            "├─ 🎂 <b>Возраст:</b> <code>{age}</code>\n"
            "├─ 🌐 <b>Национальность:</b> <code>{nationality}</code>\n"
            "│\n"
            "├─ 💰 <b>Тарифы:</b>\n"
            "│  ├─ 📌 <b>Ходка:</b> <code>{price_walk:,} сум</code>\n"
            "│  ├─ ⏳ <b>1 час:</b> <code>{price_hour:,} сум</code>\n"
            "│  └─ 🌌 <b>Ночь:</b> <code>{price_night:,} сум</code>\n"
            "│\n"
            "╰─────────────────────────╯\n\n"
            "🏙 <b>Город:</b> #{city}"
        ),
        "flat_card": (
            "╭────── 🏠 <b>КВАРТИРА</b> ──────╮\n"
            "│\n"
            "├─ 📌 <b>Название:</b> <code>{title}</code>\n"
            "├─ 📍 <b>Локация:</b> <code>{location}</code>\n"
            "│\n"
            "├─ 💰 <b>Тариф:</b>\n"
            "│  └─ ☀️ <b>Сутки (День):</b> <code>{price_day:,} сум</code>\n"
            "│\n"
            "╰─────────────────────────╯\n\n"
            "🏙 <b>Город:</b> #{city}"
        ),
    },
    "uz": {
        "welcome": "Assalomu alaykum! Tilni tanlang / Здравствуйте! Выберите язык:",
        "reg_name": "Xush kelibsiz! Ijara xizmati 🏠🐱\n\nIltimos, <b>ismingizni</b> kiriting:",
        "reg_phone": "Tanishganimdan xursandman, {name}! Telefon raqamingizni yuborish uchun pastdagi tugmani bosing:",
        "btn_phone": "📱 Telefon raqamni yuborish",
        "reg_city": "Ajoyib! Endi shahringizni tanlang:",
        "reg_success": "Ro'yxatdan o'tish muvaffaqiyatli yakunlandi! 🎉",
        "main_find": "🐱 Mushukcha topish",
        "main_find_flat": "🏠 Xonadon topish",
        "main_profile": "👤 Mening profilim",
        "btn_support": "💬 Qo'llab-quvvatlash",
        "welcome_back": "Qaytganingizdan xursandmiz, {name}! 👋",
        "select_city": "Qidirish uchun shaharni tanlang:",
        "no_cats": "😔 <b>{city}</b> shahrida hozircha bo'sh mushukchalar yo'q.",
        "no_flats": "😔 <b>{city}</b> shahrida hozircha bo'sh xonadonlar yo'q.",
        "btn_order": "🛒 Buyurtma berish",
        "btn_contact": "💬 Bog'lanish",
        "btn_back_cities": "🏙 Boshqa shaharni tanlash",
        "btn_change_lang": "🌐 Tilni o'zgartirish / Изменить язык",
        "lang_changed": "Til muvaffaqiyatli O'zbek tiliga o'zgartirildi! 🇺🇿",
        "deposit_btn": "💳 Balansni to'ldirish",
        "deposit_disabled": "Balansni to'ldirish funksiyasi vaqtincha ishlamayapti.",
        "order_success": "✅ Buyurtmangiz qabul qilindi! Menejer tez orada siz bilan bog'lanadi.",
        "nav_prev": "⬅️ Orqaga",
        "nav_next": "Oldingi ➡️",
        "btn_back": "🔙 Orqaga",
        "currency": "so'm",
        "main_menu_title": "Bosh menyu",
        "not_registered": "⛔ Barcha imkoniyatlardan foydalanish uchun ro'yxatdan o'ting. /start bosing",
        "support_text": "💬 <b>Qo'llab-quvvatlash xizmati</b>\n\nSavollaringiz bo'lsa, operatorimizga yozing:\n👉 <b>{support}</b>",
        "support_btn": "✉️ Operatorga yozish",
        "profile": (
            "👤 <b>Sizning profilingiz:</b>\n\n"
            "▫️ <b>Ism:</b> {name}\n"
            "▫️ <b>Telefon:</b> +{phone}\n"
            "▫️ <b>Shahar:</b> {city}\n"
            "▫️ <b>Til:</b> {lang}\n"
            "💰 <b>Balans:</b> {balance:,} so'm\n"
            "🆔 <b>ID:</b> <code>{user_id}</code>"
        ),
        "cat_card": (
            "╭────── 🐾 <b>PROFIL</b> ──────╮\n"
            "│\n"
            "├─ 👤 <b>Ism:</b> <code>{name}</code>\n"
            "├─ 🎂 <b>Yoshi:</b> <code>{age}</code>\n"
            "├─ 🌐 <b>Millati:</b> <code>{nationality}</code>\n"
            "│\n"
            "├─ 💰 <b>Tariflar:</b>\n"
            "│  ├─ 📌 <b>Xotka:</b> <code>{price_walk:,} so'm</code>\n"
            "│  ├─ ⏳ <b>1 soat:</b> <code>{price_hour:,} so'm</code>\n"
            "│  └─ 🌌 <b>Bir kecha:</b> <code>{price_night:,} so'm</code>\n"
            "│\n"
            "╰─────────────────────────╯\n\n"
            "🏙 <b>Shahar:</b> #{city}"
        ),
        "flat_card": (
            "╭────── 🏠 <b>XONADON</b> ──────╮\n"
            "│\n"
            "├─ 📌 <b>Nomi:</b> <code>{title}</code>\n"
            "├─ 📍 <b>Joylashuv:</b> <code>{location}</code>\n"
            "│\n"
            "├─ 💰 <b>Tarif:</b>\n"
            "│  └─ ☀️ <b>Bir kun:</b> <code>{price_day:,} so'm</code>\n"
            "│\n"
            "╰─────────────────────────╯\n\n"
            "🏙 <b>Shahar:</b> #{city}"
        ),
    },
}
