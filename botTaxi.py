import re
from telethon import TelegramClient, events

# API ma'lumotlari
api_id = 22731419
api_hash = '2e2a9ce500a5bd08bae56f6ac2cc4890'

# Telegram session
client = TelegramClient('taxi_session', api_id, api_hash)

# Kalit so‘zlar
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

# Xabar yuboriladigan kanal
target_chat = '@rozimuhammadTaxi'

# Matnni tozalash
def clean_text(text):
    return re.sub(r'\s+', ' ', text.strip().lower())


@client.on(events.NewMessage(incoming=True))
async def handler(event):
    try:
        if event.is_private or not event.raw_text:
            return

        text = event.raw_text.strip()
        text_clean = clean_text(text)

        # Kalit so‘zlarni tekshirish
        if not any(k in text_clean for k in keywords):
            return

        # Chat va yuboruvchi haqida ma’lumot
        chat = await event.get_chat()
        sender = await event.get_sender()

        # Guruh nomi va link
        if hasattr(chat, 'username') and chat.username:
            source_line = f"{chat.title or chat.username} (https://t.me/{chat.username}/{event.id})"
        else:
            source_line = f"{chat.title or 'Shaxsiy yoki yopiq guruh'}"

        # Habar yuboruvchi username
        username = f"@{sender.username}" if sender.username else "Username yo‘q"

        # Telefon raqamni formatlash
        if getattr(sender, "phone", None):
            phone = sender.phone
            if not phone.startswith("+"):  # agar + bilan boshlanmagan bo‘lsa
                phone = f"+{phone}"
        else:
            phone = "Ko‘rinmaydi"

        # Yuboriladigan xabar
        message_to_send = (
            f"🚖 <b>Xabar topildi!</b>\n\n"
            f"📄 <b>Matn:</b>\n{text}\n\n"
            f"📍 <b>Qayerdan:</b>\n{source_line}\n\n"
            f"👤 <b>Habar yuboruvchi:</b> {username}\n"
            f"📞 <b>Telefon:</b> {phone}\n\n"
            f"🔔 <i>Yangiliklardan xabardor bo‘lib turing!</i>"
        )

        await client.send_message(target_chat, message_to_send, parse_mode='html')
        print("✅ Yuborildi:", text[:60])

    except Exception as e:
        print("❌ Xatolik:", e)


print("🚕 Taxi bot ishga tushdi...")
client.start()
client.run_until_disconnected()
