import logging
import os
import sys
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.ext import Application, CommandHandler, InlineQueryHandler, ContextTypes
import uuid
import hashlib

# Configuration 
# Pastikan nilai ini benar dan sudah diatur di BotFather
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

# --- Handler Command /start ---
# (Tetap sama, hanya untuk panduan)
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
        f"**Tombol Web App akan terkirim bersama pesan.**\n\n" 
        f"**Format:** `@{bot_username} [kode] [username]`\n" 
        f"**Kode auth:** `{AUTH_CODE}`\n"
    ) 
      
    try: 
        await update.message.reply_text(welcome_text, parse_mode="Markdown") 
    except Exception as e: 
        logger.error(f"Failed to send /start message: {e}") 

# --- Handler Inline Query (Penting!) ---
async def handle_inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    """Handler untuk inline query (@bot)""" 
    if not update.inline_query: 
        return 
          
    query = update.inline_query.query.strip() 
    user = update.inline_query.from_user 
    user_id = user.id 
      
    logger.info(f"Inline query from {user_id}: query='{query}'") 
      
    results = [] 
      
    # --- Kode otorisasi (Case 4, 3, 2) lainnya diabaikan di sini untuk fokus ke Case 1 ---
    # *Jalankan logika otorisasi Anda di sini*

    # --- PENTING: CASE 1 (Otorisasi Sukses) ---
    # Jika otorisasi/parsing sukses, asumsikan 'target_username' sudah didapat:
    
    parts = query.split(' ', 1)
    auth_code_part = parts[0] if parts else ""
    username_part = parts[1].strip() if len(parts) > 1 else ""

    if auth_code_part == AUTH_CODE and username_part:
        target_username = username_part
        logger.info(f"User {user_id} provided CORRECT code and username: '{target_username}'") 
          
        # 1. BUAT TOMBOL WEB APP
        # Tombol ini akan langsung muncul di pesan yang dikirim
        webapp_button_markup = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                text="🔍 Open Web App Details", 
                web_app=WebAppInfo(url=create_webapp_url(target_username))
            )
        ]])

        # 2. FORMAT PESAN
        message_text = ( 
            "🔐 <b>Fragment Authentication</b>\n\n" 
            f"📧 <b>Username:</b> <code>{target_username}</code>\n" 
            f"✅ <b>Status:</b> Authenticated\n" 
            f"🔑 <b>Auth Code:</b> <code>{AUTH_CODE}</code>\n\n" 
            f"<i>Tap tombol di bawah untuk melihat details.</i>" 
        )
          
        # 3. BUAT HASIL INLINE DENGAN TOMBOL
        results.append( 
            InlineQueryResultArticle( 
                id=generate_unique_id(user_id, target_username), # ID harus unik
                title=f"✅ Send Auth for @{target_username}",  # Teks "Tap to Send"
                description=f"Open Web App for: {target_username}", 
                input_message_content=InputTextMessageContent( 
                    message_text=message_text, 
                    parse_mode="HTML" 
                ),
                # ✅ KUNCI: Tambahkan reply_markup ke InlineQueryResultArticle
                reply_markup=webapp_button_markup, 
                thumbnail_url="https://img.icons8.com/fluency/96/verified-badge.png"
            ) 
        )
    else:
        # Jika kode salah atau format kurang, berikan hasil instruksi
        results.append( 
            InlineQueryResultArticle( 
                id=generate_unique_id(user_id, "instructions"),
                title="🔐 AUTHENTICATION REQUIRED", 
                description=f"Type: {AUTH_CODE} username", 
                input_message_content=InputTextMessageContent( 
                    message_text="Gunakan format yang benar: `kode username`", 
                    parse_mode="Markdown" 
                ) 
            ) 
        )

    try: 
        # Kirim hasil inline query
        await update.inline_query.answer(results, cache_time=1, is_personal=True) 
        logger.info(f"Successfully answered inline query with {len(results)} results.") 
    except Exception as e: 
        logger.error(f"Error answering inline query: {e}") 

# --- Handler Error ---
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    """Handler untuk error logging""" 
    logger.error(f"Error: {context.error}", exc_info=context.error) 

# --- Main Function ---
def main(): 
    """Main function""" 
    if not BOT_TOKEN: 
        logger.error("BOT_TOKEN tidak ditemukan!") 
        sys.exit(1) 
          
    logger.info(f"Starting Fragment Authentication Bot") 
      
    application = Application.builder().token(BOT_TOKEN).build() 
      
    application.add_handler(CommandHandler("start", start)) 
    application.add_handler(InlineQueryHandler(handle_inline_query)) 
    application.add_error_handler(error_handler) 
      
    logger.info("Bot started in polling mode...") 
    application.run_polling() 

if __name__ == "__main__": 
    main()