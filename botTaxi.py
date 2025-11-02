# botTaxi.py
# -*- coding: utf-8 -*-

import re
import asyncio
# Windows uchun event loop muammosini hal qilamiz (Windowsda Python 3.10+ uchun kerak bo'ladi)
try:
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
except Exception:
    # agar WindowsSelectorEventLoopPolicy mavjud bo'lmasa yoki boshqa OS bo'lsa, o'tib ketamiz
    pass

from telethon import TelegramClient, events

# === API ma'lumotlari ===
api_id = 28023612
api_hash = 'fe94ef46addc1b6b8253d5448e8511f0'

# === Session nomi ===
client = TelegramClient('taxi_session', api_id, api_hash)

# === Xabar yuboriladigan kanal ===
target_chat = 'https://t.me/+BFl15wH-PAswZTYy'

# === To'liq kalit so'zlar ro'yxati (siz bergan barcha variantlar) ===
KEYWORDS = [
    # Odam bor variantlari
    'odam bor', 'odam bor 1', 'odam bor 1ta', 'odam bor 1 ta',
    'tortta odam bor', "to'rtta odam bor", 'odambor', 'odam borakan', 'odam bor ekan',
    'bitta odam bor', 'ikkita odam bor', 'bita odam bor', 'ikta odam bor',
    'uchta odam bor', 'bir kamplekt odam bor', 'br kamplek odam bor', 'bir komplekt odam bor',

    # Ruscha o‘zbekcha yozilishlar (kirillcha/variantlar)
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
    'mashina keraa', 'машина кераа', 'toshkentdan qoqonga odam bor', "toshkendan qo'qonga odam bor",
    "toshkentdan fargonaga odam bor", "toshkentdan farg'onaga odam bor",
    "toshkendan fargonaga odam bor", "bosh mashina kerak", "bosh mashina bormikan", "boshi bormikan"
]

# Lowercase qilingan KEYWORDS set — tekshirish tezligi uchun
KEYWORDS_SET = set(k.lower() for k in KEYWORDS)

# === Telefon raqamini topish uchun regexlarni oldindan kompilyatsiya qilamiz ===
PHONE_PATTERNS = [
    re.compile(r'\+?998[\s\-\.\(]*\d{2}[\s\-\.\)]*\d{3}[\s\-\.\)]*\d{2}[\s\-\.\)]*\d{2}'),  # +998 90 123 45 67
    re.compile(r'\b\d{2}[\s\-\.\)]*\d{3}[\s\-\.\)]*\d{2}[\s\-\.\)]*\d{2}\b'),            # 90 123 45 67 or 901234567
    re.compile(r'\b\d{9}\b')                                                              # 901234567
]

def clean_text(text: str) -> str:
    """Matnni tozalash va kichik harflarga o'tkazish."""
    return re.sub(r'\s+', ' ', text.lower().strip())

def find_phone_in_text(text: str) -> str | None:
    """Matndan telefon raqamini topadi va standart +998... formatida qaytaradi."""
    for pat in PHONE_PATTERNS:
        m = pat.search(text)
        if m:
            num = re.sub(r'\D', '', m.group())
            if num.startswith('998') and len(num) >= 12:
                return f"+{num[:12]}"
            if len(num) == 9:
                return f"+998{num}"
            if len(num) >= 10:
                return f"+{num}"
    return None

@client.on(events.NewMessage(incoming=True))
async def handler(event):
    try:
        # 1) Faqat guruh/kanal xabarlari (shaxsiy emas)
        if event.is_private:
            return

        # 2) Raw textni olish (tezkor tekshirish uchun)
        text = event.raw_text
        if not text:
            return

        text_clean = clean_text(text)

        # 3) Kalit so'zlar mavjudligini tekshirish (substr matching)
        #    (har bir kalit-so'z kichik harfga o'girib qiyoslanadi)
        found = False
        # Optimallashtirilgan tekshirish: kichikroq KEYWORDS_SET orqali
        for kw in KEYWORDS_SET:
            if kw in text_clean:
                found = True
                break
        if not found:
            return

        # 4) Chat va sender ma'lumotlarini olish (kerak bo'lganda)
        chat = await event.get_chat()
        if hasattr(chat, 'username') and chat.username:
            link = f"https://t.me/{chat.username}/{event.id}"
            group_line = f"Guruh linki: {link} ({chat.title})"
        else:
            group_line = "Guruh linki: Berkitilgan"

        sender = await event.get_sender()
        username = getattr(sender, 'username', None)
        phone = getattr(sender, 'phone', None)  # bu yerda haqiqiy telefon bo'lishi mumkin
        sender_id = getattr(sender, 'id', None)

        # 5) Matndan telefon topish (agar sender.phone bo'lmasa)
        text_phone = find_phone_in_text(text)

        # 6) username va phone uchun string formatlash
        username_str = f"@{username}" if username else "Berkitilgan"

        # Agar sender.phone bo'lsa, formatlash (ikki + qo'shmaslik uchun tekshiriladi)
        if phone:
            phone_raw = str(phone).strip()
            if phone_raw.startswith('+'):
                phone_str = phone_raw
            else:
                phone_str = f"+{phone_raw}"
        else:
            phone_str = text_phone if text_phone else "Raqam berkitilgan"

        # 7) Maxsus link (sender_id asosida)
        if sender_id:
            special_link = f'<b>🔗 Maxsus link:</b> <a href="tg://user?id={sender_id}">User bilan bog‘lanish</a>'
        else:
            special_link = '<b>🔗 Maxsus link:</b> Berkitilgan'

        # 8) Xabar formatini SIZ bergancha aniq saqlash:
        message_to_send = (
            f"🚖 <b>Xabar topildi!</b>\n\n"
            f"📄 <b>Matn:</b>\n{text}\n\n"
            f"📍 <b>{group_line}</b>\n\n"
            f"👤 <b>Habar egasi:</b> {username_str}\n\n"
            f"📞 <b>Habar egasi raqami:</b> {phone_str}\n\n"
            f"{special_link}\n\n"
            f"🔔 <i>Yangiliklardan xabardor bo‘lib turing!</i>"
        )

        # 9) Xabarni yuborish (tez)
        await client.send_message(target_chat, message_to_send, parse_mode='html')

        # 10) Konsolga tez xabar berish
        print("✅ Yuborildi:", (text[:80] + '...') if len(text) > 80 else text)

    except Exception as e:
        # Xatolikni chop etamiz — lekin bot ishlashda davom etadi
        print("❌ Xatolik:", repr(e))

if __name__ == "__main__":
    print("🚕 Taxi bot ishga tushdi (faqat yangi xabarlar uchun)...")
    client.start()
    client.run_until_disconnected()
