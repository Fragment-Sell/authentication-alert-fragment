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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /start"""
    if not update.message:
        return
        
    user = update.effective_user
    
    bot_username = (await context.bot.get_me()).username
    
    welcome_text = (
        "👋 **Fragment Authentication Bot**\n\n"
        "**Cara menggunakan:**\n"
        f"1. Buka chat dengan user target\n"
        f"2. Ketik `@{bot_username}` spasi `{AUTH_CODE}`\n"
        f"3. Contoh: `@{bot_username} {AUTH_CODE}`\n\n"
        "**Fitur:**\n"
        "• Fragment authentication untuk user yang sedang di-chat\n"
        "• Siapa saja yang tahu kode dapat mengirim\n"
        "• Interactive details\n\n"
        f"**Kode saat ini:** `{AUTH_CODE}`"
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
    
    # CASE 1: Kode BENAR - Tampilkan Fragment Authentication
    if query == AUTH_CODE:
        logger.info(f"User {user_id} provided CORRECT code")
        
        # Untuk inline query, kita tidak bisa langsung tahu target user
        # Tapi kita bisa minta user untuk memilih/mengetik username target
        results.append(
            InlineQueryResultArticle(
                id=generate_unique_id(user_id, "correct_code"),
                title="✅ FRAGMENT AUTHENTICATION",
                description="Correct code! Click to send offer template",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        "🔐 **Fragment Authentication**\n\n"
                        "Direct offer to sell your username @[username]\n\n"
                        "**Status:** ✅ Authenticated\n"
                        "**Instructions:** Replace @[username] with target username"
                    ),
                    parse_mode="Markdown"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📋 View Details", callback_data="show_details")]
                ])
            )
        )
    
    # CASE 2: Kode SALAH - Tampilkan pesan error
    elif query != "":
        logger.info(f"User {user_id} provided WRONG code: '{query}'")
        
        results.append(
            InlineQueryResultArticle(
                id=generate_unique_id(user_id, f"wrong_{query}"),
                title="❌ AUTHENTICATION FAILED",
                description=f"Wrong code! Click for instructions",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        "❌ **Authentication Failed**\n\n"
                        f"Code you entered: `{query}`\n"
                        f"Correct code: `{AUTH_CODE}`\n\n"
                        "Please try again with the correct code."
                    ),
                    parse_mode="Markdown"
                )
            )
        )
    
    # CASE 3: Query KOSONG - Tampilkan instruksi
    else:
        logger.info(f"User {user_id} provided EMPTY query - showing instructions")
        
        results.append(
            InlineQueryResultArticle(
                id=generate_unique_id(user_id, "instructions"),
                title="🔐 AUTHENTICATION REQUIRED",
                description=f"Type the code: {AUTH_CODE}",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        "🔐 **Authentication Required**\n\n"
                        f"Please type the authentication code after @username_bot\n\n"
                        f"**Correct code:** `{AUTH_CODE}`\n\n"
                        "**Example:** `@username_bot {AUTH_CODE}`"
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
    user_id = user.id
    
    try:
        await query.answer()
    except error.TelegramError as e:
        logger.error(f"Error answering callback: {e}")
        return
    
    if query.data == "show_details":
        try:
            # Ambil username dari pesan asli (jika ada)
            original_text = query.message.text
            username = "target_username"
            
            # Coba extract username dari pesan asli
            if "@[" in original_text and "]" in original_text:
                start_idx = original_text.find("@[") + 2
                end_idx = original_text.find("]", start_idx)
                if start_idx < end_idx:
                    username = original_text[start_idx:end_idx]
            
            detail_text = (
                "🔒 **Fragment Authentication Details**\n\n"
                f"**Target Username:** @{username}\n"
                f"**Offer Type:** Direct Sale\n"
                f"**Status:** Available\n"
                f"**Authentication:** Verified ✅\n"
                f"**Security Level:** High\n\n"
                "*This is a secure fragment authentication offer*\n\n"
                "**Instructions:** Edit the message to replace @[username] with actual target username"
            )
            
            await query.edit_message_text(
                text=detail_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back to Message", callback_data="back_to_message")],
                    [InlineKeyboardButton("❌ Close", callback_data="close")]
                ])
            )
                
        except Exception as e:
            logger.error(f"Error in show_details: {e}")
            await query.answer("❌ Error loading details", show_alert=True)
    
    elif query.data == "back_to_message":
        try:
            await query.edit_message_text(
                text=(
                    "🔐 **Fragment Authentication**\n\n"
                    "Direct offer to sell your username @[username]\n\n"
                    "**Status:** ✅ Authenticated\n"
                    "**Instructions:** Replace @[username] with target username"
                ),
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📋 View Details", callback_data="show_details")]
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