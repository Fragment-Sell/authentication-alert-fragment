import logging 
import os 
import sys 
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.ext import Application, CommandHandler, InlineQueryHandler, ContextTypes, CallbackQueryHandler
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

def create_webapp_url(username: str) -> str:
    """Buat URL webapp dengan parameter"""
    return f"{WEBAPP_URL}?username={username}&source=bot&auth={AUTH_CODE}"

def create_detail_button(username: str, message_id: str) -> InlineKeyboardMarkup:
    """Buat tombol view detail untuk pesan yang sudah terkirim"""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(
            text="🔍 View Details in Web App", 
            web_app=WebAppInfo(url=create_webapp_url(username))
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
        f"1. Ketik `@{bot_username} {AUTH_CODE} username_target` di chat manapun\n" 
        f"2. Contoh: `@{bot_username} {AUTH_CODE} Sui_panda`\n" 
        f"3. Pilih hasil dari bot dan kirim ke chat\n" 
        f"4. **Tombol 'View Details' akan muncul otomatis** setelah pesan terkirim\n\n" 
        f"**Format:** `@{bot_username} [kode] [username]`\n" 
        f"**Kode auth:** `{AUTH_CODE}`\n"
    ) 
     
    try: 
        await update.message.reply_text(welcome_text, parse_mode="Markdown") 
    except Exception as e: 
        logger.error(f"Failed to send /start message: {e}") 

# --- Handler Inline Query (TANPA TOMBOL di inline results) ---
async def handle_inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    """Handler untuk inline query (@bot)""" 
    if not update.inline_query: 
        return 
         
    query = update.inline_query.query.strip() 
    user = update.inline_query.from_user 
    user_id = user.id 
     
    logger.info(f"Inline query from {user_id}: query='{query}'") 
     
    results = [] 
     
    # CASE 4: Query KOSONG - Tampilkan instruksi
    if not query:
        logger.info(f"User {user_id} provided EMPTY query - showing instructions")
         
        results.append( 
            InlineQueryResultArticle( 
                id=generate_unique_id(user_id, "instructions"),
                title="🔐 AUTHENTICATION REQUIRED", 
                description=f"Type: {AUTH_CODE} username", 
                input_message_content=InputTextMessageContent( 
                    message_text=( 
                        "🔐 <b>Fragment Authentication Bot</b>\n\n" 
                        f"<b>Format:</b> <code>@{ (await context.bot.get_me()).username } {AUTH_CODE} username_target</code>\n\n" 
                        f"<b>Contoh:</b>\n" 
                        f"• <code>@{ (await context.bot.get_me()).username } {AUTH_CODE} Sui_panda</code>\n" 
                        f"• <code>@{ (await context.bot.get_me()).username } {AUTH_CODE} John_Doe</code>\n\n"
                        f"<i>Gunakan format di atas untuk memulai</i>"
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
    
    # CASE 3: Kode SALAH
    if auth_code_part != AUTH_CODE:
        logger.info(f"User {user_id} provided WRONG code: '{auth_code_part}'")
         
        results.append( 
            InlineQueryResultArticle( 
                id=generate_unique_id(user_id, f"wrong_{auth_code_part}"),
                title="❌ AUTHENTICATION FAILED", 
                description=f"Wrong code! Click for instructions", 
                input_message_content=InputTextMessageContent( 
                    message_text=( 
                        "❌ <b>Authentication Failed</b>\n\n" 
                        f"Kode yang dimasukkan: <code>{auth_code_part}</code>\n" 
                        f"Kode yang benar: <code>{AUTH_CODE}</code>\n\n" 
                        f"<b>Format yang benar:</b>\n"
                        f"<code>@{ (await context.bot.get_me()).username } {AUTH_CODE} username_target</code>"
                    ), 
                    parse_mode="HTML" 
                ) 
            ) 
        )
        
        await update.inline_query.answer(results, cache_time=60, is_personal=True)
        return
         
    # CASE 2: Kode BENAR tapi tidak ada username
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
                        f"Tambahkan username target setelah kode:\n\n" 
                        f"<b>Format:</b> <code>@{ (await context.bot.get_me()).username } {AUTH_CODE} username_target</code>\n" 
                        f"<b>Example:</b> <code>@{ (await context.bot.get_me()).username } {AUTH_CODE} Sui_panda</code>"
                    ), 
                    parse_mode="HTML" 
                ) 
            ) 
        )
        
        await update.inline_query.answer(results, cache_time=60, is_personal=True)
        return
         
    # CASE 1: Kode BENAR dan ada username - SUKSES
    target_username = username_part 
    logger.info(f"User {user_id} provided CORRECT code and username: '{target_username}'") 
     
    escaped_username = escape_username(target_username) 
     
    # Format pesan CLEAN tanpa tombol di inline results
    message_text = ( 
        "🔐 <b>Fragment Authentication</b>\n\n" 
        f"📧 <b>Username:</b> <code>{target_username}</code>\n" 
        f"✅ <b>Status:</b> Authenticated\n" 
        f"🔑 <b>Auth Code:</b> <code>{AUTH_CODE}</code>\n\n" 
        f"<i>Tombol details akan muncul setelah pesan ini terkirim...</i>" 
    )
     
    results.append( 
        InlineQueryResultArticle( 
            id=generate_unique_id(user_id, f"correct_{target_username}"),
            title="✅ FRAGMENT AUTHENTICATION", 
            description=f"Offer for: {target_username} - Tap to send", 
            input_message_content=InputTextMessageContent( 
                message_text=message_text, 
                parse_mode="HTML" 
            ),
            thumbnail_url="https://img.icons8.com/fluency/96/verified-badge.png"
        ) 
    )
     
    try: 
        await update.inline_query.answer(results, cache_time=1, is_personal=True) 
        logger.info(f"Successfully sent authentication result for '{target_username}' to user {user_id}") 
    except Exception as e: 
        logger.error(f"Error answering inline query: {e}") 

