import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Token bot dari environment variable
BOT_TOKEN = os.environ.get('BOT_TOKEN')
MINI_APP_URL = os.environ.get('WEB_APP_URL', 'https://fragment-authentication.vercel.app/')  # Ganti dengan URL mini app Anda

# State management sederhana
user_data = {}

# Command /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_data[user_id] = {'state': 'awaiting_username'}
    
    await update.message.reply_text('Username Please ?')

# Handle username input
async def handle_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    
    # Cek jika user dalam state yang benar
    if user_id not in user_data or user_data[user_id].get('state') != 'awaiting_username':
        await update.message.reply_text('Silakan ketik /start untuk memulai.')
        return
    
    username = update.message.text.strip()
    
    # Validasi username sederhana
    if not username:
        await update.message.reply_text('Username tidak valid. Silakan ketik username yang valid.')
        return
    
    # Simpan username
    user_data[user_id]['username'] = username
    user_data[user_id]['state'] = 'completed'
    
    # Buat tombol untuk mini app
    keyboard = [
        [InlineKeyboardButton("View Detail", web_app={"url": f"{MINI_APP_URL}?username={username}"})]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = f"Fragment Authentication : Direct offer to sell your username @{username}"
    
    await update.message.reply_text(message_text, reply_markup=reply_markup)

# Handle callback query (jika diperlukan)
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    # Tambahkan logika callback jika diperlukan

# Handle messages yang tidak sesuai
async def handle_other_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    
    if user_id in user_data and user_data[user_id].get('state') == 'awaiting_username':
        await update.message.reply_text('Silakan ketik username Anda.')
    else:
        await update.message.reply_text('Silakan ketik /start untuk memulai.')

# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Error occurred: {context.error}")

def main() -> None:
    # Cek jika BOT_TOKEN tersedia
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN environment variable is required")
    
    # Create Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_username))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.ALL, handle_other_messages))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start bot
    port = int(os.environ.get('PORT', 8443))
    webhook_url = os.environ.get('WEBHOOK_URL')
    
    if webhook_url:
        # Production mode dengan webhook (Railway)
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=BOT_TOKEN,
            webhook_url=f"{webhook_url}/{BOT_TOKEN}"
        )
    else:
        # Development mode dengan polling
        application.run_polling()

if __name__ == '__main__':
    main()