import re
import asyncio
from telethon import TelegramClient, events

# ====== SOZLAMALAR ======
api_id = 22731419
api_hash = '2e2a9ce500a5bd08bae56f6ac2cc4890'
SESSION_NAME = 'taxi_session'
target_chat = '@rozimuhammadTaxi'

# Telegram client (ko‘p worker bilan)
client = TelegramClient(SESSION_NAME, api_id, api_hash, workers=50)

# Kalit so‘zlar (o‘zbekcha + ruscha)
keywords = [
    'odam bor', 'odam bor 1', 'odam bor 1ta', 'odam bor 1 ta',
    'tortta odam bor', "to'rtta odam bor", 'odambor', 'odam borakan', 'odam bor ekan',
    'bitta odam bor', 'ikkita odam bor', 'bita odam bor', 'ikta odam bor',
    'uchta odam bor', 'bir kamplekt odam bor', 'br kamplek odam bor', 'bir komplekt odam bor',
    'одам бор', 'одам бор 1', 'одам бор 1та', 'одам бор 1 та', 'тортта одам бор', "то'ртта одам бор",
    'odamboр', 'одам боракан', 'одам бор экан',
    'rishtonga odam bor', 'toshkentga odam bor', 'риштонга одам бор', 'тошкентга одам бор',
    'mashina kerak', 'mashina kere', 'mashina kerek', 'bagajli mashina kerak', 'bagajli mashina kere',
    'машина керак', 'машина керe', 'машина керек', 'багажли машина керак', 'багажли машина кере',
    'pochta bor', 'rishtonga pochta bor', 'rishtondan pochta bor', 'toshkentga pochta bor', 'toshkentdan pochta bor',
    'почта бор', 'риштонга почта бор', 'риштондан почта бор', 'тошкентга почта бор', 'тошкентдан почта бор',
    '1 kishi bor', '2 kishi bor', '3 kishi bor', '4 kishi bor',
    '1kishi bor', '2kishi bor', '3kishi bor', '4kishi bor',
    '2ta odam bor', 'odam bor 2 ta', '3ta odam bor', 'odam bor 3ta', 'odam bor 3 ta',
    '4ta odam bor', 'odam bor 4ta', 'odam bor 4 ta',
    'ketadi', 'ketishadi', 'ketishi kerak', 'ketishi', 'ayol kishi ketadi',
    'кeтaди', 'кeтишaди', 'кeтиши кeрaк', 'кeтиши', 'ayол киши кeтaди',
    'kampilek odam bor', 'kompilekt odam bor', 'komplek odam bor',
    'kampilek одам бор', 'kompilekt одам бор', 'komplek одам бор',
    'dastavka bor', 'dastafka', 'даставка бор', 'дастaфка',
    'mashina keraa', 'машина кераа'
]

# Set qilib olish → O(1) lookup
keywords_set = set(map(str.lower, keywords))

# Matnni tekshirish (lower + split)
def clean_text(text):
    return re.sub(r'\s+', ' ', text.strip().lower())

# ====== XABAR HANDLER ======
@client.on(events.NewMessage(incoming=True))
async def handler(event):
    try:
        if event.is_private or not event.raw_text:
            return

        text = event.raw_text.strip()          # asl xabar
        text_clean = clean_text(text)          # tekshirish uchun kichik harf
        text_words = set(text_clean.split())   # so‘zlarga bo‘lib setga olish

        # Agar keywords topilmasa, chiqish
        if not text_words.intersection(keywords_set):
            return

        # Xabar qayerdan kelganini aniqlash
        chat = await event.get_chat()
        if hasattr(chat, 'username') and chat.username:
            link = f"https://t.me/{chat.username}/{event.id}"
            name = chat.title or chat.username
            source_line = f"{name} ({link})"
        else:
            username = getattr(event.sender, 'username', None)
            source_line = f"@{username} (Link yo‘q)" if username else "Shaxsiy yoki yopiq guruh"

        # Yuborish (background task bilan) → keyingi xabarlar kutmaydi
        message_to_send = (
            f"🚖 <b>Xabar topildi!</b>\n\n"
            f"📄 <b>Matn:</b>\n{text}\n\n"
            f"📍 <b>Qayerdan:</b>\n{source_line}\n\n"
            f"🔔 <i>Yangiliklardan xabardor bo‘lib turing!</i>"
        )
        asyncio.create_task(client.send_message(target_chat, message_to_send, parse_mode='html'))
        print("✅ Yuborildi:", text[:60])

    except Exception as e:
        print("❌ Xatolik:", e)

# ====== BOTNI ISHGA TUSHURISH ======
print("🚕 Taxi bot ishga tushdi...")
client.start()
client.run_until_disconnected()
