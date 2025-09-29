import logging
from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, InlineQueryHandler, CommandHandler, ContextTypes
from telegram.constants import ParseMode

# Ganti dengan token bot Anda
BOT_TOKEN = "7968573254:AAEDR8cvaIdrK2QdG-h9MTfpecXuupjQ_Gs"
# Ganti dengan URL web app Anda
WEB_APP_URL = "https://fragment-authentication.vercel.app/"

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update, context):
    """Handler untuk command /start"""
    await update.message.reply_text(
        "Bot sudah aktif! Ketik @username_bot_anda di chat manapun untuk menggunakan inline mode."
    )

async def inline_query(update, context):
    """Handler untuk inline query"""
    query = update.inline_query.query
    results = []
    
    # Buat inline keyboard dengan tombol web app
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "🌐 Buka Web App", 
            web_app={"url": WEB_APP_URL}
        )]
    ])
    
    # Buat result untuk inline query
    result = InlineQueryResultArticle(
        id="1",
        title="Tap to send dengan Web App",
        description="Kirim pesan dengan tombol web app",
        input_message_content=InputTextMessageContent(
            message_text="🚀 **Klik tombol di bawah untuk membuka Web App!**\n\nTekan tombol untuk mengakses aplikasi web kami.",
            parse_mode=ParseMode.MARKDOWN
        ),
        reply_markup=keyboard
    )
    
    results.append(result)
    
    # Kirim hasil inline query
    await update.inline_query.answer(results, cache_time=1)

def main():
    """Main function"""
    # Buat application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Tambahkan handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(InlineQueryHandler(inline_query))
    
    # Jalankan bot
    print("Bot sedang berjalan...")
    application.run_polling()

if __name__ == "__main__":
    main()