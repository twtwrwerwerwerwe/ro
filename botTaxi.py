import re
from telethon import TelegramClient, events

# API ma'lumotlari
api_id = 28023612
api_hash = 'fe94ef46addc1b6b8253d5448e8511f0'

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
    'машина керак', 'машина керe', 'машина нужен', 'багажли машина керак', 'багажли машина кере',

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
    'mashina keraa', 'машина кераа', 'Toshkentdan Qoqonga odam bor', "Toshkendan Qo'qonga odam bor", 
    "Toshkentdan Fargonaga odam bor", "Toshkentdan Farg'onaga odam bor", 
    "Toshkendan Fargonaga odam bor", "Bosh mashina kerak", "Bosh mashina bormikan", "Boshi bormikan" 
]

# Xabar yuboriladigan kanal yoki chat
target_chat = 'https://t.me/+BFl15wH-PAswZTYy'

# Matnni tekshirish uchun tayyorlash
def clean_text(text):
    return re.sub(r'\s+', ' ', text.strip().lower())

# Matndan raqam topish (turli formatlarga mos)
def find_phone_in_text(text):
    # turli formatlarni qamrab oluvchi regex:
    # misollar: +998901234567, 90 123 45 67, 90-123-45-67, 901234567, 998901234567
    patterns = [
        r'\+?998[\s\-\.\(]*\d{2}[\s\-\.\)]*\d{3}[\s\-\.\)]*\d{2}[\s\-\.\)]*\d{2}',  # +998 90 123 45 67
        r'\b\d{2}[\s\-\.\)]*\d{3}[\s\-\.\)]*\d{2}[\s\-\.\)]*\d{2}\b',            # 90 123 45 67 or 901234567
        r'\b\d{9}\b'                                                              # 901234567
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            num = re.sub(r'\D', '', m.group())
            # agar 12 ta raqam (998901234567) bo'lsa +998... shakliga o'tkazamiz
            if num.startswith('998') and len(num) >= 12:
                return f"+{num[:12]}"
            # agar 9 ta (901234567) bo'lsa +998 qo'shamiz
            if len(num) == 9:
                return f"+998{num}"
            # agar 11-12 ta boshqa shakl bo'lsa ham + qo'shamiz
            if len(num) >= 10:
                return f"+{num}"
    return None


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
            group_line = f"Guruh linki: {link} ({chat.title})"
        else:
            group_line = "Guruh linki: Berkitilgan"

        # Username va telefon raqamini olish
        sender = await event.get_sender()
        username = getattr(sender, 'username', None)
        phone = getattr(sender, 'phone', None)
        sender_id = getattr(sender, 'id', None)

        # Agar senderda raqam yoki username yo‘q bo‘lsa — matndan qidiramiz
        text_phone = find_phone_in_text(text)

        username_str = f"@{username}" if username else "Berkitilgan"
        phone_str = f"+{phone}" if phone else (text_phone if text_phone else "Raqam berkitilgan")

        # **Eslatma:** endi har doim xabar yuboriladi (even if username/phone/text_phone missing)
        # Maxsus link — agar sender_id bo'lsa, klikli link; bo'lmasa "Berkitilgan" yozuvi chiqadi
        if sender_id:
            special_link = f'<b>🔗 Maxsus link:</b> <a href="tg://user?id={sender_id}">User bilan bog‘lanish</a>'
        else:
            special_link = '<b>🔗 Maxsus link:</b> Berkitilgan'

        # Yuboriladigan xabar
        message_to_send = (
            f"🚖 <b>Xabar topildi!</b>\n\n"
            f"📄 <b>Matn:</b>\n{text}\n\n"
            f"📍 <b>{group_line}</b>\n\n"
            f"👤 <b>Habar egasi:</b> {username_str}\n\n"
            f"📞 <b>Habar egasi raqami:</b> {phone_str}\n\n"
            f"{special_link}\n\n"
            f"🔔 <i>Yangiliklardan xabardor bo‘lib turing!</i>"
        )

        await client.send_message(target_chat, message_to_send, parse_mode='html')
        print("✅ Yuborildi:", text[:60])

    except Exception as e:
        print("❌ Xatolik:", e)


print("🚕 Taxi bot ishga tushdi...")
client.start()
client.run_until_disconnected()
