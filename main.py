import logging
import os
import sys
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InlineQueryResultArticle, InputTextMessageContent, error
from telegram.ext import Application, CommandHandler, InlineQueryHandler, CallbackQueryHandler, ContextTypes
import uuid
import hashlib
import urllib.parse # Pertahankan import yang mungkin dibutuhkan di fungsi lain atau di masa depan

# Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', '').strip()
AUTH_CODE = os.getenv('AUTH_CODE', '1234').strip()
PORT = int(os.getenv('PORT', 8443))
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '').strip() # Nilai WEBHOOK_URL akan digunakan

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def generate_unique_id(user_id: int, query: str) -> str:
    """Generate unique ID berdasarkan user_id dan query untuk menghindari cache"""
    unique_string = f"{user_id}_{query}_{uuid.uuid4()}"
    return hashlib.md5(unique_string.encode()).hexdigest()

def escape_username(username: str) -> str:
    """Escape karakter khusus untuk menghindari masalah formatting"""
    # Ganti underscore dengan underscore + zero-width space untuk menghindari italic
    return username.replace('_', '_​')  # underscore + zero-width space

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /start"""
    if not update.message:
        return
        
    user = update.effective_user
    
    bot_username = (await context.bot.get_me()).username
    
    welcome_text = (
        "👋 **Fragment Authentication Bot**\n\n"
        "**Cara menggunakan:**\n"
        f"1. Ketik `@{bot_username} {AUTH_CODE} username_target`\n"
        f"2. Contoh: `@{bot_username} {AUTH_CODE} Sui_panda`\n"
        f"3. Bot akan kirim offer untuk username tersebut\n\n"
        f"**Format:** `@{bot_username} [kode] [username]`\n"
        f"**Kode auth:** `{AUTH_CODE}`\n\n"
        "✅ **Support:** Username dengan underscore (_) didukung penuh"
    )
    
    try:
        await update.message.reply_text(welcome_text, parse_mode="Markdown")
    except error.TelegramError as e:
        logger.error(f"Failed to send /start message: {e}")

async def handle_inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk inline query (@bot)"""
    if not update.inline_query:
        return
        
    query = update.inline_query.query.strip()
    user = update.inline_query.from_user
    user_id = user.id
    
    logger.info(f"Inline query from {user_id}: query='{query}'")
    
    results = []
    
    # Parse query: format "code username"
    parts = query.split(' ', 1)  # Split menjadi 2 parts: code dan username
    auth_code_part = parts[0] if parts else ""
    username_part = parts[1] if len(parts) > 1 else ""
    
    # CASE 1: Kode BENAR dan ada username - Tampilkan Fragment Authentication
    if auth_code_part == AUTH_CODE and username_part:
        # Pertahankan format asli username (case sensitive)
        target_username = username_part.strip()
        
        logger.info(f"User {user_id} provided CORRECT code and username: '{target_username}'")
        
        # Escape username untuk menghindari masalah formatting
        escaped_username = escape_username(target_username)
        
        # Hash username untuk ID unik (dipertahankan dari kode lama, meskipun callback data sudah dihapus)
        username_hash = hashlib.md5(target_username.encode()).hexdigest()
        
        # Tentukan URL untuk tombol "View Details"
        # Gunakan WEBHOOK_URL secara langsung tanpa parameter tambahan
        details_url = WEBHOOK_URL 
        
        # Format pesan dengan HTML parsing untuk kontrol yang lebih baik
        message_text = (
            "🔐 <b>Fragment Authentication</b>\n\n"
            f"Direct offer to sell your username: <code>{target_username}</code>\n\n"
            f"<b>Status:</b> ✅ Authenticated\n"
            f"<b>Target:</b> {escaped_username}"
        )
        
        results.append(
            InlineQueryResultArticle(
                id=generate_unique_id(user_id, f"correct_{username_hash}"),
                title="✅ FRAGMENT AUTHENTICATION",
                description=f"Offer for: {target_username}",
                input_message_content=InputTextMessageContent(
                    message_text=message_text,
                    parse_mode="HTML"  # Gunakan HTML untuk formatting yang lebih terkontrol
                ),
                reply_markup=InlineKeyboardMarkup([
                    # PERUBAHAN UTAMA: Menggunakan url=details_url (WEBHOOK_URL)
                    # dan menambahkan tombol close untuk mempertahankan fitur lama
                    [InlineKeyboardButton("📋 View Details", url=details_url)],
                    [InlineKeyboardButton("❌ Close", callback_data="close")] # Tombol close dipertahankan menggunakan callback data
                ])
            )
        )
    
    # CASE 2: Kode BENAR tapi tidak ada username - Minta input username
    elif auth_code_part == AUTH_CODE and not username_part:
        logger.info(f"User {user_id} provided CORRECT code but no username")
        
        results.append(
            InlineQueryResultArticle(
                id=generate_unique_id(user_id, "need_username"),
                title="🔐 USERNAME REQUIRED",
                description="Add target username after the code",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        "🔐 <b>Username Required</b>\n\n"
                        f"Please add the target username after the code.\n\n"
                        f"<b>Format:</b> @username_bot {AUTH_CODE} username_target\n"
                        f"<b>Example:</b> @username_bot {AUTH_CODE} Sui_panda"
                    ),
                    parse_mode="HTML"
                )
            )
        )
    
    # CASE 3: Kode SALAH - Tampilkan pesan error
    elif auth_code_part != "" and auth_code_part != AUTH_CODE:
        logger.info(f"User {user_id} provided WRONG code: '{auth_code_part}'")
        
        results.append(
            InlineQueryResultArticle(
                id=generate_unique_id(user_id, f"wrong_{auth_code_part}"),
                title="❌ AUTHENTICATION FAILED",
                description=f"Wrong code! Click for instructions",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        "❌ <b>Authentication Failed</b>\n\n"
                        f"Code you entered: <code>{auth_code_part}</code>\n"
                        f"Correct code: <code>{AUTH_CODE}</code>\n\n"
                        "Please try again with the correct code."
                    ),
                    parse_mode="HTML"
                )
            )
        )
    
    # CASE 4: Query KOSONG - Tampilkan instruksi
    else:
        logger.info(f"User {user_id} provided EMPTY query - showing instructions")
        
        results.append(
            InlineQueryResultArticle(
                id=generate_unique_id(user_id, "instructions"),
                title="🔐 AUTHENTICATION REQUIRED",
                description=f"Type: {AUTH_CODE} username",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        "🔐 <b>Authentication Required</b>\n\n"
                        f"<b>Format:</b> @username_bot {AUTH_CODE} username_target\n\n"
                        f"<b>Examples:</b>\n"
                        f"• @username_bot {AUTH_CODE} Sui_panda\n"
                        f"• @username_bot {AUTH_CODE} John_Doe\n"
                        f"• @username_bot {AUTH_CODE} Alice_Smith\n"
                        f"• @username_bot {AUTH_CODE} test_user_123"
                    ),
                    parse_mode="HTML"
                )
            )
        )
    
    try:
        await update.inline_query.answer(results, cache_time=1, is_personal=True)
        logger.info(f"Successfully sent {len(results)} results to user {user_id}")
    except error.TelegramError as e:
        logger.error(f"Error answering inline query: {e}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler untuk tombol callback.
    Fungsi ini dipertahankan secara keseluruhan, hanya menyesuaikan callback_data yang relevan.
    Karena tombol 'View Details' sudah diubah menjadi URL,
    kita hanya perlu mempertahankan logic untuk 'close'.
    """
    if not update.callback_query:
        return
        
    query = update.callback_query
    user = query.from_user
    
    try:
        await query.answer()
    except error.TelegramError as e:
        logger.error(f"Error answering callback: {e}")
        return
    
    # Logic callback data lama untuk 'details_' dan 'back_' dihapus/dinonaktifkan
    # karena tombol 'View Details' sekarang adalah URL eksternal.
    
    if query.data == "close":
        try:
            await query.message.delete()
        except Exception as e:
            logger.error(f"Error closing: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk error logging"""
    logger.error(f"Error: {context.error}", exc_info=context.error)

def main():
    """Main function"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN tidak ditemukan!")
        sys.exit(1)
        
    logger.info(f"Starting Fragment Authentication Bot")
    logger.info(f"AUTH_CODE: {AUTH_CODE}")
    # Tambahkan logging WEBHOOK_URL untuk verifikasi
    logger.info(f"WEBHOOK_URL: {WEBHOOK_URL}")

    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(InlineQueryHandler(handle_inline_query))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_error_handler(error_handler)
    
    if WEBHOOK_URL:
        logger.info(f"Webhook mode on port {PORT}")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}"
        )
    else:
        logger.info("Polling mode")
        application.run_polling()

if __name__ == "__main__":
    main()