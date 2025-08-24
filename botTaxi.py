import os
import re
import asyncio
import logging
import tempfile
import subprocess
from datetime import datetime, timezone
from telethon import TelegramClient, events
from faster_whisper import WhisperModel
import difflib

# ====== SOZLAMALAR ======
API_ID = 22731419
API_HASH = "2e2a9ce500a5bd08bae56f6ac2cc4890"
SESSION_NAME = "taxi_session"

TARGET_CHAT = "@rozimuhammadTaxi"   # Qayta yuboriladigan kanal/guruh

# Whisper model
WHISPER_MODEL_SIZE = "tiny"
WHISPER_COMPUTE_TYPE = "int8"
TRANSCRIBE_LANGUAGE = "uz"

# ====== KALIT SO‘ZLAR ======
# Faqat matnli xabarlar uchun
ALLOWED_KEYWORDS = [
    "olamiz va yuramiz", "odam bor", "mashina kerak"
]

# Rad etiladigan kalit so‘zlar (ruscha harflar ham)
BLOCK_KEYWORDS = [
    "почта", "КОБИЛТЬ", "ТОМ БАГАЖ", "Хизмат", "Чикораслар",
    "авто", "автo", "автoмобиль"
]

# ====== LOGGING ======
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("taxi-bot")

# ====== TELETHON KLIENT ======
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# Whisper model yuklash
log.info("Whisper model yuklanmoqda...")
whisper_model = WhisperModel(WHISPER_MODEL_SIZE, compute_type=WHISPER_COMPUTE_TYPE)
log.info("Whisper model tayyor.")

# ====== FUNKSIYALAR ======
def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())

def fuzzy_match(text: str, keywords, cutoff=0.55) -> bool:
    """Audio va matn uchun fuzzy qidiruv"""
    text = clean_text(text)
    if not text:
        return False

    # To‘g‘ridan-to‘g‘ri ichida bormi?
    for kw in keywords:
        if kw.lower() in text:
            return True

    # Yaqqol o‘xshash jumla
    for kw in keywords:
        ratio = difflib.SequenceMatcher(None, text, kw.lower()).ratio()
        if ratio >= cutoff:
            return True

    # So‘zlar bo‘yicha yaqinlik
    words = text.split()
    for kw in keywords:
        kw_words = kw.lower().split()
        for word in words:
            if difflib.get_close_matches(word, kw_words, n=1, cutoff=cutoff):
                return True

    return False

def format_username_and_phone(sender) -> tuple[str, str]:
    username = f"@{sender.username}" if getattr(sender, "username", None) else "Username yo‘q"
    raw_phone = getattr(sender, "phone", None)
    if raw_phone:
        phone = raw_phone if raw_phone.startswith("+") else f"+{raw_phone}"
    else:
        phone = "Ko‘rinmaydi"
    return username, phone

def build_source_line(chat, message_id: int) -> str:
    if hasattr(chat, "username") and chat.username:
        return f"{chat.title or chat.username} (https://t.me/{chat.username}/{message_id})"
    return f"{chat.title or 'Shaxsiy yoki yopiq guruh'}"

def is_audio_message(event) -> bool:
    msg = event.message
    if not msg or not msg.media:
        return False
    mime = getattr(getattr(msg, "document", None), "mime_type", "") or ""
    if mime.startswith("audio/") or "ogg" in mime or "opus" in mime:
        return True
    for attr in getattr(getattr(msg, "document", None), "attributes", []):
        if getattr(attr, "voice", False):
            return True
    return False

def ffmpeg_convert_to_wav(src_path: str, dst_path: str) -> None:
    cmd = ["ffmpeg", "-y", "-i", src_path, "-ac", "1", "-ar", "16000", dst_path]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def transcribe_audio(wav_path: str) -> str:
    segments, _ = whisper_model.transcribe(
        wav_path,
        language=TRANSCRIBE_LANGUAGE,
        vad_filter=True
    )
    return " ".join([seg.text.strip() for seg in segments if seg.text]).strip()

