import logging
import os
import sys # Import sys untuk exit jika token tidak ada
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InlineQueryResultArticle, InputTextMessageContent, error
from telegram.ext import Application, CommandHandler, InlineQueryHandler, CallbackQueryHandler, ContextTypes
import uuid

# --- 1. Konfigurasi dari Environment Variables ---
BOT_TOKEN = os.getenv('BOT_TOKEN', '').strip()
# Menggunakan default set kosong untuk OWNER_IDS jika tidak ada di env
OWNER_IDS_STR = os.getenv('OWNER_IDS', '').strip()
AUTH_CODE = os.getenv('AUTH_CODE', '1234').strip()
PORT = int(os.getenv('PORT', 8443))
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '').strip()

# --- 2. Setup Logging ---
# Atur format logging yang lebih terperinci
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- 3. Parsing OWNER_IDS dengan Penanganan Error yang Lebih Baik ---
OWNER_IDS = set()
if OWNER_IDS_STR:
    # Memastikan setiap ID adalah integer dan mengabaikan string kosong
    try:
        OWNER_IDS = set(map(int, [x.strip() for x in OWNER_IDS_STR.split(',') if x.strip()]))
        logger.info(f"Successfully parsed OWNER_IDS: {OWNER_IDS}")
    except ValueError as e:
        logger.error(f"Error parsing OWNER_IDS. Ensure all IDs are valid integers separated by commas. Error: {e}")
        # OWNER_IDS tetap set kosong, tapi logged error.