# --- NEW: Handler untuk menambahkan tombol setelah pesan terkirim ---
async def handle_chosen_inline_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler dipanggil ketika user memilih/mengirim hasil inline query"""
    if not update.chosen_inline_result:
        return
        
    chosen_result = update.chosen_inline_result
    result_id = chosen_result.result_id
    user_id = chosen_result.from_user.id
    message_id = chosen_result.inline_message_id
    
    logger.info(f"User {user_id} chosen inline result: {result_id}")
    
    # Cek jika ini adalah hasil sukses (Case 1)
    if result_id.startswith("correct_"):
        # Extract username dari result_id (format: "correct_username")
        username = result_id.replace("correct_", "", 1)
        
        # Buat tombol details
        detail_button = create_detail_button(username, message_id)
        
        # Update pesan yang sudah terkirim dengan menambahkan tombol
        try:
            await context.bot.edit_message_text(
                message_text=(
                    "🔐 <b>Fragment Authentication</b>\n\n" 
                    f"📧 <b>Username:</b> <code>{username}</code>\n" 
                    f"✅ <b>Status:</b> Authenticated\n" 
                    f"🔑 <b>Auth Code:</b> <code>{AUTH_CODE}</code>\n\n" 
                    f"<i>Klik tombol di bawah untuk melihat details di Web App</i>"
                ),
                chat_id=None,  # Untuk inline messages
                message_id=message_id,
                parse_mode="HTML",
                reply_markup=detail_button
            )
            logger.info(f"Successfully added detail button for username '{username}'")
        except Exception as e:
            logger.error(f"Failed to add detail button: {e}")

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
    # NEW: Tambahkan handler untuk chosen inline result
    application.add_handler(CallbackQueryHandler(handle_chosen_inline_result))
    application.add_error_handler(error_handler) 
     
    logger.info("Bot started in polling mode...") 
    application.run_polling() 

if __name__ == "__main__": 
    main()