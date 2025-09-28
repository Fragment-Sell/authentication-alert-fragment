import logging
import os
import sys
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InlineQueryResultArticle, InputTextMessageContent, error
from telegram.ext import Application, CommandHandler, InlineQueryHandler, CallbackQueryHandler, ContextTypes
import uuid
import hashlib

# Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', '').strip()
AUTH_CODE = os.getenv('AUTH_CODE', '1234').strip()
PORT = int(os.getenv('PORT', 8443))
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '').strip()

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

def format_username(username: str) -> str:
    """Format username dengan @ dan pertahankan case asli"""
    username = username.strip()
    if not username.startswith('@'):
        username = f"@{username}"
    return username

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
        f"3. Bot akan kirim offer untuk @Sui_panda\n\n"
        f"**Format:** `@{bot_username} [kode] [username]`\n"
        f"**Kode auth:** `{AUTH_CODE}`\n\n"
        "💡 **Tips:** Tulis username persis seperti aslinya (huruf besar/kecil)"
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
        # Tambahkan @ jika belum ada, TAPI pertahankan case
        if not target_username.startswith('@'):
            target_username = f"@{target_username}"
            
        logger.info(f"User {user_id} provided CORRECT code and username: '{target_username}'")
        
        results.append(
            InlineQueryResultArticle(
                id=generate_unique_id(user_id, f"correct_{target_username}"),
                title="✅ FRAGMENT AUTHENTICATION",
                description=f"Offer for {target_username}",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        f"🔐 **Fragment Authentication**\n\n"
                        f"Direct offer to sell your username {target_username}\n\n"
                        f"**Status:** ✅ Authenticated\n"
                        f"**Target:** {target_username}"
                    ),
                    parse_mode="Markdown"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📋 View Details", callback_data=f"details_{hashlib.md5(target_username.encode()).hexdigest()}")]
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
                        "🔐 **Username Required**\n\n"
                        f"Please add the target username after the code.\n\n"
                        f"**Format:** `@username_bot {AUTH_CODE} username_target`\n"
                        f"**Example:** `@username_bot {AUTH_CODE} Sui_panda`\n\n"
                        "💡 **Important:** Write the username exactly as it appears (case sensitive)"
                    ),
                    parse_mode="Markdown"
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
                        "❌ **Authentication Failed**\n\n"
                        f"Code you entered: `{auth_code_part}`\n"
                        f"Correct code: `{AUTH_CODE}`\n\n"
                        "Please try again with the correct code."
                    ),
                    parse_mode="Markdown"
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
                        "🔐 **Authentication Required**\n\n"
                        f"**Format:** `@username_bot {AUTH_CODE} username_target`\n\n"
                        f"**Examples:**\n"
                        f"• `@username_bot {AUTH_CODE} Sui_panda`\n"
                        f"• `@username_bot {AUTH_CODE} John_Doe`\n"
                        f"• `@username_bot {AUTH_CODE} AliceSmith`\n\n"
                        "💡 **Tip:** Write the username exactly as it appears, including uppercase/lowercase letters"
                    ),
                    parse_mode="Markdown"
                )
            )
        )
    
    try:
        await update.inline_query.answer(results, cache_time=1, is_personal=True)
        logger.info(f"Successfully sent {len(results)} results to user {user_id}")
    except error.TelegramError as e:
        logger.error(f"Error answering inline query: {e}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk tombol callback"""
    if not update.callback_query:
        return
        
    query = update.callback_query
    user = query.from_user
    
    try:
        await query.answer()
    except error.TelegramError as e:
        logger.error(f"Error answering callback: {e}")
        return
    
    if query.data.startswith("details_"):
        try:
            # Extract hash dari callback data dan cari username asli dari pesan
            hash_part = query.data.replace("details_", "")
            
            # Ambil username asli dari teks pesan
            original_text = query.message.text
            target_username = "target_username"
            
            # Extract username dari teks pesan (pertahankan case asli)
            if "your username " in original_text:
                start_idx = original_text.find("your username ") + len("your username ")
                end_idx = original_text.find("\n", start_idx)
                if end_idx == -1:
                    end_idx = len(original_text)
                username_line = original_text[start_idx:end_idx].strip()
                # Ambil sampai akhir (bisa berupa username saja atau dengan teks lain)
                if " " in username_line:
                    target_username = username_line.split(" ")[0]
                else:
                    target_username = username_line
            
            detail_text = (
                "🔒 **Fragment Authentication Details**\n\n"
                f"**Target Username:** {target_username}\n"
                f"**Offer Type:** Direct Sale\n"
                f"**Status:** Available\n"
                f"**Authentication:** Verified ✅\n"
                f"**Security Level:** High\n\n"
                "*This is a secure fragment authentication offer*\n\n"
                f"**Offer:** Direct offer to sell your username {target_username}"
            )
            
            await query.edit_message_text(
                text=detail_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back to Offer", callback_data="back_to_offer")],
                    [InlineKeyboardButton("❌ Close", callback_data="close")]
                ])
            )
                
        except Exception as e:
            logger.error(f"Error in show_details: {e}")
            await query.answer("❌ Error loading details", show_alert=True)
    
    elif query.data == "back_to_offer":
        try:
            # Kembali ke pesan asli (tidak perlu menyimpan username)
            await query.edit_message_text(
                text=query.message.text,  # Kembalikan ke teks asli
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📋 View Details", callback_data="details_back")]
                ])
            )
        except Exception as e:
            logger.error(f"Error going back: {e}")
    
    elif query.data == "close":
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