# ====== MATNLI XABAR UCHUN FILTRLASH ======
def match_text_message(text: str) -> bool:
    text_clean = clean_text(text)
    if not text_clean:
        return False

    # Rad etiladigan kalit so‘zlar bor-yo‘qligini tekshirish
    block_present = any(bk.lower() in text_clean for bk in BLOCK_KEYWORDS)
    allow_present = any(ak.lower() in text_clean for ak in ALLOWED_KEYWORDS)

    if allow_present:
        # Agar ruxsat berilgan kalit so‘z bo‘lsa, rad etiladigan bo‘lsa ham olinadi
        return True
    else:
        # Agar ruxsat berilgan kalit so‘z bo‘lmasa, tashlab ket
        return False

# ====== AUDIO XABAR UCHUN FILTRLASH ======
def match_audio_message(text: str) -> bool:
    # Audio xabarlar uchun fuzzy qidiruv
    return fuzzy_match(text, ALLOWED_KEYWORDS, cutoff=0.55)

# ====== AUDIO PROCESSOR ======
async def process_audio(event, username, phone, source_line):
    try:
        with tempfile.TemporaryDirectory() as tmpd:
            src_path = await event.message.download_media(file=tmpd)
            wav_path = os.path.join(tmpd, "audio.wav")
            ffmpeg_convert_to_wav(src_path, wav_path)
            transcript = transcribe_audio(wav_path)

            if match_audio_message(transcript):
                caption = (
                    "🚖 <b>Xabar topildi!</b>\n\n"
                    f"🎧 <b>Audio habar:</b>\n(Ovozli fayl ilova qilingan)\n\n"
                    f"📍 <b>Qayerdan:</b>\n{source_line}\n\n"
                    f"👤 <b>Habar yuboruvchi:</b> {username}\n"
                    f"📞 <b>Telefon:</b> {phone}\n\n"
                    "🔔 <i>Yangiliklardan xabardor bo‘lib turing!</i>"
                )
                await client.send_file(TARGET_CHAT, file=src_path, caption=caption, parse_mode="html")
                log.info("✅ Audio yuborildi.")
    except subprocess.CalledProcessError:
        log.exception("ffmpeg konvertatsiya xatosi")
    except Exception:
        log.exception("Audio qayta ishlashda xatolik")

# ====== HANDLER ======
@client.on(events.NewMessage(incoming=True))
async def handler(event):
    try:
        if event.is_private:
            return

        # Faqat yangi xabar (1 daqiqadan eski bo‘lsa tashlaymiz)
        msg_time = event.message.date.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        if (now - msg_time).total_seconds() > 60:
            return

        chat = await event.get_chat()
        sender = await event.get_sender()
        source_line = build_source_line(chat, event.id)
        username, phone = format_username_and_phone(sender)

        # === AUDIO ===
        if is_audio_message(event):
            asyncio.create_task(process_audio(event, username, phone, source_line))
            return

        # === MATN ===
        raw_text = (event.raw_text or "").strip()
        if raw_text and match_text_message(raw_text):
            message_to_send = (
                "🚖 <b>Xabar topildi!</b>\n\n"
                f"📄 <b>Matn:</b>\n{raw_text}\n\n"
                f"📍 <b>Qayerdan:</b>\n{source_line}\n\n"
                f"👤 <b>Habar yuboruvchi:</b> {username}\n"
                f"📞 <b>Telefon:</b> {phone}\n\n"
                "🔔 <i>Yangiliklardan xabardor bo‘lib turing!</i>"
            )
            await client.send_message(TARGET_CHAT, message_to_send, parse_mode="html")
            log.info("✅ Matn yuborildi.")

    except Exception:
        log.exception("Xatolik yuz berdi")

# ====== ISHGA TUSHIRISH ======
if __name__ == "__main__":
    print("🚕 Taxi bot ishga tushdi...")
    with client:
        client.run_until_disconnected()
