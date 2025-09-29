import logging 
import os 
import sys 
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.ext import Application, CommandHandler, InlineQueryHandler, ContextTypes, ChosenInlineResultHandler
import uuid 
import hashlib 

# Configuration 
BOT_TOKEN = os.getenv('BOT_TOKEN', '').strip() 
AUTH_CODE = os.getenv('AUTH_CODE', '1234').strip() 
WEBAPP_URL = os.getenv('WEBAPP_URL', 'https://fragment.com/username').strip()

# Setup logging DETAILED
logging.basicConfig( 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.DEBUG  # Ganti ke DEBUG untuk detail lebih
) 
logger = logging.getLogger(__name__) 

# --- Fungsi Utility ---
def generate_unique_id(user_id: int, query: str) -> str: 
    unique_string = f"{user_id}_{query}_{uuid.uuid4()}" 
    return hashlib.md5(unique_string.encode()).hexdigest() 

def create_webapp_url(username: str) -> str:
    return f"{WEBAPP_URL}?username={username}&source=bot&auth={AUTH_CODE}"

def create_detail_button(username: str) -> InlineKeyboardMarkup:
    """Buat tombol view detail"""
    web_app_url = create_webapp_url(username)
    logger.info(f"Creating WebApp button with URL: {web_app_url}")
    
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(
            text="🔍 View Details in Web App", 
            web_app=WebAppInfo(url=web_app_url)
        )
    ]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    if not update.message: 
        return 
         
    bot_username = (await context.bot.get_me()).username 
     
    welcome_text = ( 
        "👋 **Fragment Authentication Bot**\n\n" 
        "**Cara menggunakan:**\n" 
        f"1. Ketik `@{bot_username} {AUTH_CODE} username_target` di chat manapun\n" 
        f"2. Contoh: `@{bot_username} {AUTH_CODE} Sui_panda`\n" 
        f"3. Pilih hasil dari bot dan kirim ke chat\n" 
        f"4. **Tombol akan muncul otomatis**\n\n" 
        f"**Kode auth:** `{AUTH_CODE}`\n"
        f"**Web App URL:** `{WEBAPP_URL}`\n"
    ) 
     
    try: 
        await update.message.reply_text(welcome_text, parse_mode="Markdown") 
    except Exception as e: 
        logger.error(f"Failed to send /start message: {e}") 

# --- Handler Inline Query ---
async def handle_inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    if not update.inline_query: 
        return 
         
    query = update.inline_query.query.strip() 
    user = update.inline_query.from_user 
    user_id = user.id 
     
    logger.info(f"🔍 INLINE QUERY from {user_id}: '{query}'") 
     
    results = [] 
     
    # CASE 4: Query KOSONG
    if not query:
        logger.info("📝 Showing instructions for empty query")
        results.append( 
            InlineQueryResultArticle( 
                id="instructions_empty",
                title="🔐 AUTHENTICATION REQUIRED", 
                description=f"Type: {AUTH_CODE} username", 
                input_message_content=InputTextMessageContent( 
                    message_text=( 
                        "🔐 <b>Fragment Authentication Bot</b>\n\n" 
                        f"<b>Format:</b> @bot_username {AUTH_CODE} username_target\n\n" 
                        f"<b>Example:</b> @bot_username {AUTH_CODE} Sui_panda"
                    ), 
                    parse_mode="HTML" 
                ) 
            ) 
        )
        
        await update.inline_query.answer(results, cache_time=300, is_personal=True)
        return
     
    # Parse query
    parts = query.split(' ', 1)  
    auth_code_part = parts[0] if parts else ""
    username_part = parts[1].strip() if len(parts) > 1 else ""
    
    logger.info(f"🔍 Parsed - Code: '{auth_code_part}', Username: '{username_part}'")
    
    # CASE 3: Kode SALAH
    if auth_code_part != AUTH_CODE:
        logger.info(f"❌ Wrong code provided: '{auth_code_part}'")
        results.append( 
            InlineQueryResultArticle( 
                id=f"wrong_{auth_code_part}",
                title="❌ AUTHENTICATION FAILED", 
                description=f"Wrong code! Click for instructions", 
                input_message_content=InputTextMessageContent( 
                    message_text=( 
                        "❌ <b>Authentication Failed</b>\n\n" 
                        f"Kode: <code>{auth_code_part}</code>\n" 
                        f"Kode benar: <code>{AUTH_CODE}</code>"
                    ), 
                    parse_mode="HTML" 
                ) 
            ) 
        )
        
        await update.inline_query.answer(results, cache_time=60, is_personal=True)
        return
         
    # CASE 2: Kode BENAR tapi tidak ada username
    if not username_part: 
        logger.info("📝 Correct code but no username")
        results.append( 
            InlineQueryResultArticle( 
                id="need_username",
                title="🔐 USERNAME REQUIRED", 
                description="Add target username after the code", 
                input_message_content=InputTextMessageContent( 
                    message_text=( 
                        "🔐 <b>Username Required</b>\n\n" 
                        f"Kode <code>{AUTH_CODE}</code> benar! ✅\n\n" 
                        f"Format: @bot_username {AUTH_CODE} username_target"
                    ), 
                    parse_mode="HTML" 
                ) 
            ) 
        )
        
        await update.inline_query.answer(results, cache_time=60, is_personal=True)
        return
         
    # CASE 1: Kode BENAR dan ada username - SUKSES
    target_username = username_part 
    logger.info(f"✅ SUCCESS - Code correct, username: '{target_username}'") 
     
    # Format pesan SEMENTARA
    message_text = ( 
        "🔐 <b>Fragment Authentication</b>\n\n" 
        f"📧 <b>Username:</b> <code>{target_username}</code>\n" 
        f"✅ <b>Status:</b> Authenticated\n" 
        f"🔑 <b>Auth Code:</b> <code>{AUTH_CODE}</code>\n\n" 
        f"<i>Loading button...</i>" 
    )
     
    results.append( 
        InlineQueryResultArticle( 
            id=f"correct_{target_username}",
            title="✅ FRAGMENT AUTHENTICATION", 
            description=f"Username: {target_username} - Tap to send", 
            input_message_content=InputTextMessageContent( 
                message_text=message_text, 
                parse_mode="HTML" 
            )
        ) 
    )
     
    try: 
        await update.inline_query.answer(results, cache_time=1, is_personal=True) 
        logger.info(f"📤 Sent inline results for '{target_username}'") 
    except Exception as e: 
        logger.error(f"❌ Error answering inline query: {e}") 

