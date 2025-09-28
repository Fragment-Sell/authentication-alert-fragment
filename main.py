import logging
import os
import sys
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InlineQueryResultArticle, InputTextMessageContent, error
from telegram.ext import Application, CommandHandler, InlineQueryHandler, CallbackQueryHandler, ContextTypes
import uuid
import hashlib

# Configuration - Hanya butuh BOT_TOKEN dan AUTH_CODE saja
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
    user_id = user.id
    
    bot_username = (await context.bot.get_me()).username
    
    welcome_text = (
        "👋 **Fragment Authentication Bot**\n\n"
        "**Cara menggunakan:**\n"
        f"1. Buka chat/grup manapun\n"
        f"2. Ketik `@{bot_username}` spasi `{AUTH_CODE}`\n"
        f"3. Contoh: `@{bot_username} {AUTH_CODE}`\n\n"
        "**Fitur:**\n"
        "• Siapa saja yang tahu kode dapat mengirim fragment authentication\n"
        "• Secure fragment authentication\n"
        "• Interactive buttons\n\n"
        f"**Kode saat ini:** `{AUTH_CODE}`\n"
        f"**User ID Anda:** `{user_id}`"
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
    username = user.username or user.first_name
    
    logger.info(f"Inline query from {user_id} (@{username}): query='{query}'")
    logger.info(f"Query == AUTH_CODE: {query == AUTH_CODE}")
    
    results = []
    
    # CASE 1: Kode BENAR - Tampilkan Fragment Authentication
    if query == AUTH_CODE:
        logger.info(f"User {user_id} provided CORRECT code - showing fragment auth")
        
        contact_url = f"https://t.me/{user.username}" if user.username else f"tg://user?id={user_id}"
        
        results.append(
            InlineQueryResultArticle(
                id=generate_unique_id(user_id, "correct_code"),
                title="✅ FRAGMENT AUTHENTICATION",
                description="Correct code! Click to send offer",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        "🔐 **Fragment Authentication**\n\n"
                        f"Direct offer to sell your username @{username}\n\n"
                        "**Status:** ✅ Authenticated\n"
                        f"**Username:** @{username}\n"
                        f"**Authentication:** Verified"
                    ),
                    parse_mode="Markdown"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📋 View Details", callback_data=f"details_{user_id}")],
                    [InlineKeyboardButton("👤 Contact", url=contact_url)]
                ]),
                thumbnail_url="https://img.icons8.com/color/96/000000/verified-account.png"
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
                        "Please try again with the correct code.\n\n"
                        f"**Example:** `@username_bot {AUTH_CODE}`"
                    ),
                    parse_mode="Markdown"
                ),
                thumbnail_url="https://img.icons8.com/color/96/000000/cancel.png"
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
                        f"**Example:** `@username_bot {AUTH_CODE}`\n\n"
                        "Siapa saja yang mengetahui kode dapat mengirim fragment authentication."
                    ),
                    parse_mode="Markdown"
                ),
                thumbnail_url="https://img.icons8.com/color/96/000000/lock--v1.png"
            )
        )
    
    try:
        # CACHE_TIME = 1 untuk menghindari cache, IS_PERSONAL = True untuk hasil per user
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
    
    if query.data.startswith("details_"):
        try:
            target_user_id = int(query.data.split("_")[1])
            
            # Verifikasi sederhana - hanya user yang membuat pesan yang bisa lihat detail
            if user_id == target_user_id:
                detail_text = (
                    "🔒 **Fragment Authentication Details**\n\n"
                    f"**Username:** @{user.username or user.first_name}\n"
                    f"**User ID:** `{user_id}`\n"
                    f"**Offer Type:** Direct Sale\n"
                    f"**Status:** Available\n"
                    f"**Authentication:** Verified ✅\n"
                    f"**Security Level:** High\n\n"
                    "*This is a secure fragment authentication offer*\n\n"
                    "**Note:** Anyone with the correct code can send this offer."
                )
                
                await query.edit_message_text(
                    text=detail_text,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Back", callback_data="back")],
                        [InlineKeyboardButton("❌ Close", callback_data="close")]
                    ])
                )
            else:
                await query.answer("❌ Anda hanya dapat melihat detail pesan yang Anda buat", show_alert=True)
                
        except Exception as e:
            logger.error(f"Error in details: {e}")
            await query.answer("❌ Error loading details", show_alert=True)
    
    elif query.data == "back":
        try:
            username = user.username or user.first_name
            contact_url = f"https://t.me/{user.username}" if user.username else f"tg://user?id={user_id}"
            
            await query.edit_message_text(
                text=f"🔐 **Fragment Authentication**\n\nDirect offer to sell your username @{username}",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📋 View Details", callback_data=f"details_{user_id}")],
                    [InlineKeyboardButton("👤 Contact", url=contact_url)]
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
    logger.info(f"Sample command: @your_bot_username {AUTH_CODE}")

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