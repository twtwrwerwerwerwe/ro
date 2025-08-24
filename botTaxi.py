import re
from telethon import TelegramClient, events

# API ma'lumotlari
api_id = 22731419
api_hash = '2e2a9ce500a5bd08bae56f6ac2cc4890'

# Telegram session
client = TelegramClient('taxi_session', api_id, api_hash)

# Kalit so‘zlar (kichik harflarda)
keywords = set(map(str.lower, [
    'odam bor', 'odam bor 1', 'odam bor 1ta', 'odam bor 1 ta',
    'rishtonga odam bor', 'toshkentga odam bor',
    'pochta bor', 'rishtonga pochta bor', 'rishtondan pochta bor',
    'toshkentga pochta bor', 'toshkentdan pochta bor',
    'ketadi', 'ketishadi', 'ketishi kerak', 'ketishi', 'ayol kishi ketadi',
    'mashina kerak', 'mashina kere', 'mashina kerek',
    'kampilek odam bor', 'kompilekt odam bor', 'komplek odam bor',
    'одам бор', 'одам бор 1', 'одам бор 1та', 'одам бор 1 та',
    'риштонга одам бор', 'тошкентга одам бор',
    'почта бор', 'риштонга почта бор', 'риштондон почта бор',
    'тошкентга почта бор', 'тошкентдан почта бор',
    'кетади', 'кетишади', 'кетиши керак', 'кетиши', 'айол киши кетади',
    'машина керак', 'машина кере', 'машина керек',
    'кампилек одам бор', 'компилект одам бор', 'комплек одам бор'
]))

# Xabar yuboriladigan kanal yoki chat
target_chat = '@rozimuhammadTaxi'


# Matnni tozalash (faqat kalit so‘zlarni qidirishda)
def clean_text(text):
    return re.sub(r'\s+', ' ', text.strip().lower())


@client.on(events.NewMessage(incoming=True))
async def handler(event):
    try:
        # Shaxsiy xabarlarni tashlab ketamiz
        if event.is_private or not event.raw_text:
            return

        text = event.raw_text.strip()
        text_clean = clean_text(text)

        # Kalit so‘zlarni tekshirish
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

        # Yuboriladigan xabar
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
