import logging
import os
import sys
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InlineQueryResultArticle, InputTextMessageContent, error
from telegram.ext import Application, CommandHandler, InlineQueryHandler, CallbackQueryHandler, ContextTypes
import uuid

# --- 1. Konfigurasi dari Environment Variables ---
BOT_TOKEN = os.getenv('BOT_TOKEN', '').strip()
OWNER_IDS_STR = os.getenv('OWNER_IDS', '').strip()
AUTH_CODE = os.getenv('AUTH_CODE', '1234').strip()
PORT = int(os.getenv('PORT', 8443))
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '').strip()

# --- 2. Setup Logging ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- 3. Parsing OWNER_IDS ---
OWNER_IDS = set()
if OWNER_IDS_STR:
    try:
        OWNER_IDS = set(map(int, [x.strip() for x in OWNER_IDS_STR.split(',') if x.strip()]))
        logger.info(f"Successfully parsed OWNER_IDS: {OWNER_IDS}")
    except ValueError as e:
        logger.error(f"Error parsing OWNER_IDS: {e}")

# --- 4. Handlers ---

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
        "**Untuk Owner:**\n"
        f"• Ketik `@{bot_username} {AUTH_CODE}` di chat manapun\n"
        "• Bot akan mengirimkan fragment authentication\n\n"
        "**Fitur:**\n"
        "• Direct username offer\n"
        "• Secure fragment authentication\n"
        "• Interactive buttons\n\n"
    )
    
    if is_owner:
        welcome_text += f"✅ **Status:** Anda terverifikasi sebagai Owner (ID: {user_id})"
    else:
        welcome_text += f"❌ **Status:** Akses terbatas (Owner only)\n\nUser ID Anda: {user_id}"
    
    try:
        await update.message.reply_text(welcome_text, parse_mode="Markdown")
    except error.TelegramError as e:
        logger.error(f"Failed to send /start message to user {user_id}: {e}")

