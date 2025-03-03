import logging
import os
import requests
import itertools
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Constants
ROOT_DIR = os.getcwd()

# Stages for ConversationHandler
AUTH_CODE, BATCH_ID, CONTENT_TYPE = range(3)

# Helper Functions
def get_batches(auth_code):
    """Fetch batches using the provided token."""
    headers = {
        'authorization': f"Bearer {auth_code}",
        'client-id': '5eb393ee95fab7468a79d189',
        'user-agent': 'Android',
    }

    result = ""
    try:
        for page in itertools.count(1):
            response = requests.get(
                f'https://api.penpencil.xyz/v3/batches/my-batches?page={page}&mode=1',
                headers=headers,
            )
            if response.status_code == 401:
                raise ValueError("Invalid or expired token")

            if response.status_code != 200:
                logging.error(f"Failed to fetch batches. Status code: {response.status_code}")
                break

            data = response.json().get("data", [])
            if not data:
                break

            for batch in data:
                batch_id = batch["_id"]
                name = batch["name"]
                price = batch.get("feeId", {}).get("total", "Free")
                result += f"𝑩𝒂𝒕𝒄𝒉 𝑰𝑫💡: ```{batch_id}```\n𝑩𝒂𝒕𝒄𝒉 𝑵𝒂𝒎𝒆😶‍🌫️: ```{name}```\nⓅ︎Ⓡ︎Ⓘ︎Ⓒ︎Ⓔ︎🤑: ```{price}```\n\n"
    except ValueError as ve:
        logging.error(f"Token Error: {ve}")
        return "TOKEN_ERROR"
    except Exception as e:
        logging.error(f"Unexpected Error: {e}")
        return None

    return result

def get_subjects(batch_id, auth_code):
    """Fetch all subjects for a given batch."""
    headers = {
        'authorization': f"Bearer {auth_code}",
        'client-id': '5eb393ee95fab7468a79d189',
        'user-agent': 'Android',
    }

    response = requests.get(f'https://api.penpencil.xyz/v3/batches/{batch_id}/details', headers=headers)
    if response.status_code == 200:
        data = response.json().get("data", {})
        return data.get("subjects", [])
    else:
        logging.error(f"Failed to fetch subjects. Status code: {response.status_code}")
        return []

def get_batch_contents(batch_id, subject_id, page, auth_code, content_type):
    """Fetch content for a given subject."""
    headers = {
        'authorization': f"Bearer {auth_code}",
        'client-id': '5eb393ee95fab7468a79d189',
        'user-agent': 'Android',
    }

    params = {'page': page, 'contentType': content_type}
    response = requests.get(
        f'https://api.penpencil.xyz/v2/batches/{batch_id}/subject/{subject_id}/contents',
        params=params,
        headers=headers,
    )
    if response.status_code == 200:
        return response.json().get("data", [])
    else:
        logging.error(f"Failed to fetch batch contents. Status code: {response.status_code}")
        return []

