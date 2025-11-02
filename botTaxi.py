import re
from telethon import TelegramClient, events

# === API ma'lumotlari ===
api_id = 28023612
api_hash = 'fe94ef46addc1b6b8253d5448e8511f0'

# === Session nomi ===
client = TelegramClient('taxi_session', api_id, api_hash)

# === Xabar yuboriladigan kanal ===
TARGET_CHAT = 'https://t.me/+BFl15wH-PAswZTYy'

# === Kalit so‘zlar (to‘liq ro‘yxat) ===
KEYWORDS = [
    # Odam bor
    'odam bor', 'odam bor 1', 'odam bor 1ta', 'odam bor 1 ta',
    'tortta odam bor', "to'rtta odam bor", 'odambor', 'odam borakan', 'odam bor ekan',
    'bitta odam bor', 'ikkita odam bor', 'bita odam bor', 'ikta odam bor',
    'uchta odam bor', 'bir kamplekt odam bor', 'br kamplek odam bor', 'bir komplekt odam bor',
    'odam bor 2ta', 'odam bor 2 ta', 'odam bor 3ta', 'odam bor 3 ta', 'odam bor 4ta', 'odam bor 4 ta',
    '2ta odam bor', '3ta odam bor', '4ta odam bor',

    # Ruscha / kirillcha
    'одам бор', 'одам бор 1', 'одам бор 1та', 'одам бор 1 та',
    'тортта одам бор', "то'ртта одам бор", 'одамбoр', 'одам боракан', 'одам бор экан',
    'битта одам бор', 'иккита одам бор', 'бита одам бор', 'икта одам бор',
    'учта одам бор', 'бир комплект одам бор', 'бр комплект одам бор',
    'одам бор 2 та', 'одам бор 3 та', 'одам бор 4 та',
    '2та одам бор', '3та одам бор', '4та одам бор',
    'одам бор 2та', 'одам бор 3та', 'одам бор 4та',

    # Yo‘nalishlar
    'rishtonga odam bor', 'toshkentga odam bor',
    'риштонга одам бор', 'тошкентга одам бор',

    # Mashina kerak
    'mashina kerak', 'mashina kere', 'mashina kerek', 'bagajli mashina kerak', 'bagajli mashina kere',
    'машина керак', 'машина керe', 'машина нужен', 'багажли машина керак', 'багажли машина кере',
    'mashina keraa', 'машина кераа', 'bosh mashina kerak', 'bosh mashina bormikan', 'boshi bormikan',

    # Pochta
    'pochta bor', 'rishtonga pochta bor', 'rishtondan pochta bor', 'toshkentga pochta bor', 'toshkentdan pochta bor',
    'почта бор', 'риштонга почта бор', 'риштондан почта бор', 'тошкентга почта бор', 'тошкентдан почта бор',

    # Kishilar soni
    '1 kishi bor', '2 kishi bor', '3 kishi bor', '4 kishi bor',
    '1kishi bor', '2kishi bor', '3kishi bor', '4kishi bor',
    '1 киши бор', '2 киши бор', '3 киши бор', '4 киши бор',
    '1киши бор', '2киши бор', '3киши бор', '4киши бор',

    # Yo‘lga chiqish
    'ketadi', 'ketishadi', 'ketishi kerak', 'ketishi', 'ayol kishi ketadi',
    'кeтaди', 'кeтишaди', 'кeтиши кeрaк', 'кeтиши', 'ayол киши кeтaди',

    # Komplekt odamlar
    'kampilek odam bor', 'kompilekt odam bor', 'komplek odam bor',
    'kampilek одам бор', 'kompilekt одам бор', 'komplek одам бор',

    # Dastavka
    'dastavka bor', 'dastafka', 'даставка бор', 'дастaфка',

    # Maxsus yo‘nalishlar
    'toshkentdan qoqonga odam bor', "toshkendan qo'qonga odam bor",
    "toshkentdan fargonaga odam bor", "toshkentdan farg'onaga odam bor",
    "toshkendan fargonaga odam bor"
]

# === Matnni tozalovchi funksiya ===
def clean_text(text: str):
    return re.sub(r'\s+', ' ', text.lower().strip())

# === Raqamni aniqlovchi funksiya ===
def find_phone_in_text(text: str):
    patterns = [
        r'\+?998[\s\-\.\(]*\d{2}[\s\-\.\)]*\d{3}[\s\-\.\)]*\d{2}[\s\-\.\)]*\d{2}',
        r'\b\d{2}[\s\-\.\)]*\d{3}[\s\-\.\)]*\d{2}[\s\-\.\)]*\d{2}\b',
        r'\b\d{9}\b'
    ]
    for p in patterns:
        match = re.search(p, text)
        if match:
            num = re.sub(r'\D', '', match.group())
            if num.startswith('998') and len(num) >= 12:
                return f"+{num[:12]}"
            if len(num) == 9:
                return f"+998{num}"
            if len(num) >= 10:
                return f"+{num}"
    return None

# === Faqat yangi xabarlarni filtrlash ===
@client.on(events.NewMessage(incoming=True))
async def filter_new_messages(event):
    try:
        if event.is_private or not event.raw_text:
            return

        text_clean = clean_text(event.raw_text)
        if not any(k in text_clean for k in KEYWORDS):
            return

        chat = await event.get_chat()
        chat_name = getattr(chat, 'title', 'Noma’lum guruh')

        if getattr(chat, 'username', None):
            msg_link = f"https://t.me/{chat.username}/{event.id}"
        else:
            msg_link = "Berkitilgan"

        sender = await event.get_sender()
        username = getattr(sender, 'username', None)
        sender_id = getattr(sender, 'id', None)
        text_phone = find_phone_in_text(event.raw_text)

        username_str = f"@{username}" if username else "Berkitilgan"
        phone_str = text_phone if text_phone else "Raqam topilmadi"
        user_link = f'<a href="tg://user?id={sender_id}">Bog‘lanish</a>' if sender_id else "Berkitilgan"

        message = (
            f"🚖 <b>Yangi xabar topildi!</b>\n\n"
            f"📄 <b>Matn:</b>\n{event.raw_text}\n\n"
            f"📍 <b>Guruh:</b> {chat_name}\n"
            f"🔗 <b>Xabar linki:</b> {msg_link}\n\n"
            f"👤 <b>Yuboruvchi:</b> {username_str}\n"
            f"📞 <b>Raqam:</b> {phone_str}\n"
            f"🧩 <b>Maxsus link:</b> {user_link}"
        )

        await client.send_message(TARGET_CHAT, message, parse_mode='html')
        print(f"✅ Yangi mos xabar yuborildi: {event.raw_text[:60]}...")

    except Exception as e:
        print("❌ Xatolik:", e)

print("🚕 Taxi bot ishga tushdi (faqat yangi xabarlar uchun)...")
client.start()
client.run_until_disconnected()
