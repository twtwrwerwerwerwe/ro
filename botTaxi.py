# botTaxi.py
# -*- coding: utf-8 -*-

import re
import asyncio
from telethon import TelegramClient, events

# === Windows uchun asyncio muammosini hal qilamiz ===
try:
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
except Exception:
    pass

# === API MA'LUMOTLARI ===
api_id = 28023612
api_hash = 'fe94ef46addc1b6b8253d5448e8511f0'

# === SESSION ===
client = TelegramClient('taxi_session', api_id, api_hash)

# === YUBORILADIGAN KANAL (sizning kanal linkingiz) ===
target_chat = 'https://t.me/+BFl15wH-PAswZTYy'

# === KALIT SO‘ZLAR RO‘YXATI ===
KEYWORDS = [
    # Odam bor
    'odam bor', 'odambor', 'odam borakan', 'odam bor ekan',
    'bitta odam bor', 'ikkita odam bor', 'uchta odam bor', 'tortta odam bor', "to'rtta odam bor",
    'bir komplekt odam bor', 'komplekt odam bor', 'kompilekt odam bor', 'kampilek odam bor', 'komplek odam bor',
    '1ta odam bor', '2ta odam bor', '3ta odam bor', '4ta odam bor',
    'odam bor 1', 'odam bor 2', 'odam bor 3', 'odam bor 4', 'odam bor 1ta', 'odam bor 2ta', 'odam bor 3ta', 'odam bor 4ta',

    # Kirillcha variantlar
    'одам бор', 'одамбoр', 'одам боракан', 'одам бор экан',
    'битта одам бор', 'иккита одам бор', 'учта одам бор', 'тортта одам бор',
    'бир комплект одам бор', 'комплект одам бор', 'кампилек одам бор', 'компилект одам бор', 'комплек одам бор',
    'одам бор 1', 'одам бор 2', 'одам бор 3', 'одам бор 4',
    'одам бор 1та', 'одам бор 2та', 'одам бор 3та', 'одам бор 4та',

    # Yo‘nalish
    'rishtonga odam bor', 'toshkentga odam bor', 'риштонга одам бор', 'тошкентга одам бор',

    # Mashina kerak
    'mashina kerak', 'mashina kere', 'mashina kerek', 'bagajli mashina kerak', 'bagajli mashina kere',
    'машина керак', 'машина кере', 'машина нужен', 'багажли машина керак', 'багажли машина кере',
    'mashina keraa', 'машина кераа', 'bosh mashina kerak', 'bosh mashina bormikan', 'boshi bormikan',

    # Pochta bor
    'pochta bor', 'rishtonga pochta bor', 'rishtondan pochta bor', 'toshkentga pochta bor', 'toshkentdan pochta bor',
    'почта бор', 'риштонга почта бор', 'риштондан почта бор', 'тошкентга почта бор', 'тошкентдан почта бор',

    # Ketadi
    'ketadi', 'ketishadi', 'ketishi kerak', 'ketishi', 'ayol kishi ketadi',
    'кeтaди', 'кeтишaди', 'кeтиши кeрaк', 'кeтиши', 'ayол киши кeтaди',

    # Dastavka
    'dastavka bor', 'dastafka', 'даставка бор', 'дастaфка',

    # Boshqa yo‘nalishlar
    'toshkentdan qoqonga odam bor', "toshkendan qo'qonga odam bor",
    "toshkentdan fargonaga odam bor", "toshkentdan farg'onaga odam bor", "toshkendan fargonaga odam bor"
]
KEYWORDS_SET = set(k.lower() for k in KEYWORDS)

# === OLDINDAN KOMPILIYATSiyALANGAN REGEXLAR (tezlik uchun) ===
# Kalit so'zlarni so'z chegaralari bilan qidiramiz (case-insensitive)
KEYWORDS_RE = [re.compile(r'\b' + re.escape(k) + r'\b', re.IGNORECASE) for k in KEYWORDS]

