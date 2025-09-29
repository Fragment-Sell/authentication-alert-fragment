import logging 
import os 
import sys 
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.ext import Application, CommandHandler, InlineQueryHandler, ContextTypes 
import uuid 
import hashlib 

# Configuration 
BOT_TOKEN = os.getenv('BOT_TOKEN', '').strip() 
AUTH_CODE = os.getenv('AUTH_CODE', '1234').strip() 
WEBAPP_URL = os.getenv('WEBAPP_URL', 'https://fragment.com/username').strip()

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

def create_webapp_button(username: str) -> InlineKeyboardMarkup:
    """Buat tombol webapp dengan username sebagai parameter"""
    webapp_url = f"{WEBAPP_URL}?username={username}&source=bot"
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(
            text="🔗 Buka di Web App", 
            web_app=WebAppInfo(url=webapp_url)
        )
    ]])

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
        f"**Web App:** {WEBAPP_URL}\n"
    ) 
     
    try: 
        await update.message.reply_text(welcome_text, parse_mode="Markdown") 
    except Exception as e: 
        logger.error(f"Failed to send /start message: {e}") 

# --- Handler Inline Query dengan Urutan yang Dioptimalkan ---
async def handle_inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    """Handler untuk inline query (@bot) dengan urutan logika yang optimal""" 
    if not update.inline_query: 
        return 
         
    query = update.inline_query.query.strip() 
    user = update.inline_query.from_user 
    user_id = user.id 
     
    logger.info(f"Inline query from {user_id}: query='{query}'") 
     
    results = [] 
     
    # CASE 4: Query KOSONG - Tampilkan instruksi (PALING SEDERHANA)
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
                        f"• @username_bot {AUTH_CODE} Alice_Smith\n\n"
                        f"<i>Klik contoh di atas untuk mencoba!</i>"
                    ), 
                    parse_mode="HTML" 
                ) 
            ) 
        )
        
        await update.inline_query.answer(results, cache_time=300, is_personal=True)
        return
     
    # Parse query setelah memastikan query tidak kosong
    parts = query.split(' ', 1)  
    auth_code_part = parts[0] if parts else ""
    username_part = parts[1].strip() if len(parts) > 1 else ""
    
    # CASE 3: Kode SALAH - Validasi kode (PRIORITAS TINGGI)
    if auth_code_part != AUTH_CODE:
        logger.info(f"User {user_id} provided WRONG code: '{auth_code_part}'")
         
        # Berikan saran jika kode mirip
        suggestion = ""
        if auth_code_part and len(auth_code_part) == len(AUTH_CODE):
            suggestion = "\n\n💡 <i>Kode hampir benar! Periksa kembali.</i>"
        elif auth_code_part:
            suggestion = f"\n\n💡 <i>Kode seharusnya {len(AUTH_CODE)} digit.</i>"
            
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
                        f"<b>Format yang benar:</b>\n"
                        f"<code>@{ (await context.bot.get_me()).username } {AUTH_CODE} username_target</code>"
                        f"{suggestion}"
                    ), 
                    parse_mode="HTML" 
                ) 
            ) 
        )
        
        await update.inline_query.answer(results, cache_time=60, is_personal=True)
        return
         
    # CASE 2: Kode BENAR tapi tidak ada username - Minta input username
    if not username_part: 
        logger.info(f"User {user_id} provided CORRECT code but no username") 
         
        results.append( 
            InlineQueryResultArticle( 
                id=generate_unique_id(user_id, "need_username"),
                title="🔐 USERNAME REQUIRED", 
                description="Add target username after the code", 
                input_message_content=InputTextMessageContent( 
                    message_text=( 
                        "🔐 <b>Username Required</b>\n\n" 
                        f"Kode auth <code>{AUTH_CODE}</code> benar! ✅\n\n" 
                        f"Sekarang tambahkan username target setelah kode.\n\n" 
                        f"<b>Format:</b> @username_bot {AUTH_CODE} username_target\n" 
                        f"<b>Example:</b> @username_bot {AUTH_CODE} Sui_panda\n\n"
                        f"<i>Ketik username setelah kode {AUTH_CODE}...</i>"
                    ), 
                    parse_mode="HTML" 
                ) 
            ) 
        )
        
        await update.inline_query.answer(results, cache_time=60, is_personal=True)
        return
         
    # CASE 1: Kode BENAR dan ada username - Tampilkan Fragment Authentication (SUCCESS)
    target_username = username_part 
    logger.info(f"User {user_id} provided CORRECT code and username: '{target_username}'") 
     
    escaped_username = escape_username(target_username) 
     
    # Format pesan dengan HTML parsing + Tombol Web App
    message_text = ( 
        "🔐 <b>Fragment Authentication</b>\n\n" 
        f"Direct offer to sell your username: <code>{target_username}</code>\n\n" 
        f"<b>Status:</b> ✅ Authenticated\n" 
        f"<b>Target:</b> {escaped_username}\n" 
        f"<b>Auth Code:</b> <code>{AUTH_CODE}</code>\n\n" 
        f"<i>Klik tombol di bawah untuk membuka Web App</i>" 
    )
    
    # Buat tombol webapp
    reply_markup = create_webapp_button(target_username)
     
    results.append( 
        InlineQueryResultArticle( 
            id=generate_unique_id(user_id, f"correct_{target_username}"),
            title="✅ FRAGMENT AUTHENTICATION", 
            description=f"Offer for: {target_username} - Tap to send", 
            input_message_content=InputTextMessageContent( 
                message_text=message_text, 
                parse_mode="HTML" 
            ), 
            reply_markup=reply_markup,
            thumbnail_url="https://img.icons8.com/fluency/96/verified-badge.png"
        ) 
    )
     
    try: 
        await update.inline_query.answer(results, cache_time=1, is_personal=True) 
        logger.info(f"Successfully sent {len(results)} results to user {user_id}") 
    except Exception as e: 
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
    logger.info(f"WEBAPP_URL: {WEBAPP_URL}")
 
    application = Application.builder().token(BOT_TOKEN).build() 
     
    application.add_handler(CommandHandler("start", start)) 
    application.add_handler(InlineQueryHandler(handle_inline_query)) 
    application.add_error_handler(error_handler) 
     
    # Simple polling mode
    logger.info("Bot started in polling mode...") 
    application.run_polling() 

if __name__ == "__main__": 
    main()