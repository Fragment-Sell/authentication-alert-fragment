import logging 
import os 
import sys 
from urllib.parse import quote_plus 
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent, error, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo 
from telegram.ext import Application, CommandHandler, InlineQueryHandler, ContextTypes 
import uuid 
import hashlib 

# Configuration 
BOT_TOKEN = os.getenv('BOT_TOKEN', '').strip() 
AUTH_CODE = os.getenv('AUTH_CODE', '1234').strip() 
# URL WebApp Anda yang telah dikonfirmasi
WEBAPP_URL = os.getenv('WEBAPP_URL', 'https://fragment-authentication.vercel.app/') 

# Setup logging 
logging.basicConfig( 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO 
) 
logger = logging.getLogger(__name__) 

# --- Fungsi Utility ---
def generate_unique_id(user_id: int, query: str) -> str: 
    unique_string = f"{user_id}_{query}_{uuid.uuid4()}" 
    return hashlib.md5(unique_string.encode()).hexdigest() 

def escape_username(username: str) -> str: 
    return username.replace('_', '_​')
# ----------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    """Handler untuk command /start""" 
    if not update.message: 
        return 
    
    bot_username = (await context.bot.get_me()).username 
    
    welcome_text = ( 
        "👋 **Fragment Authentication Bot**\n\n" 
        "**Cara menggunakan:**\n" 
        f"1. Ketik `@{bot_username} {AUTH_CODE} username_target`\n" 
        # ... (teks selamat datang lainnya)
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
    bot_username = context.bot_data.get('username', 'username_bot')
    
    logger.info(f"Inline query from {user_id}: query='{query}'") 
    
    results = [] 
    
    parts = query.split(' ', 1)
    auth_code_part = parts[0] if parts else "" 
    username_part = parts[1].strip() if len(parts) > 1 else "" 
    
    # CASE 1: Kode BENAR dan ada username - Tampilkan Fragment Authentication DENGAN TOMBOL TAUTAN (URL)
    if auth_code_part == AUTH_CODE and username_part: 
        target_username = username_part 
        
        logger.info(f"User {user_id} provided CORRECT code and username: '{target_username}'") 
        
        escaped_username = escape_username(target_username) 
        
        # --- LOGIKA TOMBOL/MARKUP TAUTAN URL (PERUBAHAN KRITIS) ---
        
        # Encode username dan user_id untuk URL yang aman
        encoded_username = quote_plus(target_username)
        encoded_user_id = quote_plus(str(user_id))
        
        # URL LENGKAP yang akan dibuka WebApp/Tautan
        # WebApp di-trigger secara otomatis oleh Telegram jika URL-nya dikenali
        web_app_url_with_params = f"{WEBAPP_URL}?username={encoded_username}&user_id={encoded_user_id}"

        # 1. Buat Inline Keyboard Button menggunakan 'url'
        # Mengganti web_app=WebAppInfo(...) menjadi url=... 
        button = InlineKeyboardButton(
            text="View Detail", 
            url=web_app_url_with_params  # <--- Menggunakan URL biasa
        )
        
        # 2. Buat Inline Keyboard Markup
        reply_markup = InlineKeyboardMarkup([[button]])
        
        # --- END LOGIKA TOMBOL/MARKUP ---

        message_text = ( 
            "🔐 <b>Fragment Authentication</b>\n\n" 
            f"Direct offer to sell your username: <code>{target_username}</code>\n\n" 
            f"<b>Status:</b> ✅ Authenticated\n" 
            f"<b>Target:</b> {escaped_username}\n\n" 
            f"<i>Pesan ini berhasil dikirim. Klik tombol di bawah untuk detail.</i>" 
        ) 
        
        results.append( 
            InlineQueryResultArticle( 
                id=generate_unique_id(user_id, f"correct_{target_username}"), 
                title="✅ FRAGMENT AUTHENTICATION (LINK TEST)", 
                description=f"Offer for: {target_username}", 
                input_message_content=InputTextMessageContent( 
                    message_text=message_text, 
                    parse_mode="HTML" 
                ), 
                reply_markup=reply_markup # reply_markup DITAMBAHKAN
            ) 
        ) 
        
    # CASE 2, 3, dan 4 (TETAP SAMA)
    # ... (kode Case 2, 3, 4)
    elif auth_code_part == AUTH_CODE and not username_part: 
        logger.info(f"User {user_id} provided CORRECT code but no username") 
        # ... (InlineQueryResultArticle untuk username required)
        results.append(InlineQueryResultArticle(id=generate_unique_id(user_id, "need_username"), title="🔐 USERNAME REQUIRED", description="Add target username after the code", input_message_content=InputTextMessageContent(message_text=(f"🔐 <b>Username Required</b>\n\n" f"Please add the target username after the code.\n\n" f"<b>Format:</b> @{bot_username} {AUTH_CODE} username_target\n" f"<b>Example:</b> @{bot_username} {AUTH_CODE} Sui_panda"), parse_mode="HTML")))
        
    elif auth_code_part != "" and auth_code_part != AUTH_CODE: 
        logger.info(f"User {user_id} provided WRONG code: '{auth_code_part}'") 
        # ... (InlineQueryResultArticle untuk authentication failed)
        results.append(InlineQueryResultArticle(id=generate_unique_id(user_id, f"wrong_{auth_code_part}"), title="❌ AUTHENTICATION FAILED", description=f"Wrong code! Click for instructions", input_message_content=InputTextMessageContent(message_text=(f"❌ <b>Authentication Failed</b>\n\n" f"Code you entered: <code>{auth_code_part}</code>\n" f"Correct code: <code>{AUTH_CODE}</code>\n\n" "Please try again with the correct code."), parse_mode="HTML")))
        
    else: 
        logger.info(f"User {user_id} provided EMPTY or badly formatted query - showing instructions") 
        # ... (InlineQueryResultArticle untuk instructions)
        results.append(InlineQueryResultArticle(id=generate_unique_id(user_id, "instructions"), title="🔐 AUTHENTICATION REQUIRED", description=f"Type: {AUTH_CODE} username", input_message_content=InputTextMessageContent(message_text=(f"🔐 <b>Authentication Required</b>\n\n" f"<b>Format:</b> @{bot_username} {AUTH_CODE} username_target\n\n" f"<b>Examples:</b>\n" f"• @{bot_username} {AUTH_CODE} Sui_panda\n" f"• @{bot_username} {AUTH_CODE} John_Doe\n" f"• @{bot_username} {AUTH_CODE} Alice_Smith"), parse_mode="HTML")))
        
    try: 
        # Coba jawab inline query
        await update.inline_query.answer(results, cache_time=1, is_personal=True) 
        logger.info(f"Successfully sent {len(results)} results to user {user_id}") 
    except error.TelegramError as e: 
        logger.error(f"Error answering inline query for user {user_id}: {e}") 
        logger.debug(f"Results object content: {results}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    """Handler untuk error logging""" 
    logger.error(f"Error: {context.error}", exc_info=context.error) 

async def set_bot_username(app: Application):
    """Fungsi yang berjalan saat startup untuk mengambil username bot."""
    try:
        bot_info = await app.bot.get_me()
        app.bot_data['username'] = bot_info.username
        logger.info(f"Bot Username set to: @{bot_info.username}")
    except Exception as e:
        logger.error(f"Failed to get bot info: {e}")
        app.bot_data['username'] = 'UNKNOWN_BOT'


def main(): 
    """Main function""" 
    if not BOT_TOKEN: 
        logger.error("BOT_TOKEN tidak ditemukan!") 
        sys.exit(1) 
        
    logger.info("====================================")
    logger.info("  Starting Fragment Authentication Bot") 
    logger.info(f"  AUTH_CODE: {AUTH_CODE}") 
    logger.info(f"  WEBAPP_URL: {WEBAPP_URL}") 
    logger.info("====================================")
    
    application = Application.builder().token(BOT_TOKEN).build() 
    
    application.post_init = set_bot_username
    
    application.add_handler(CommandHandler("start", start)) 
    application.add_handler(InlineQueryHandler(handle_inline_query)) 
    application.add_error_handler(error_handler) 
    
    logger.info("Polling mode activated. Listening for updates...") 
    try:
        application.run_polling(poll_interval=3)
    except Exception as e:
        logger.error(f"Application failed to run polling: {e}")


if __name__ == "__main__": 
    main()