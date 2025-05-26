from telegram.ext import ApplicationBuilder, CommandHandler
import os

async def start(update, context):
    await update.message.reply_text("Привет! Я бот.")

if __name__ == '__main__':
    token = os.getenv("YOUR_BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()
