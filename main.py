import os
import logging
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.ext import Application, CommandHandler, InlineQueryHandler, ContextTypes

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', '').strip()
WEBAPP_URL = os.getenv('WEBAPP_URL', 'https://fragment.com').strip()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Simple start command"""
    welcome_text = (
        "🤖 **Web App Bot**\n\n"
        "**Cara pakai:**\n"
        "1. Ketik `@bot_username test` di chat manapun\n"
        "2. Pilih hasil yang muncul\n"
        "3. Tombol Web App akan langsung muncul!\n\n"
        "**Contoh:** `@bot_username test`"
    )
    
    if update.message:
        await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def handle_inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Simple inline query handler dengan Web App button"""
    if not update.inline_query:
        return

    query = update.inline_query.query.strip().lower()
    user_id = update.inline_query.from_user.id
    
    logger.info(f"Inline query from {user_id}: '{query}'")

    results = []

    # Jika user ketik "test" atau query apapun
    if query:
        # Buat tombol Web App
        web_app_button = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                text="🚀 Buka Web App", 
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        ]])

        # Buat hasil inline
        results.append(
            InlineQueryResultArticle(
                id="webapp_result",
                title="📱 Buka Web App Saya",
                description="Klik untuk mengirim pesan dengan tombol Web App",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        "🔗 **Akses Web App Saya**\n\n"
                        "Klik tombol di bawah ini untuk membuka Web App langsung di Telegram:"
                    ),
                    parse_mode="Markdown"
                ),
                reply_markup=web_app_button  # ✅ Tombol langsung di sini!
            )
        )
    else:
        # Jika query kosong, beri instruksi
        results.append(
            InlineQueryResultArticle(
                id="instructions",
                title="📝 Cara Pakai Bot",
                description="Ketik 'test' untuk mencoba Web App",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        "🤖 **Web App Bot**\n\n"
                        "Ketik `@bot_username test` untuk mencoba Web App!"
                    ),
                    parse_mode="Markdown"
                )
            )
        )

    try:
        await update.inline_query.answer(results, cache_time=0, is_personal=True)
        logger.info(f"Sent {len(results)} results to user {user_id}")
    except Exception as e:
        logger.error(f"Error: {e}")

def main():
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN tidak ditemukan!")
        return

    logger.info("🤖 Starting Simple Web App Bot...")
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(InlineQueryHandler(handle_inline_query))
    
    logger.info("🔄 Bot running in polling mode...")
    application.run_polling()

if __name__ == "__main__":
    main()