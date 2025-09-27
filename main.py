import logging
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Application, CommandHandler, InlineQueryHandler, CallbackQueryHandler, ContextTypes
import uuid

# Configuration from Environment Variables (Railway)
BOT_TOKEN = os.getenv('BOT_TOKEN', '').strip()
OWNER_IDS_STR = os.getenv('OWNER_IDS', '').strip()
AUTH_CODE = os.getenv('AUTH_CODE', '1234').strip()
PORT = int(os.getenv('PORT', 8443))
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '').strip()

# Parse OWNER_IDS
OWNER_IDS = set()
if OWNER_IDS_STR:
    try:
        OWNER_IDS = set(map(int, [x.strip() for x in OWNER_IDS_STR.split(',') if x.strip()]))
    except ValueError as e:
        logging.error(f"Error parsing OWNER_IDS: {e}")

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /start"""
    if not update.message:
        return
        
    user_id = update.effective_user.id
    is_owner = user_id in OWNER_IDS
    
    welcome_text = (
        "👋 **Fragment Authentication Bot**\n\n"
        "**Untuk Owner:**\n"
        "• Ketik `@username_bot 1234` di chat manapun\n"
        "• Ganti `1234` dengan kode autentikasi Anda\n\n"
        "**Fitur:**\n"
        "• Direct username offer\n"
        "• Secure fragment authentication\n"
        "• Interactive buttons\n\n"
    )
    
    if is_owner:
        welcome_text += "✅ **Status:** Anda terverifikasi sebagai Owner"
    else:
        welcome_text += "❌ **Status:** Akses terbatas (Owner only)"
    
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def handle_inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk inline query (@bot)"""
    if not update.inline_query:
        return
        
    query = update.inline_query.query.strip()
    user_id = update.inline_query.from_user.id
    username = update.inline_query.from_user.username or update.inline_query.from_user.first_name
    
    logger.info(f"Inline query from {user_id} (@{username}): '{query}'")
    
    # Jika user adalah owner dan mengirim kode yang benar
    if user_id in OWNER_IDS and query == AUTH_CODE:
        results = [
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="✅ Fragment Authentication - Direct Offer",
                description=f"Click to send offer for @{username}",
                input_message_content=InputTextMessageContent(
                    message_text=f"🔐 **Fragment Authentication**\n\nDirect offer to sell your username @{username}",
                    parse_mode="Markdown"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📋 View Detail", callback_data=f"view_detail_{user_id}")],
                    [InlineKeyboardButton("👤 Contact Owner", url=f"https://t.me/{username}")]
                ])
            )
        ]
    elif user_id in OWNER_IDS and query == "":
        # Jika owner tapi belum input kode
        results = [
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="🔐 Authentication Required",
                description=f"Input code: {AUTH_CODE}",
                input_message_content=InputTextMessageContent(
                    message_text="⚠️ **Authentication Required**\n\nPlease input your authentication code after @username_bot",
                    parse_mode="Markdown"
                )
            )
        ]
    else:
        # Jika bukan owner atau kode salah
        results = [
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="❌ Access Denied",
                description="Owner authentication required",
                input_message_content=InputTextMessageContent(
                    message_text="🚫 **Access Denied**\n\nThis feature is only available for verified owners.",
                    parse_mode="Markdown"
                )
            )
        ]
    
    try:
        await update.inline_query.answer(results, cache_time=0)
        logger.info(f"Successfully answered inline query for user {user_id}")
    except Exception as e:
        logger.error(f"Error answering inline query: {e}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk tombol callback"""
    if not update.callback_query:
        return
        
    query = update.callback_query
    user_id = query.from_user.id
    callback_data = query.data
    
    try:
        await query.answer()
    except Exception as e:
        logger.error(f"Error answering callback: {e}")
        return
    
    if callback_data.startswith("view_detail_"):
        try:
            target_user_id = int(callback_data.split("_")[2])
            username = query.from_user.username or query.from_user.first_name
            
            # Verifikasi bahwa user yang menekan tombol adalah owner yang sesuai
            if user_id == target_user_id:
                detail_text = (
                    f"🔒 **Fragment Authentication Details**\n\n"
                    f"**Username:** @{username}\n"
                    f"**User ID:** `{user_id}`\n"
                    f"**Offer Type:** Direct Sale\n"
                    f"**Status:** Available\n"
                    f"**Authentication:** Verified ✅\n"
                    f"**Timestamp:** {query.message.date.strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
                    f"*This is a secure fragment authentication offer.*"
                )
                
                await query.edit_message_text(
                    text=detail_text,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Back", callback_data="back_to_main"),
                         InlineKeyboardButton("❌ Close", callback_data="close")]
                    ])
                )
            else:
                await query.answer("❌ Anda tidak memiliki akses ke detail ini", show_alert=True)
        except Exception as e:
            logger.error(f"Error in view_detail: {e}")
            await query.answer("❌ Error loading details", show_alert=True)
    
    elif callback_data == "back_to_main":
        try:
            username = query.from_user.username or query.from_user.first_name
            await query.edit_message_text(
                text=f"🔐 **Fragment Authentication**\n\nDirect offer to sell your username @{username}",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📋 View Detail", callback_data=f"view_detail_{user_id}")],
                    [InlineKeyboardButton("👤 Contact Owner", url=f"https://t.me/{username}")]
                ])
            )
        except Exception as e:
            logger.error(f"Error in back_to_main: {e}")
    
    elif callback_data == "close":
        try:
            await query.delete_message()
        except Exception as e:
            logger.error(f"Error deleting message: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk error logging"""
    logger.error(f"Error occurred: {context.error}", exc_info=context.error)

def main():
    """Main function untuk menjalankan bot"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN tidak ditemukan! Pastikan sudah di-set di environment variables.")
        return
    
    if not OWNER_IDS:
        logger.warning("OWNER_IDS kosong! Bot hanya akan merespon ke user yang terdaftar.")
    
    logger.info(f"Bot starting with OWNER_IDS: {OWNER_IDS}")
    logger.info(f"Authentication code: {AUTH_CODE}")

    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(InlineQueryHandler(handle_inline_query))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_error_handler(error_handler)
    
    # Check if running on Railway with webhook URL
    if WEBHOOK_URL:
        logger.info(f"Running with webhook on port {PORT}")
        try:
            application.run_webhook(
                listen="0.0.0.0",
                port=PORT,
                url_path=BOT_TOKEN,
                webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}"
            )
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            logger.info("Falling back to polling...")
            application.run_polling()
    else:
        logger.info("Running with polling...")
        application.run_polling()

if __name__ == "__main__":
    main()