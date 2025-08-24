import re
from telethon import TelegramClient, events

# API ma'lumotlari
api_id = 22731419
api_hash = '2e2a9ce500a5bd08bae56f6ac2cc4890'

# Telegram session
client = TelegramClient('taxi_session', api_id, api_hash)

# Kalit so‘zlar (faqat kichik harflarda)
keywords = [
    # Odam bor variantlari
    'odam bor', 'odam bor 1', 'odam bor 1ta', 'odam bor 1 ta',
    'tortta odam bor', "to'rtta odam bor", 'odambor', 'odam borakan', 'odam bor ekan',
    'bitta odam bor', 'ikkita odam bor', 'bita odam bor', 'ikta odam bor',
    'uchta odam bor', 'bir kamplekt odam bor', 'br kamplek odam bor', 'bir komplekt odam bor',

    # Ruscha o‘zbekcha yozilishlar
    'одам бор', 'одам бор 1', 'одам бор 1та', 'одам бор 1 та',
    'тортта одам бор', "то'ртта одам бор", 'одамбoр', 'одам боракан', 'одам бор экан',
    'битта одам бор', 'иккита одам бор', 'бита одам бор', 'икта одам бор',
    'учта одам бор', 'бир кampleкт одам бор', 'бр кampleк одам бор', 'бир комплект одам бор',

    # Rishton/Toshkentga odam bor
    'rishtonga odam bor', 'toshkentga odam bor',
    'риштонга одам бор', 'тошкентга одам бор',

    # Mashina kerak
    'mashina kerak', 'mashina kere', 'mashina kerek', 'bagajli mashina kerak', 'bagajli mashina kere',
    'машина керак', 'машина керe', 'машина керек', 'багажли машина керак', 'багажли машина кере',

    # Pochta bor
    'pochta bor', 'rishtonga pochta bor', 'rishtondan pochta bor', 'toshkentga pochta bor', 'toshkentdan pochta bor',
    'почта бор', 'риштонга почта бор', 'риштондан почта бор', 'тошкентга почта бор', 'тошкентдан почта бор',

    # Kishi soni bor
    '1 kishi bor', '2 kishi bor', '3 kishi bor', '4 kishi bor',
    '1kishi bor', '2kishi bor', '3kishi bor', '4kishi bor',
    '2ta odam bor', 'odam bor 2 ta', '3ta odam bor', 'odam bor 3ta', 'odam bor 3 ta',
    '4ta odam bor', 'odam bor 4ta', 'odam bor 4 ta',
    '1 киши бор', '2 киши бор', '3 киши бор', '4 киши бор',
    '1киши бор', '2киши бор', '3киши бор', '4киши бор',
    '2та одам бор', 'одам бор 2 та', '3та одам бор', 'одам бор 3та', 'одам бор 3 та',
    '4та одам бор', 'одам бор 4та', 'одам бор 4 та',

    # Ketadi
    'ketadi', 'ketishadi', 'ketishi kerak', 'ketishi', 'ayol kishi ketadi',
    'кeтaди', 'кeтишaди', 'кeтиши кeрaк', 'кeтиши', 'ayол киши кeтaди',

    # Kampilekt
    'kampilek odam bor', 'kompilekt odam bor', 'komplek odam bor',
    'kampilek одам бор', 'kompilekt одам бор', 'komplek одам бор',

    # Dastavka
    'dastavka bor', 'dastafka',
    'даставка бор', 'дастaфка',

    # Mashina kerak boshqa
    'mashina keraa', 'машина кераа',
]


# Xabar yuboriladigan kanal yoki chat
target_chat = '@rozimuhammadTaxi'


# Matnni tekshirish uchun tayyorlash
def clean_text(text):
    return re.sub(r'\s+', ' ', text.strip().lower())


@client.on(events.NewMessage(incoming=True))
async def handler(event):
    try:
        # Shaxsiy xabarlarni tashlab ketamiz
        if event.is_private or not event.raw_text:
            return

        text = event.raw_text.strip()           # Asl matn (yuborish uchun)
        text_clean = clean_text(text)           # Kichik harfga o'tkazilgan matn (tekshirish uchun)

        # Kalit so‘zlarni tekshirish (lower() bilan)
        if not any(k in text_clean for k in keywords):
            return

        # Xabar qayerdan kelganligini aniqlaymiz
        chat = await event.get_chat()
        if hasattr(chat, 'username') and chat.username:
            link = f"https://t.me/{chat.username}/{event.id}"
            name = chat.title or chat.username
            source_line = f"{name} ({link})"
        else:
            username = getattr(event.sender, 'username', None)
            source_line = f"@{username} (Link yo‘q)" if username else "Shaxsiy yoki yopiq guruh"

        # Yuboriladigan xabar (matn asl holatda chiqadi)
        message_to_send = (
            f"🚖 <b>Xabar topildi!</b>\n\n"
            f"📄 <b>Matn:</b>\n{text}\n\n"
            f"📍 <b>Qayerdan:</b>\n{source_line}\n\n"
            f"🔔 <i>Yangiliklardan xabardor bo‘lib turing!</i>"
        )

        await client.send_message(target_chat, message_to_send, parse_mode='html')
        print("✅ Yuborildi:", text[:60])

    except Exception as e:
        print("❌ Xatolik:", e)


print("🚕 Taxi bot ishga tushdi...")
client.start()
client.run_until_disconnected()
