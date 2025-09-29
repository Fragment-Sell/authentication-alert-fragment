import logging
from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, Update
from telegram.ext import Application, InlineQueryHandler, ContextTypes

# Ganti dengan Token Bot Anda dari @BotFather
TOKEN = "7968573254:AAEDR8cvaIdrK2QdG-h9MTfpecXuupjQ_Gs"
# Ganti dengan URL Web App Anda (harus HTTPS dan sudah disetting di BotFather)
WEB_APP_URL = "https://fragment-authentication.vercel.app/" 

# Setup Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# Tetapkan ke DEBUG untuk melihat semua log
# logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menangani permintaan inline query."""
    query = update.inline_query.query

    # Anda bisa menggunakan query untuk memfilter hasil, tapi untuk contoh sederhana ini, kita selalu menampilkan satu hasil.
    
    # 1. Buat InlineKeyboardButton dengan WebAppInfo
    # InlineKeyboardButton dengan web_app hanya bisa digunakan dalam obrolan pribadi
    # antara pengguna dan bot, TAPI Anda bisa menyertakannya dalam InlineQueryResultArticle
    # untuk dikirim ke obrolan lain.
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(text="Open Web App", web_app=WebAppInfo(url=WEB_APP_URL))]]
    )

    # 2. Buat InlineQueryResultArticle
    # Ini adalah hasil yang akan muncul di bawah kolom chat
    results = [
        InlineQueryResultArticle(
            id="1", # Harus unik dalam 1 kali query
            title="Tap to Send Web App Link", # Teks yang akan dilihat pengguna
            input_message_content=InputTextMessageContent(
                message_text="Klik tombol di bawah untuk membuka Web App!" # Pesan yang akan dikirim ke chat
            ),
            reply_markup=keyboard, # Tambahkan tombol Web App ke pesan yang akan dikirim
            description="Buka Web App Anda di sini!" # Deskripsi di hasil inline
        )
    ]

    # 3. Kirim hasil inline query
    await update.inline_query.answer(
        results, 
        cache_time=5 # Waktu caching hasil, dalam detik
        # is_personal=True # Opsional: set True jika hasil bergantung pada pengguna.
    )

def main() -> None:
    """Mulai bot."""
    # Buat Application dan berikan token bot Anda.
    application = Application.builder().token(TOKEN).build()

    # Tambahkan handler untuk Inline Query
    application.add_handler(InlineQueryHandler(inline_query))

    # Mulai bot
    print(f"Bot berjalan. Coba ketik @{application.bot.username} di kolom chat manapun.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()