import logging
from flask import Flask
from telegram.ext import ApplicationBuilder, CommandHandler
from pw_handler import pw_handler
from ak_handler import ak_handler
from iit_handler import iit_handler
from kgs_handler import kgs_handler
from appx_handler import appx_handler # Import the new handler
from config import BOT_TOKEN

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)

# Flask App
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running on Flask server!"

if __name__ == "__main__":
    from threading import Thread

    # Start Flask server
    flask_thread = Thread(target=lambda: app.run(host="0.0.0.0", port=5000))
    flask_thread.start()

    # Telegram Bot setup
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers
    async def start(update, context):
        await update.message.reply_text("𝐻𝑒𝑙𝑙𝑜 𝑢𝑠𝑒𝑟  😉 𝐼'𝑚 𝐴 𝑆𝑖𝑚𝑝𝑙𝑒 𝐵𝑎𝑡𝑐ℎ 𝑡𝑜 𝑇𝑥𝑇 𝑒𝑥𝑡𝑟𝑎𝑐𝑡𝑜𝑟 𝐵𝑜𝑡\n\n𝑈𝑠𝑒 𝑡ℎ𝑒𝑠𝑒 𝑐𝑜𝑚𝑚𝑎𝑛𝑑𝑠:\n🫠 /pw - 𝑓𝑜𝑟 𝑃𝑊 𝑐𝑜𝑛𝑡𝑒𝑛𝑡\n🫠 /iit - 𝑓𝑜𝑟 𝐼𝐼𝑇 𝑆𝑐ℎ𝑜𝑜𝑙 𝑐𝑜𝑛𝑡𝑒𝑛𝑡\n🫠 /ak - 𝑓𝑜𝑟  𝑨𝒑𝒏𝒊 𝒌𝒂𝒌𝒔𝒉𝒂 𝑐𝑜𝑛𝑡𝑒𝑛𝑡")

    application.add_handler(CommandHandler("start", start))
    application.add_handler(pw_handler)
    application.add_handler(ak_handler) 
    application.add_handler(iit_handler)
    application.add_handler(kgs_handler)
    application.add_handler(appx_handler)  # Add the new IIT handler
    application.run_polling()