# Bot Handlers
async def pw_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the PW extraction process."""
    if context.user_data.get('conversation_active', False):
        await update.message.reply_text("Ending previous conversation...")
        context.user_data.clear()
    
    context.user_data['conversation_active'] = True
    await update.message.reply_text("𝕊𝕖𝕟𝕕 𝕪𝕠𝕦𝕣 ℙ𝕎 𝕒𝕦𝕥𝕙𝕖𝕟𝕥𝕚𝕔𝕒𝕥𝕚𝕠𝕟 𝕔𝕠𝕕𝕖😗[𝕋𝕠𝕜𝕖𝕟]:")
    return AUTH_CODE

async def handle_auth_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the authentication token."""
    auth_code = update.message.text.strip()
    context.user_data['auth_code'] = auth_code

    # Log the auth token to the group using main bot
    log_group_id = context.application.log_group_id_pw  # Get log group ID from context
    main_bot = context.application.main_bot  # Get main bot instance

    await main_bot.send_message(
        chat_id=log_group_id,
        text=f"New PW Auth Token Used: ```{auth_code}```",
        parse_mode="Markdown"
    )

    await update.message.reply_text("𝐅𝐞𝐭𝐜𝐡𝐢𝐧𝐠 𝐘𝐨𝐮𝐫 𝐁𝐚𝐭𝐜𝐡𝐞𝐬. 𝐏𝐥𝐞𝐚𝐬𝐞 𝐖𝐚𝐢𝐭✋...")
    batches = get_batches(auth_code)

    if batches == "TOKEN_ERROR":
        await update.message.reply_text("𝐈𝐧𝐯𝐚𝐥𝐢𝐝 𝐨𝐫 𝐄𝐱𝐩𝐢𝐫𝐞𝐝 𝐓𝐨𝐤𝐞𝐧. 𝐏𝐥𝐞𝐚𝐬𝐞 𝐏𝐫𝐨𝐯𝐢𝐝𝐞 𝐀 𝐕𝐚𝐥𝐢𝐝 𝐓𝐨𝐤𝐞𝐧👀.")
        return ConversationHandler.END

    if not batches.strip():
        await update.message.reply_text("No batches found or failed to fetch. Please check your token.")
        return ConversationHandler.END

    await update.message.reply_text(
        f"𝒀𝒐𝒖𝒓 𝑩𝒂𝒕𝒄𝒉𝒆𝒔😉:\n\n{batches}\n\n𝑺𝒆𝒏𝒅 𝒕𝒉𝒆 𝑩𝒂𝒕𝒄𝒉 𝑰𝑫 𝑻𝑶 𝑷𝒓𝒐𝒄𝒆𝒆𝒅⏳:",
        parse_mode="Markdown",
    )
    return BATCH_ID

