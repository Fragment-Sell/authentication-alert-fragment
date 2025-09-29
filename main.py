import logging 
import os 
import sys 
# Import disederhanakan, hanya menyisakan yang diperlukan
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent, error, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo # <-- DITAMBAHKAN
from telegram.ext import Application, CommandHandler, InlineQueryHandler, ContextTypes 
import uuid 
import hashlib 

# Configuration 
BOT_TOKEN = os.getenv('BOT_TOKEN', '').strip() 
AUTH_CODE = os.getenv('AUTH_CODE', '1234').strip() 
# *CATATAN PENTING:* # Anda harus menentukan URL WebApp Anda di sini. Ini bisa berupa URL apa pun
# yang dapat diakses oleh browser (misalnya, https://nama-bot.herokuapp.com/web-app)
# Pastikan WebApp tersebut telah dikonfigurasi di BotFather.
WEBAPP_URL = os.getenv('WEBAPP_URL', 'https://www.google.com/') # <-- DITAMBAHKAN (Ganti dengan URL WebApp Anda)

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
    # underscore + zero-width space
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
        f"**Kode auth:** `{AUTH_CODE}`\n" 
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
    # Pastikan username di-strip untuk parsing yang handal
    username_part = parts[1].strip() if len(parts) > 1 else "" 
    
    # CASE 1: Kode BENAR dan ada username - Tampilkan Fragment Authentication DENGAN TOMBOL WEBAPP 
    if auth_code_part == AUTH_CODE and username_part: 
        target_username = username_part 
        
        logger.info(f"User {user_id} provided CORRECT code and username: '{target_username}'") 
        
        escaped_username = escape_username(target_username) 
        
        # --- LOGIKA TOMBOL/MARKUP DITAMBAHKAN DI SINI ---
        
        # 1. Buat Inline Keyboard Button
        # WebAppInfo digunakan untuk mengarahkan ke WebApp bot
        web_app_info = WebAppInfo(url=f"{WEBAPP_URL}?username={target_username}&user_id={user_id}") 
        button = InlineKeyboardButton(
            text="View Detail", 
            web_app=web_app_info # Menggunakan web_app
        )
        
        # 2. Buat Inline Keyboard Markup
        reply_markup = InlineKeyboardMarkup([[button]])
        
        # --- END LOGIKA TOMBOL/MARKUP ---

        # Format pesan dengan HTML parsing 
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
                title="✅ FRAGMENT AUTHENTICATION", 
                description=f"Offer for: {target_username}", 
                input_message_content=InputTextMessageContent( 
                    message_text=message_text, 
                    parse_mode="HTML" 
                ), 
                reply_markup=reply_markup # <-- reply_markup DITAMBAHKAN
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
        bot_username = (await context.bot.get_me()).username if not context.bot_data.get('username') else context.bot_data['username']
        logger.info(f"User {user_id} provided EMPTY query - showing instructions") 
        
        results.append( 
            InlineQueryResultArticle( 
                id=generate_unique_id(user_id, "instructions"), 
                title="🔐 AUTHENTICATION REQUIRED", 
                description=f"Type: {AUTH_CODE} username", 
                input_message_content=InputTextMessageContent( 
                    message_text=( 
                        "🔐 <b>Authentication Required</b>\n\n" 
                        f"<b>Format:</b> @{bot_username} {AUTH_CODE} username_target\n\n" 
                        f"<b>Examples:</b>\n" 
                        f"• @{bot_username} {AUTH_CODE} Sui_panda\n" 
                        f"• @{bot_username} {AUTH_CODE} John_Doe\n" 
                        f"• @{bot_username} {AUTH_CODE} Alice_Smith" 
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
    logger.info(f"WEBAPP_URL: {WEBAPP_URL}") # <-- DITAMBAHKAN
    
    application = Application.builder().token(BOT_TOKEN).build() 
    
    application.add_handler(CommandHandler("start", start)) 
    application.add_handler(InlineQueryHandler(handle_inline_query)) 
    application.add_error_handler(error_handler) 
    
    # Ambil username bot dan simpan di context_data untuk digunakan di handle_inline_query
    async def set_bot_username(app: Application):
        bot_info = await app.bot.get_me()
        app.bot_data['username'] = bot_info.username

    # Jalankan function untuk mendapatkan username sebelum loop utama
    application.post_init = set_bot_username
    
    # Logika Webhook/Polling
    if os.getenv('WEBHOOK_URL'):
        # Karena konfigurasinya dihapus, ini hanya peringatan
        logger.warning("WEBHOOK_URL ditemukan. Mode Webhook mungkin memerlukan konfigurasi PORT dan URL yang tepat.")
        logger.info("Polling mode (as fallback)") 
        application.run_polling() 
    else: 
        logger.info("Polling mode") 
        application.run_polling() 

if __name__ == "__main__": 
    main()