async def handle_inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk inline query (@bot)"""
    if not update.inline_query:
        return
        
    query = update.inline_query.query.strip()
    user = update.inline_query.from_user
    user_id = user.id
    username = user.username or user.first_name
    
    logger.info(f"Inline query from {user_id} (@{username}): query='{query}'")
    logger.info(f"User {user_id} in OWNER_IDS: {user_id in OWNER_IDS}")
    logger.info(f"Query matches AUTH_CODE: {query == AUTH_CODE}")
    
    results = []
    
    # 1. Cek apakah user adalah owner
    if user_id not in OWNER_IDS:
        logger.info(f"User {user_id} is not in OWNER_IDS")
        results.append(
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="❌ Access Denied",
                description="Owner authentication required",
                input_message_content=InputTextMessageContent(
                    message_text="🚫 **Access Denied**\n\nThis feature is only available for verified owners.",
                    parse_mode="Markdown"
                )
            )
        )
    # 2. Jika user adalah owner dan kode benar
    elif query == AUTH_CODE:
        logger.info(f"User {user_id} provided correct auth code")
        contact_url = f"https://t.me/{user.username}" if user.username else f"tg://user?id={user_id}"
        
        results.append(
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
                    [InlineKeyboardButton("👤 Contact Owner", url=contact_url)]
                ])
            )
        )
    # 3. Jika user adalah owner tapi kode salah atau kosong
    else:
        logger.info(f"User {user_id} is owner but provided wrong/empty code: '{query}'")
        bot_username = (await context.bot.get_me()).username
        
        if query == "":
            description = f"Input authentication code: {AUTH_CODE}"
            message_text = f"⚠️ **Authentication Required**\n\nPlease type: `@{bot_username} {AUTH_CODE}`"
        else:
            description = "Wrong code! Click for instructions"
            message_text = f"❌ **Wrong Authentication Code**\n\nPlease use: `@{bot_username} {AUTH_CODE}`"
        
        results.append(
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="🔐 Authentication Required",
                description=description,
                input_message_content=InputTextMessageContent(
                    message_text=message_text,
                    parse_mode="Markdown"
                )
            )
        )
    
    try:
        await update.inline_query.answer(results, cache_time=0, is_personal=True)
        logger.info(f"Successfully answered inline query for user {user_id}")
    except error.TelegramError as e:
        logger.error(f"Error answering inline query for user {user_id}: {e}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk tombol callback"""
    if not update.callback_query:
        return
        
    query = update.callback_query
    user = query.from_user
    user_id = user.id
    callback_data = query.data
    
    try:
        await query.answer()
    except error.TelegramError as e:
        logger.error(f"Error answering callback query from user {user_id}: {e}")
        return
    
    if callback_data.startswith("view_detail_"):
        try:
            target_user_id = int(callback_data.split("_")[2])
            username = user.username or user.first_name
            
            # Verifikasi bahwa user yang menekan tombol adalah owner yang sesuai
            if user_id == target_user_id and user_id in OWNER_IDS:
                timestamp = query.message.edit_date.strftime('%Y-%m-%d %H:%M:%S UTC') if query.message.edit_date else query.message.date.strftime('%Y-%m-%d %H:%M:%S UTC')

                detail_text = (
                    f"🔒 **Fragment Authentication Details**\n\n"
                    f"**Username:** @{username}\n"
                    f"**User ID:** `{user_id}`\n"
                    f"**Offer Type:** Direct Sale\n"
                    f"**Status:** Available\n"
                    f"**Authentication:** Verified ✅\n"
                    f"**Timestamp:** {timestamp}\n\n"
                    f"*This is a secure fragment authentication offer.*"
                )
                
                await query.edit_message_text(
                    text=detail_text,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Back", callback_data=f"back_to_main_{target_user_id}"),
                         InlineKeyboardButton("❌ Close", callback_data="close")]
                    ])
                )
            else:
                await query.answer("❌ Anda tidak memiliki akses ke detail ini", show_alert=True)
        except (ValueError, IndexError, error.TelegramError) as e:
            logger.error(f"Error in view_detail for user {user_id}: {e}")
            await query.answer("❌ Error loading details", show_alert=True)
        
    elif callback_data.startswith("back_to_main_"):
        try:
            target_user_id = int(callback_data.split("_")[3])
            
            if user_id != target_user_id or user_id not in OWNER_IDS:
                await query.answer("❌ Akses Ditolak", show_alert=True)
                return
                 
            username = user.username or user.first_name
            contact_url = f"https://t.me/{user.username}" if user.username else f"tg://user?id={user_id}"
            
            await query.edit_message_text(
                text=f"🔐 **Fragment Authentication**\n\nDirect offer to sell your username @{username}",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📋 View Detail", callback_data=f"view_detail_{user_id}")],
                    [InlineKeyboardButton("👤 Contact Owner", url=contact_url)]
                ])
            )
        except (ValueError, IndexError, error.TelegramError) as e:
            logger.error(f"Error in back_to_main for user {user_id}: {e}")
            await query.answer("❌ Error: Gagal kembali ke menu utama", show_alert=True)
        
    elif callback_data == "close":
        try:
            await query.message.delete()
        except error.BadRequest as e:
            logger.warning(f"Failed to delete message for user {user_id}: {e}")
        except error.TelegramError as e:
            logger.error(f"Error deleting message for user {user_id}: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk error logging"""
    logger.error(f"Error occurred: {context.error}", exc_info=context.error)

def main():
    """Main function untuk menjalankan bot"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN tidak ditemukan! Pastikan sudah di-set di environment variables.")
        sys.exit(1)
        
    if not OWNER_IDS:
        logger.warning("OWNER_IDS kosong! Bot hanya akan berfungsi untuk inline query yang tidak terautentikasi.")
    
    logger.info(f"Bot starting with OWNER_IDS: {OWNER_IDS}")
    logger.info(f"Authentication code: {AUTH_CODE}")

    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(InlineQueryHandler(handle_inline_query))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_error_handler(error_handler)
    
    # Run bot
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
            sys.exit(1)
    else:
        logger.info("Running with polling...")
        application.run_polling()

if __name__ == "__main__":
    main()