import logging
import os
import sys
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InlineQueryResultArticle, InputTextMessageContent, error
from telegram.ext import Application, CommandHandler, InlineQueryHandler, CallbackQueryHandler, ContextTypes
import uuid

# Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', '').strip()
OWNER_IDS_STR = os.getenv('OWNER_IDS', '').strip()
AUTH_CODE = os.getenv('AUTH_CODE', '1234').strip()
PORT = int(os.getenv('PORT', 8443))
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '').strip()

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Parse OWNER_IDS
OWNER_IDS = set()
if OWNER_IDS_STR:
    try:
        OWNER_IDS = set(map(int, [x.strip() for x in OWNER_IDS_STR.split(',') if x.strip()]))
        logger.info(f"OWNER_IDS: {OWNER_IDS}")
    except ValueError as e:
        logger.error(f"Error parsing OWNER_IDS: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /start"""
    if not update.message:
        return
        
    user = update.effective_user
    user_id = user.id
    is_owner = user_id in OWNER_IDS
    
    bot_username = (await context.bot.get_me()).username
    
    welcome_text = (
        "👋 **Fragment Authentication Bot**\n\n"
        "**Cara menggunakan:**\n"
        f"1. Ketik `@{bot_username}` di chat manapun\n"
        f"2. Pilih opsi yang sesuai\n"
        f"3. Jika owner, ketik kode: `{AUTH_CODE}`\n\n"
    )
    
    if is_owner:
        welcome_text += f"✅ **Status:** Owner (ID: {user_id})"
    else:
        welcome_text += f"❌ **Status:** Bukan Owner\nUser ID: {user_id}"
    
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
    
    logger.info(f"Inline query from {user_id}: query='{query}'")
    
    results = []
    
    # OPSI A: Jika kode benar DAN user adalah owner
    if query == AUTH_CODE and user_id in OWNER_IDS:
        logger.info(f"User {user_id} provided CORRECT code")
        
        results.append(
            InlineQueryResultArticle(
                id="correct_code",
                title="✅ FRAGMENT AUTHENTICATION - CORRECT CODE",
                description="Kode benar! Klik untuk mengirim offer",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        "🔐 **Fragment Authentication**\n\n"
                        f"Direct offer to sell your username @{username}\n\n"
                        f"✅ **Status:** Authenticated\n"
                        f"👤 **Owner:** {username}\n"
                        f"🆔 **User ID:** {user_id}"
                    ),
                    parse_mode="Markdown"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📋 View Details", callback_data=f"details_{user_id}")],
                    [InlineKeyboardButton("👤 Contact", url=f"https://t.me/{user.username}" if user.username else f"tg://user?id={user_id}")]
                ]),
                thumbnail_url="https://img.icons8.com/color/96/000000/verified-account.png"
            )
        )
    
    # OPSI B: Jika kode salah TAPI user adalah owner
    elif query != AUTH_CODE and user_id in OWNER_IDS and query != "":
        logger.info(f"User {user_id} provided WRONG code: '{query}'")
        
        results.append(
            InlineQueryResultArticle(
                id="wrong_code",
                title="❌ AUTHENTICATION FAILED - WRONG CODE",
                description="Kode salah! Klik untuk instruksi",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        "❌ **Authentication Failed**\n\n"
                        f"Kode yang Anda masukkan: `{query}`\n"
                        f"Kode yang benar: `{AUTH_CODE}`\n\n"
                        "Silakan coba lagi dengan kode yang benar."
                    ),
                    parse_mode="Markdown"
                )
            )
        )
    
    # OPSI C: Default - Instruksi authentication
    else:
        logger.info(f"Showing auth instructions for user {user_id}")
        
        if user_id in OWNER_IDS:
            description = f"Ketik kode: {AUTH_CODE}"
            message_text = (
                "🔐 **Authentication Required**\n\n"
                f"Ketik kode authentication setelah @username_bot\n\n"
                f"**Kode yang benar:** `{AUTH_CODE}`\n"
                f"**User ID Anda:** `{user_id}`\n\n"
                "Contoh: `@username_bot 1234`"
            )
        else:
            description = "Access denied - Owner only"
            message_text = (
                "🚫 **Access Denied**\n\n"
                "Fitur ini hanya tersedia untuk verified owners.\n\n"
                f"**User ID Anda:** `{user_id}`"
            )
        
        results.append(
            InlineQueryResultArticle(
                id="auth_required",
                title="🔐 AUTHENTICATION REQUIRED",
                description=description,
                input_message_content=InputTextMessageContent(
                    message_text=message_text,
                    parse_mode="Markdown"
                ),
                thumbnail_url="https://img.icons8.com/color/96/000000/lock--v1.png"
            )
        )
    
    try:
        await update.inline_query.answer(results, cache_time=1, is_personal=True)
        logger.info(f"Sent {len(results)} results to user {user_id}")
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
            
            if user_id == target_user_id:
                detail_text = (
                    "🔒 **Fragment Authentication Details**\n\n"
                    f"**Username:** @{user.username or user.first_name}\n"
                    f"**User ID:** `{user_id}`\n"
                    f"**Offer Type:** Direct Sale\n"
                    f"**Status:** Available\n"
                    f"**Authentication:** Verified ✅\n"
                    f"**Security Level:** High\n\n"
                    "*Secure fragment authentication offer*"
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
                await query.answer("❌ Access denied", show_alert=True)
                
        except Exception as e:
            logger.error(f"Error in details: {e}")
            await query.answer("❌ Error loading details", show_alert=True)
    
    elif query.data == "back":
        try:
            username = user.username or user.first_name
            await query.edit_message_text(
                text=f"🔐 **Fragment Authentication**\n\nDirect offer to sell your username @{username}",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📋 View Details", callback_data=f"details_{user_id}")],
                    [InlineKeyboardButton("👤 Contact", url=f"https://t.me/{user.username}" if user.username else f"tg://user?id={user_id}")]
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
        
    logger.info(f"Starting bot...")
    logger.info(f"OWNER_IDS: {OWNER_IDS}")
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