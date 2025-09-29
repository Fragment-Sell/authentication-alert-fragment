import logging
from telegram import InlineQueryResultCachedPhoto, InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, InlineQueryHandler, CommandHandler, ContextTypes
from telegram.constants import ParseMode

# Ganti dengan token bot Anda
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

# FILE_ID dari foto yang sudah diupload ke Telegram
# Cara mendapatkan file_id: kirim foto ke bot via @BotFather, lalu check logs
PHOTO_FILE_ID = "FILE_ID_FROM_TELEGRAM"

# URL web app Anda
WEB_APP_URL = "https://your-webapp-domain.com"

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update, context):
    """Handler untuk command /start"""
    await update.message.reply_text(
        "Bot trading sudah aktif! Ketik @username_bot_anda di chat manapun untuk mengirim sinyal trading."
    )

async def inline_query(update, context):
    """Handler untuk inline query"""
    query = update.inline_query.query
    results = []
    
    # Buat inline keyboard dengan tombol web app
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Trade Now & Win Big!", web_app={"url": WEB_APP_URL})]
    ])
    
    # Teks pesan yang akan dikirim (sesuaikan dengan format yang diinginkan)
    message_text = """BITCOIN

AUTO-CLOSE EXECUTED!

Sui, your smart trading paid off!

Liquidated Closed: 110,239.01

Profit: 209,703,067 CATTEA

Stop Take Profit triggered perfectly! Smart risk management in action!

Ready for your next winning trade?

Trade Now & Win Big!"""
    
    # Buat result untuk inline query dengan foto
    result = InlineQueryResultCachedPhoto(
        id="1",
        photo_file_id=PHOTO_FILE_ID,
        caption=message_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )
    
    results.append(result)
    
    # Kirim hasil inline query
    await update.inline_query.answer(results, cache_time=1)

async def save_photo(update, context):
    """Handler untuk menyimpan file_id foto (gunakan ini sekali saja)"""
    if update.message.photo:
        # Dapatkan file_id dari foto dengan kualitas tertinggi
        photo_file = update.message.photo[-1]
        file_id = photo_file.file_id
        
        await update.message.reply_text(f"File ID foto Anda: `{file_id}`", parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text("Silakan kirim foto untuk mendapatkan file_id")

def main():
    """Main function"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Tambahkan handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("save_photo", save_photo))  # Untuk mendapatkan file_id
    application.add_handler(InlineQueryHandler(inline_query))
    
    print("Bot sedang berjalan...")
    application.run_polling()

if __name__ == "__main__":
    main()