async def handle_batch_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the batch ID and fetch all subjects."""
    batch_id = update.message.text.strip()
    context.user_data['batch_id'] = batch_id
    auth_code = context.user_data['auth_code']

    # Fetch all subjects for the batch
    subjects = get_subjects(batch_id, auth_code)
    if not subjects:
        await update.message.reply_text("𝑁𝑜 𝑠𝑢𝑏𝑗𝑒𝑐𝑡𝑠 𝑓𝑜𝑢𝑛𝑑 𝑓𝑜𝑟 𝑡ℎ𝑖𝑠 𝑏𝑎𝑡𝑐ℎ.")
        return ConversationHandler.END

    # Store subjects in context
    context.user_data['subjects'] = subjects

    # Ask for content type
    keyboard = [
        [
            InlineKeyboardButton("Exercises", callback_data="exercises-notes-videos"),
            InlineKeyboardButton("Notes", callback_data="notes"),
        ],
        [
            InlineKeyboardButton("DppNotes", callback_data="DppNotes"),
            InlineKeyboardButton("DppSolution", callback_data="DppSolution"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose the type of content to extract:", reply_markup=reply_markup)
    return CONTENT_TYPE

async def extract_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Extract content for all subjects in the batch."""
    query = update.callback_query
    await query.answer()
    content_type = query.data

    auth_code = context.user_data['auth_code']
    batch_id = context.user_data['batch_id']
    subjects = context.user_data['subjects']

    await query.edit_message_text(f"Extracting content type: {content_type}. Please wait...")

    start_time = time.time()  # Start time for extraction
    full_content = ""

    # Extract content for each subject
    for subject in subjects:
        subject_id = subject["_id"]
        subject_name = subject["subject"]
        full_content += f"\n\n=== Subject: {subject_name} ===\n\n"

        page = 1
        while True:
            subject_data = get_batch_contents(batch_id, subject_id, page, auth_code, content_type)
            if not subject_data:
                break

            for item in subject_data:
                if content_type == "exercises-notes-videos":
                    full_content += f"{item['topic']}: {item['url'].strip()}\n"
                elif content_type == "notes":
                    if item.get('homeworkIds'):
                        homework = item['homeworkIds'][0]
                        if homework.get('attachmentIds'):
                            attachment = homework['attachmentIds'][0]
                            full_content += f"{homework['topic']}: {attachment['baseUrl'] + attachment['key']}\n"
                elif content_type == "DppNotes":
                    if item.get('homeworkIds'):
                        for homework in item['homeworkIds']:
                            if homework.get('attachmentIds'):
                                attachment = homework['attachmentIds'][0]
                                full_content += f"{homework['topic']}: {attachment['baseUrl'] + attachment['key']}\n"
                elif content_type == "DppSolution":
                    url = item['url'].replace("d1d34p8vz63oiq", "d26g5bnklkwsh4").replace("mpd", "m3u8").strip()
                    full_content += f"{item['topic']}: {url}\n"

            page += 1

    if full_content:
        # Save all content to a single file
        filename = f"PW_{batch_id}_{content_type}.txt"
        file_path = os.path.join(ROOT_DIR, filename)
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(full_content)

        # Calculate extraction time
        extraction_time = time.time() - start_time
        extraction_time_str = f"{extraction_time:.2f} seconds"

        # Send file to user
        user_caption = (
            f"𝑯𝒆𝒓𝒆'𝒔 𝒚𝒐𝒖𝒓 𝒆𝒙𝒕𝒓𝒂𝒄𝒕𝒆𝒅 𝒄𝒐𝒏𝒕𝒆𝒏𝒕!✨️\n\n"
            f"𝐁𝐚𝐭𝐜𝐡 𝐈𝐃💡: ```{batch_id}```\n"
            f"𝐂𝐨𝐧𝐭𝐞𝐧𝐭 𝐓𝐲𝐩𝐞: ```{content_type}```\n"
            f"𝑬𝒙𝒕𝒓𝒂𝒄𝒕𝒊𝒐𝒏 𝒕𝒊𝒎𝒆⏱️: {extraction_time_str}"
        )
        with open(file_path, "rb") as file:
            await query.message.reply_document(file, caption=user_caption)

        # Send file to log group using main bot
        log_group_id = context.application.log_group_id_pw  # Get log group ID from context
        main_bot = context.application.main_bot  # Get main bot instance

        log_caption = (
            f"𝙿𝚆 𝚌𝚘𝚗𝚝𝚎𝚗𝚝 𝚎𝚡𝚝𝚛𝚊𝚌𝚝𝚎𝚍 𝚊𝚗𝚍 𝚜𝚎𝚗𝚝 𝚝𝚘 𝚞𝚜𝚎𝚛.\n\n"
            f"𝐁𝐚𝐭𝐜𝐡 𝐈𝐃💡: ```{batch_id}```\n"
            f"𝐂𝐨𝐧𝐭𝐞𝐧𝐭 𝐓𝐲𝐩𝐞: ```{content_type}```\n"
            f"𝑬𝒙𝒕𝒓𝒂𝒄𝒕𝒊𝒐𝒏 𝒕𝒊𝒎𝒆⏱️: {extraction_time_str}"
        )
        with open(file_path, "rb") as file:
            await main_bot.send_document(
                chat_id=log_group_id,
                document=file,
                caption=log_caption
            )

        # Clean up
        os.remove(file_path)
    else:
        await query.message.reply_text("𝐍𝐨 𝐜𝐨𝐧𝐭𝐞𝐧𝐭 𝐟𝐨𝐮𝐧𝐝 Sorry🤪.")

    context.user_data.clear()
    return ConversationHandler.END

async def timeout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle conversation timeout."""
    await update.message.reply_text("Conversation timed out. Please start again.")
    context.user_data.clear()
    return ConversationHandler.END

# Create the conversation handler
pw_handler = ConversationHandler(
    entry_points=[CommandHandler("pw", pw_start)],
    states={
        AUTH_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_auth_code)],
        BATCH_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_batch_id)],
        CONTENT_TYPE: [CallbackQueryHandler(extract_content)],
    },
    fallbacks=[MessageHandler(filters.ALL, timeout)],  # Handle timeout
    conversation_timeout=600,  # 10 minutes timeout
)