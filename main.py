import logging 
import os 
import sys 
# Import yang dibutuhkan untuk tombol Web App
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent, error, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo 
from telegram.ext import Application, CommandHandler, InlineQueryHandler, ContextTypes 
import uuid 
import hashlib 

# Configuration 
BOT_TOKEN = os.getenv('BOT_TOKEN', '').strip() 
AUTH_CODE = os.getenv('AUTH_CODE', '1234').strip() 
# --- Konfigurasi Web App ---
# GANTI NILAI INI dengan URL Web App Anda yang sebenarnya!
WEB_APP_URL = os.getenv('WEB_APP_URL', 'https://fragment-authentication.vercel.app/').strip() 
# ---------------------------

# Setup logging 
logging.basicConfig( 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO 
) 
logger = logging.getLogger(__name__) 

# --- Fungsi Utility ---
def generate_unique_id(user_id: int, query: str) -> str: 
    """Generate unique ID berdasarkan user_id dan query untuk menghindari cache""" 
    unique_string = f"{user_id}_{query}_{uuid.uuid4()}" 
    return hashlib.md5(unique_string.encode()).hexdigest() 

def escape_username(username: str) -> str: 
    """Escape karakter khusus untuk menghindari masalah formatting""" 
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
        f"2. Contoh: `@{bot_username} {AUTH_CODE} Sui_panda`\n" 
        f"3. Bot akan kirim offer untuk username tersebut\n\n" 
        f"**Format:** `@{bot_username} [kode] [username]`\n" 
        f"**Kode auth:** `{AUTH_CODE}`\n\n"
        f"**Tombol:** 'View Detail' sekarang akan membuka Web App Anda." 
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
    parts = query.split(' ', 1)  
    auth_code_part = parts[0] if parts else ""
    # Gunakan .strip() untuk membersihkan username
    username_part = parts[1].strip() if len(parts) > 1 else "" 
     
    # ----------------------------------------------------
    # URUTAN BARU: 4 - 3 - 2 - 1 
    # ----------------------------------------------------
    
    # CASE 4: Query KOSONG - Tampilkan instruksi (DICEK PERTAMA)
    if not query: 
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
                        f"• @username_bot {AUTH_CODE} Alice_Smith" 
                    ), 
                    parse_mode="HTML" 
                ) 
            ) 
        ) 
         
    # CASE 3: Kode SALAH - Tampilkan pesan error
    elif auth_code_part != AUTH_CODE: 
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
         
    # CASE 1: Kode BENAR dan ada username - Tampilkan Fragment Authentication (DICEK TERAKHIR)
    elif auth_code_part == AUTH_CODE and username_part: 
        target_username = username_part 
         
        logger.info(f"User {user_id} provided CORRECT code and username: '{target_username}'") 
         
        escaped_username = escape_username(target_username) 
         
        # --- LOGIKA TOMBOL WEB APP ---
        keyboard_buttons = []
        reply_markup = None
        
        # Hanya tambahkan tombol jika URL Web App diatur dan bukan placeholder
        if WEB_APP_URL and WEB_APP_URL != 'https://URL_MINI_APP_ANDA':
            try:
                # Membuat tombol "View Detail" menggunakan WebAppInfo
                web_app_button = InlineKeyboardButton(
                    "📋 View Detail", 
                    web_app=WebAppInfo(url=WEB_APP_URL)
                )
                keyboard_buttons.append([web_app_button])
                reply_markup = InlineKeyboardMarkup(keyboard_buttons)
            except Exception as e:
                # Jika terjadi error saat membuat tombol, log dan lanjutkan tanpa tombol
                logger.error(f"Error creating WebAppInfo button: {e}")
        # ----------------------------

        # Format pesan dengan HTML parsing 
        message_text = ( 
            "🔐 <b>Fragment Authentication</b>\n\n" 
            f"Direct offer to sell your username: <code>{target_username}</code>\n\n" 
            f"<b>Status:</b> ✅ Authenticated\n" 
            f"<b>Target:</b> {escaped_username}\n\n" 
            f"<i>Klik tombol di bawah untuk melihat detail.</i>" 
        ) 
         
        results.append( 
            InlineQueryResultArticle( 
                id=generate_unique_id(user_id, f"correct_{target_username}"), 
                title="✅ FRAGMENT AUTHENTICATION", 
                description=f"Offer for: {target_username}", 
                input_message_content=InputTextMessageContent( 
                    message_text=message_text, 
                    parse_mode="HTML" 
                ), 
                reply_markup=reply_markup 
            ) 
        ) 
         
    # ----------------------------------------------------
    
    try: 
        # Cache time 1 detik dan is_personal=True membantu mengatasi masalah caching
        await update.inline_query.answer(results, cache_time=1, is_personal=True) 
        logger.info(f"Successfully sent {len(results)} results to user {user_id}") 
    except error.TelegramError as e: 
        logger.error(f"Error answering inline query: {e}") 

# Handler error tetap
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
    logger.info(f"WEB_APP_URL: {WEB_APP_URL}")
 
    application = Application.builder().token(BOT_TOKEN).build() 
     
    application.add_handler(CommandHandler("start", start)) 
    application.add_handler(InlineQueryHandler(handle_inline_query)) 
    application.add_error_handler(error_handler) 
     
    logger.info("Polling mode") 
    application.run_polling() 

if __name__ == "__main__": 
    main()