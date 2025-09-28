import logging
import os
import sys
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InlineQueryResultArticle, InputTextMessageContent, error
from telegram.ext import Application, CommandHandler, InlineQueryHandler, CallbackQueryHandler, ContextTypes
import uuid
import hashlib

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
    is_owner = user_id in OWNER_IDS
    
    bot_username = (await context.bot.get_me()).username
    
    welcome_text = (
        "👋 **Fragment Authentication Bot**\n\n"
        "**Cara menggunakan:**\n"
        f"1. Buka chat/grup manapun\n"
        f"2. Ketik `@{bot_username}` spasi `{AUTH_CODE}`\n"
        f"3. Contoh: `@{bot_username} {AUTH_CODE}`\n\n"
        "**Debug Info:**\n"
        f"• User ID: `{user_id}`\n"
        f"• Owner Status: {'✅' if is_owner else '❌'}\n"
        f"• Auth Code: `{AUTH_CODE}`\n\n"
        "Jika ada masalah, coba hapus cache dengan ketik: `@username_bot random123`"
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
    logger.info(f"User in OWNER_IDS: {user_id in OWNER_IDS}")
    logger.info(f"Query == AUTH_CODE: {query == AUTH_CODE}")
    
    results = []
    
    # CASE 1: User BUKAN owner - selalu tampilkan access denied
    if user_id not in OWNER_IDS:
        logger.info(f"User {user_id} is NOT in OWNER_IDS - showing access denied")
        
        results.append(
            InlineQueryResultArticle(
                id=generate_unique_id(user_id, "not_owner"),
                title="❌ ACCESS DENIED",
                description="This feature is for owners only",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        "🚫 **Access Denied**\n\n"
                        "This feature is only available for verified owners.\n\n"
                        f"**Your User ID:** `{user_id}`\n"
                        "**Status:** Not authorized"
                    ),
                    parse_mode="Markdown"
                ),
                thumbnail_url="https://img.icons8.com/color/96/000000/no-entry.png"
            )
        )
    
    # CASE 2: User adalah owner DAN kode benar
    elif query == AUTH_CODE:
        logger.info(f"User {user_id} is owner and provided CORRECT code - showing fragment auth")
        
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
                        f"**Owner:** {username}\n"
                        f"**User ID:** {user_id}"
                    ),
                    parse_mode="Markdown"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📋 View Details", callback_data=f"details_{user_id}")],
                    [InlineKeyboardButton("👤 Contact Owner", url=contact_url)]
                ]),
                thumbnail_url="https://img.icons8.com/color/96/000000/verified-account.png"
            )
        )
    
    # CASE 3: User adalah owner TAPI kode salah/kosong
    else:
        logger.info(f"User {user_id} is owner but provided WRONG/EMPTY code: '{query}'")
        
        if query == "":
            title = "🔐 AUTHENTICATION REQUIRED"
            description = f"Type the code: {AUTH_CODE}"
            message_text = (
                "🔐 **Authentication Required**\n\n"
                f"Please type the authentication code after @username_bot\n\n"
                f"**Correct code:** `{AUTH_CODE}`\n"
                f"**Your User ID:** `{user_id}`\n\n"
                "Example: `@username_bot 1234`"
            )
            thumbnail = "https://img.icons8.com/color/96/000000/lock--v1.png"
        else:
            title = "❌ WRONG CODE"
            description = f"Wrong code! Correct: {AUTH_CODE}"
            message_text = (
                "❌ **Wrong Authentication Code**\n\n"
                f"Code you entered: `{query}`\n"
                f"Correct code: `{AUTH_CODE}`\n\n"
                f"**Your User ID:** `{user_id}`\n"
                "**Status:** Owner (but wrong code)\n\n"
                "Please try again with the correct code."
            )
            thumbnail = "https://img.icons8.com/color/96/000000/cancel.png"
        
        results.append(
            InlineQueryResultArticle(
                id=generate_unique_id(user_id, f"wrong_{query}"),
                title=title,
                description=description,
                input_message_content=InputTextMessageContent(
                    message_text=message_text,
                    parse_mode="Markdown"
                ),
                thumbnail_url=thumbnail
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
            
            if user_id == target_user_id:
                detail_text = (
                    "🔒 **Fragment Authentication Details**\n\n"
                    f"**Username:** @{user.username or user.first_name}\n"
                    f"**User ID:** `{user_id}`\n"
                    f"**Offer Type:** Direct Sale\n"
                    f"**Status:** Available\n"
                    f"**Authentication:** Verified ✅\n"
                    f"**Security Level:** High\n\n"
                    "*This is a secure fragment authentication offer*"
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
            contact_url = f"https://t.me/{user.username}" if user.username else f"tg://user?id={user_id}"
            
            await query.edit_message_text(
                text=f"🔐 **Fragment Authentication**\n\nDirect offer to sell your username @{username}",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📋 View Details", callback_data=f"details_{user_id}")],
                    [InlineKeyboardButton("👤 Contact Owner", url=contact_url)]
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
        
    logger.info(f"Starting bot with:")
    logger.info(f"OWNER_IDS: {OWNER_IDS}")
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