# --- Handler untuk ketika user memilih hasil inline ---
async def handle_chosen_inline_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.chosen_inline_result:
        return
        
    chosen_result = update.chosen_inline_result
    result_id = chosen_result.result_id
    user_id = chosen_result.from_user.id
    inline_message_id = chosen_result.inline_message_id
    
    logger.info(f"🎯 CHOSEN INLINE: user_id={user_id}, result_id='{result_id}', inline_message_id='{inline_message_id}'")
    
    # Cek jika ini adalah hasil sukses
    if result_id.startswith("correct_"):
        username = result_id.replace("correct_", "", 1)
        logger.info(f"🔄 Processing successful auth for username: {username}")
        
        # Buat tombol details
        detail_button = create_detail_button(username)
        
        # Pesan FINAL dengan tombol
        final_message = ( 
            "🔐 <b>Fragment Authentication</b>\n\n" 
            f"📧 <b>Username:</b> <code>{username}</code>\n" 
            f"✅ <b>Status:</b> Authenticated\n" 
            f"🔑 <b>Auth Code:</b> <code>{AUTH_CODE}</code>\n\n" 
            f"<i>Click button below to open Web App</i>" 
        )
        
        try:
            # Edit pesan yang sudah terkirim
            await context.bot.edit_message_text(
                message_text=final_message,
                inline_message_id=inline_message_id,
                parse_mode="HTML",
                reply_markup=detail_button
            )
            logger.info(f"✅ SUCCESS: Added button for username '{username}'")
        except Exception as e:
            logger.error(f"❌ FAILED to edit message: {e}")
            # Coba log error detail
            logger.error(f"❌ Error type: {type(e).__name__}")
            logger.error(f"❌ Error args: {e.args}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    logger.error(f"🚨 BOT ERROR: {context.error}", exc_info=context.error) 

def main(): 
    # Validasi Environment Variables
    if not BOT_TOKEN:
        logger.error("🚨 BOT_TOKEN not found!")
        sys.exit(1)
        
    if not WEBAPP_URL:
        logger.warning("⚠️ WEBAPP_URL not set, buttons may not work properly")
         
    logger.info("🤖 Starting Fragment Authentication Bot") 
    logger.info(f"🔑 AUTH_CODE: {AUTH_CODE}") 
    logger.info(f"🌐 WEBAPP_URL: {WEBAPP_URL}")
    logger.info(f"🤖 BOT_TOKEN: {BOT_TOKEN[:10]}...")  # Log partial token for security
 
    application = Application.builder().token(BOT_TOKEN).build() 
     
    # Register handlers
    application.add_handler(CommandHandler("start", start)) 
    application.add_handler(InlineQueryHandler(handle_inline_query)) 
    application.add_handler(ChosenInlineResultHandler(handle_chosen_inline_result))
    application.add_error_handler(error_handler) 
     
    logger.info("🔄 Bot starting in polling mode...") 
    
    try:
        application.run_polling()
    except Exception as e:
        logger.error(f"🚨 Failed to start bot: {e}")
        sys.exit(1)

if __name__ == "__main__": 
    main()