import os
import re
import logging
import tempfile
import subprocess
import asyncio
from concurrent.futures import ThreadPoolExecutor
from telethon import TelegramClient, events
from faster_whisper import WhisperModel
from difflib import SequenceMatcher

# ====== SOZLAMALAR ======
API_ID = 22731419
API_HASH = "2e2a9ce500a5bd08bae56f6ac2cc4890"
SESSION_NAME = "taxi_session"
TARGET_CHAT = "@rozimuhammadTaxi"

# Whisper model
WHISPER_MODEL_SIZE = "tiny"
WHISPER_COMPUTE_TYPE = "int8"
TRANSCRIBE_LANGUAGE = "uz"

# Kalit so'zlar
KEYWORDS = [
    'odam bor', 'odam bor 1', 'odam bor 1ta', 'odam bor 1 ta',
    'rishtonga odam bor', 'toshkentga odam bor',
    'pochta bor', 'rishtonga pochta bor', 'toshkentga pochta bor',
    'ketadi', 'ketishadi', 'ketishi kerak',
    'mashina kerak', 'kampilek odam bor', 'kampilek odam', 'komplekt odam', 'kampilekt', 'komplekt odam', 'odam bor ekan', 'odam borakan', 'odam borkan'
    # kirillcha
    'одам бор', 'одам бор 1', 'риштонга одам бор',
    'почта бор', 'тошкентга почта бор',
    'кетади', 'кетишади', 'машина керак', 'кампилек одам бор'
]

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("taxi-bot")

# Telegram client
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# Whisper model yuklash
log.info("Whisper model yuklanmoqda...")
whisper_model = WhisperModel(WHISPER_MODEL_SIZE, compute_type=WHISPER_COMPUTE_TYPE)
log.info("Whisper model tayyor.")

# ThreadPool executor (audio transkripsiya uchun)
executor = ThreadPoolExecutor(max_workers=6)  # ko'proq parallel

# ====== FUNKSIYALAR ======
def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())

def exact_match(text: str) -> bool:
    text = clean_text(text)
    return any(kw.lower() in text for kw in KEYWORDS)

def fuzzy_match(text: str, cutoff=0.5) -> bool:
    """Sezgirroq audio xabar uchun o'xshashlik"""
    text = clean_text(text)
    return any(SequenceMatcher(None, text, kw.lower()).ratio() >= cutoff for kw in KEYWORDS)

def is_audio_message(msg) -> bool:
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

def transcribe_audio_sync(wav_path: str) -> str:
    segments, _ = whisper_model.transcribe(
        wav_path,
        language=TRANSCRIBE_LANGUAGE,
        vad_filter=True
    )
    return " ".join([seg.text.strip() for seg in segments if seg.text]).strip()

async def transcribe_audio_async(wav_path: str) -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, transcribe_audio_sync, wav_path)

def format_username_and_phone(sender) -> tuple[str, str]:
    username = f"@{sender.username}" if getattr(sender, "username", None) else "Username yo‘q"
    raw_phone = getattr(sender, "phone", None)
    phone = raw_phone if raw_phone and raw_phone.startswith("+") else f"+{raw_phone}" if raw_phone else "Ko‘rinmaydi"
    return username, phone

def build_source_line(chat, message_id: int) -> str:
    if hasattr(chat, "username") and chat.username:
        return f"{chat.title or chat.username} (https://t.me/{chat.username}/{message_id})"
    return f"{chat.title or 'Shaxsiy yoki yopiq guruh'}"

async def process_message(event):
    chat = await event.get_chat()
    sender = await event.get_sender()
    username, phone = format_username_and_phone(sender)
    source_line = build_source_line(chat, event.id)

    msg = event.message

    # ===== Audio xabar =====
    if is_audio_message(msg):
        try:
            with tempfile.TemporaryDirectory() as tmpd:
                src_path = await msg.download_media(file=tmpd)
                wav_path = os.path.join(tmpd, "audio.wav")
                ffmpeg_convert_to_wav(src_path, wav_path)

                transcript = await transcribe_audio_async(wav_path)

                if transcript and fuzzy_match(transcript, cutoff=0.5):  # o'xshashlikni sezgirroq qildik
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
        except Exception:
            log.exception("Audio xabarni qayta ishlashda xatolik yuz berdi")
        return

    # ===== Matnli xabar =====
    raw_text = (msg.raw_text or "").strip()
    if raw_text and exact_match(raw_text):
        try:
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
            log.exception("Matn xabarni yuborishda xatolik yuz berdi")

# ===== Handler =====
@client.on(events.NewMessage(incoming=True))
async def new_message_handler(event):
    try:
        if event.is_private:
            return
        await process_message(event)
    except Exception:
        log.exception("Xatolik yuz berdi")

# ===== Ishga tushirish =====
if __name__ == "__main__":
    print("🚕 Taxi bot ishga tushdi...")
    with client:
        client.run_until_disconnected()