# Telefon uchun regexlar (turli formatlarni qamrab oladi)
PHONE_PATTERNS = [
    re.compile(r'\+?998[\s\-\.\(]*\d{2}[\s\-\.\)]*\d{3}[\s\-\.\)]*\d{2}[\s\-\.\)]*\d{2}'),  # +998 90 123 45 67
    re.compile(r'\b\d{2}[\s\-\.\)]*\d{3}[\s\-\.\)]*\d{2}[\s\-\.\)]*\d{2}\b'),            # 90 123 45 67 or 901234567
    re.compile(r'\b\d{9}\b')                                                              # 901234567
]

CLEAN_RE = re.compile(r'\s+')

def clean_text(text: str) -> str:
    return CLEAN_RE.sub(' ', text.lower().strip())

def has_keyword(text: str) -> bool:
    # regexlar bilan aniqlash (so'z chegarasi bilan) — aniq va tez
    for r in KEYWORDS_RE:
        if r.search(text):
            return True
    return False

def extract_phone_from_text(text: str) -> str | None:
    for pat in PHONE_PATTERNS:
        m = pat.search(text)
        if m:
            num = re.sub(r'\D', '', m.group())
            # standartlashtirish
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
        # faqat guruh/kanal xabarlari
        if event.is_private:
            return

        text = event.raw_text
        if not text:
            return

        text_clean = clean_text(text)
        # faqat kalit so'z bo'lsa davom etadi
        if not has_keyword(text_clean):
            return

        # get_chat() va get_sender() parallel chaqiriladi (tezlik uchun)
        chat_task = asyncio.create_task(event.get_chat())
        sender_task = asyncio.create_task(event.get_sender())
        chat, sender = await asyncio.gather(chat_task, sender_task)

        # Guruh link/nom
        if hasattr(chat, 'username') and chat.username:
            group_line = f"{chat.title or 'Guruh'} — https://t.me/{chat.username}/{event.id}"
        else:
            # agar public username bo'lmasa, faqat sarlavha yoki "Berkitilgan guruh"
            group_line = f"{getattr(chat, 'title', 'Berkitilgan guruh')}"

        # Username va user id
        username = getattr(sender, 'username', None)
        username_str = f"@{username}" if username else "Berkitilgan"
        sender_id = getattr(sender, 'id', None)

        # Telefonni aniqlash: birinchi navbatda sender.profile (agar mavjud bo'lsa), keyin matndan
        phone_str = "Raqam berkitilgan"
        sender_phone = getattr(sender, 'phone', None)
        if sender_phone:
            # sender.phone bo'lsa, uni standart formatga keltirish
            phone_raw = str(sender_phone).strip()
            if phone_raw.startswith('+'):
                phone_str = phone_raw
            else:
                phone_str = f"+{phone_raw}"
        else:
            # matndan topamiz
            found = extract_phone_from_text(text)
            if found:
                phone_str = found

        # Maxsus link
        special_link = f'<a href="tg://user?id={sender_id}">Profilga o‘tish</a>' if sender_id else "Berkitilgan"

        # Xabarni kerakli formatda tayyorlash (raqam ko'rsatiladi agar topilgan bo'lsa)
        message_to_send = (
            f"🚖 <b>Xabar topildi!</b>\n\n"
            f"📄 <b>Matn:</b>\n{text}\n\n"
            f"📍 <b>Guruh:</b> {group_line}\n\n"
            f"👤 <b>Habar egasi:</b> {username_str}\n\n"
            f"📞 <b>Raqam:</b> {phone_str}\n\n"
            f"🔗 <b>Maxsus link:</b> {special_link}\n\n"
            f"🔔 <b>Yangi e’lonlardan xabardor bo‘ling!</b>"
        )

        # Juda tez yuborish (asenkron, boshqa ishni bloklamaydi)
        asyncio.create_task(client.send_message(target_chat, message_to_send, parse_mode='html'))

        # Konsolga tezkor xabar
        print("✅ Yuborildi:", (text[:80] + '...') if len(text) > 80 else text)

    except Exception as e:
        # Xatolik bo'lsa, konsolga chiqaramiz va davom etamiz
        print("❌ Xatolik:", repr(e))

# === BOSHLASH ===
if __name__ == "__main__":
    print("🚕 Super tez Taxi bot ishga tushdi! Faqat kalit so‘zli yangi xabarlar uchun.")
    client.start()
    client.run_until_disconnected()