# --- 4. Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /start. Lebih konsisten dalam penamaan variabel dan pengecekan."""
    if not update.message:
        return
        
    user = update.effective_user
    user_id = user.id
    is_owner = user_id in OWNER_IDS
    
    welcome_text = (
        "👋 **Fragment Authentication Bot**\n\n"
        "**Untuk Owner:**\n"
        f"• Ketik `@{(await context.bot.get_me()).username} {AUTH_CODE}` di chat manapun\n"
        "• Ganti kode autentikasi dengan yang terdaftar\n\n"
        "**Fitur:**\n"
        "• Direct username offer\n"
        "• Secure fragment authentication\n"
        "• Interactive buttons\n\n"
    )
    
    if is_owner:
        welcome_text += "✅ **Status:** Anda terverifikasi sebagai Owner"
    else:
        welcome_text += "❌ **Status:** Akses terbatas (Owner only)"
    
    # Menambahkan error handling untuk reply_text
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
    username = user.username or user.first_name # Menggunakan first_name jika username tidak ada
    
    logger.info(f"Inline query from {user_id} (@{username}): '{query}'")
    
    results = []
    
    # 1. Jika user adalah owner dan mengirim kode yang benar
    if user_id in OWNER_IDS and query == AUTH_CODE:
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
                    # Link ke t.me/username hanya jika username ada, jika tidak, gunakan user_id (optional)
                    [InlineKeyboardButton("👤 Contact Owner", url=f"https://t.me/{user.username}" if user.username else f"tg://user?id={user_id}")]
                ])
            )
        )
    # 2. Jika owner tapi belum input kode
    elif user_id in OWNER_IDS and query == "":
        results.append(
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="🔐 Authentication Required",
                description=f"Input code: {AUTH_CODE}",
                input_message_content=InputTextMessageContent(
                    message_text="⚠️ **Authentication Required**\n\nPlease input your authentication code after @username_bot",
                    parse_mode="Markdown"
                )
            )
        )
    # 3. Jika bukan owner atau kode salah
    else:
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
    
    try:
        # Menambahkan parameter is_personal=True, memungkinkan bot untuk menampilkan hasil yang berbeda untuk setiap pengguna
        await update.inline_query.answer(results, cache_time=0, is_personal=True)
        logger.info(f"Successfully answered inline query for user {user_id}")
    except error.TelegramError as e:
        # Pengecualian spesifik untuk TelegramError
        logger.error(f"Error answering inline query for user {user_id}: {e}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk tombol callback"""
    if not update.callback_query:
        return
        
    query = update.callback_query
    user = query.from_user
    user_id = user.id
    callback_data = query.data
    
    # Selalu coba answer callback query dulu, mencegah "Waiting for server response"
    try:
        await query.answer()
    except error.TelegramError as e:
        logger.error(f"Error answering callback query from user {user_id}: {e}")
        return
    
    if callback_data.startswith("view_detail_"):
        try:
            target_user_id = int(callback_data.split("_")[2])
            username = user.username or user.first_name
            
            # Verifikasi bahwa user yang menekan tombol adalah owner yang sesuai DAN ID di data cocok
            if user_id == target_user_id and user_id in OWNER_IDS:
                
                # Menggunakan query.message.edit_date jika ada untuk timestamp
                timestamp = query.message.edit_date.strftime('%Y-%m-%d %H:%M:%S UTC') if query.message.edit_date else query.message.date.strftime('%Y-%m-%d %H:%M:%S UTC')

                detail_text = (
                    f"🔒 **Fragment Authentication Details**\n\n"
                    f"**Username:** @{username}\n"
                    f"**User ID:** `{user_id}`\n"
                    f"**Owner ID:** `{target_user_id}`\n" # Tambahkan Owner ID
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
                        [InlineKeyboardButton("🔙 Back", callback_data=f"back_to_main_{target_user_id}"), # Kirim target_user_id kembali
                         InlineKeyboardButton("❌ Close", callback_data="close")]
                    ])
                )
            else:
                # Menampilkan alert hanya jika user_id tidak cocok atau bukan owner
                alert_msg = "❌ Akses Ditolak: Anda tidak memiliki izin untuk melihat detail ini."
                if user_id in OWNER_IDS:
                    alert_msg = "❌ Error: Detail ini hanya untuk user yang membuat offer."
                
                await query.answer(alert_msg, show_alert=True)
        except (ValueError, IndexError, error.TelegramError) as e:
            logger.error(f"Error in view_detail for user {user_id}: {e}")
            await query.answer("❌ Error loading details", show_alert=True)
        
    elif callback_data.startswith("back_to_main_"):
        try:
            target_user_id = int(callback_data.split("_")[3])
            
            # Cek keamanan kembali, hanya owner yang bisa kembali
            if user_id != target_user_id or user_id not in OWNER_IDS:
                 await query.answer("❌ Akses Ditolak", show_alert=True)
                 return
                 
            username = user.username or user.first_name
            
            await query.edit_message_text(
                text=f"🔐 **Fragment Authentication**\n\nDirect offer to sell your username @{username}",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📋 View Detail", callback_data=f"view_detail_{user_id}")],
                    [InlineKeyboardButton("👤 Contact Owner", url=f"https://t.me/{user.username}" if user.username else f"tg://user?id={user_id}")]
                ])
            )
        except (ValueError, IndexError, error.TelegramError) as e:
            logger.error(f"Error in back_to_main for user {user_id}: {e}")
            await query.answer("❌ Error: Gagal kembali ke menu utama", show_alert=True)
        
    elif callback_data == "close":
        try:
            # Perbaiki: Pastikan hanya owner yang bisa menghapus pesan yang dibuatnya sendiri.
            # Namun, karena pesan inline dapat dibuat oleh siapa saja (tapi isinya dari owner),
            # kita izinkan semua user menghapus pesan yang mereka tekan tombol close-nya.
            await query.message.delete()
        except error.BadRequest as e:
            # Error yang umum terjadi jika pesan sudah dihapus atau bot tidak memiliki izin
            logger.warning(f"Failed to delete message (already deleted or permissions issue) for user {user_id}: {e}")
        except error.TelegramError as e:
            logger.error(f"Error deleting message for user {user_id}: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk error logging. Menambahkan detail error lebih lanjut."""
    
    # Memberikan notifikasi pada user jika ada update, jika tidak log error saja
    if update and update.effective_chat:
        logger.error(f"Error processing update in chat {update.effective_chat.id}: {context.error}", exc_info=context.error)
        try:
            # Opsional: Kirim pesan error ke owner atau chat user (hati-hati dengan spam)
            # await context.bot.send_message(chat_id=OWNER_IDS.pop() if OWNER_IDS else update.effective_chat.id, text=f"⚠️ Bot encountered an error: {context.error}")
            pass
        except error.TelegramError:
             logger.warning(f"Could not send error message to chat {update.effective_chat.id}")
    else:
        logger.error(f"Error occurred: {context.error}", exc_info=context.error)

def main():
    """Main function untuk menjalankan bot"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN tidak ditemukan! Pastikan sudah di-set di environment variables.")
        # Keluar dari program secara eksplisit jika token tidak ada
        sys.exit(1)
        
    if not OWNER_IDS:
        logger.warning("OWNER_IDS kosong! Bot hanya akan berfungsi untuk inline query yang tidak terautentikasi.")
    
    logger.info(f"Bot starting with OWNER_IDS: {OWNER_IDS}")
    logger.info(f"Authentication code: {AUTH_CODE}")

    # Create application
    # Menambahkan write_timeout untuk keandalan webhook
    application = Application.builder().token(BOT_TOKEN).pool_timeout(60).write_timeout(60).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(InlineQueryHandler(handle_inline_query))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_error_handler(error_handler)
    
    # Run bot
    if WEBHOOK_URL:
        logger.info(f"Running with webhook on port {PORT}. URL: {WEBHOOK_URL}/{BOT_TOKEN}")
        try:
            application.run_webhook(
                listen="0.0.0.0",
                port=PORT,
                url_path=BOT_TOKEN,
                webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}"
            )
        except Exception as e:
            # Jika webhook gagal total (misalnya, masalah port atau sertifikat)
            logger.error(f"FATAL Webhook error: {e}. Falling back to polling is NOT recommended for Railway, please check your webhook configuration.")
            sys.exit(1) # Keluar karena environment Railway seharusnya menggunakan webhook
    else:
        logger.info("Running with polling...")
        application.run_polling(poll_interval=1.0, timeout=20)

if __name__ == "__main__":
    main()