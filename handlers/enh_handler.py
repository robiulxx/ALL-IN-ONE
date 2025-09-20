import os
import asyncio
import aiohttp
import telebot
import threading
from io import BytesIO
from PIL import Image
import logging

# Configure logging
LOGGER = logging.getLogger(__name__)

# In-memory storage for user daily limits
user_daily_limits = {}
daily_limits_lock = threading.Lock()

async def upscale(buffer: bytes) -> tuple:
    try:
        # Get image dimensions to send to API
        with Image.open(BytesIO(buffer)) as img:
            width, height = img.size

        # API expects form data with specific fields
        form_data = aiohttp.FormData()
        form_data.add_field("image_file", buffer, filename="image.jpg", content_type="image/jpeg")
        form_data.add_field("name", str(threading.get_ident()))
        form_data.add_field("desiredHeight", str(height * 4))
        form_data.add_field("desiredWidth", str(width * 4))
        form_data.add_field("outputFormat", "png")
        form_data.add_field("compressionLevel", "high")
        form_data.add_field("anime", "false")

        headers = {
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://upscalepics.com",
            "Referer": "https://upscalepics.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post("https://api.upscalepics.com/upscale-to-size", data=form_data, headers=headers) as response:
                if response.status == 200:
                    json_response = await response.json()
                    image_url = json_response.get("bgRemoved", "").strip()
                    if image_url:
                        async with session.get(image_url) as img_resp:
                            img_resp.raise_for_status()
                            img_bytes = await img_resp.read()
                            return img_bytes, None
                    else:
                        return None, "API returned no image URL."
                else:
                    return None, f"API request failed with status {response.status}"
    except Exception as e:
        return None, f"Upscale error: {str(e)}"

def register(bot: telebot.TeleBot, custom_command_handler, command_prefixes_list):
    @custom_command_handler("enh")
    def enh_handler(message):
        user_id = message.from_user.id

        with daily_limits_lock:
            if user_id not in user_daily_limits:
                user_daily_limits[user_id] = 10
            if user_daily_limits[user_id] <= 0:
                bot.reply_to(message, "**You have reached your daily limit of 10 enhancements.**", parse_mode="Markdown")
                return

        replied_message = message.reply_to_message

        photo = replied_message.photo if replied_message and replied_message.photo else None
        document = replied_message.document if replied_message and replied_message.document and replied_message.document.mime_type.startswith("image/") else None

        if not (photo or document):
            bot.reply_to(message, "**Reply to a photo or image file to enhance face**", parse_mode="Markdown")
            return

        loading_message = bot.reply_to(message, "**Enhancing Your Face....**", parse_mode="Markdown")

        try:
            # Correctly access the largest photo from the list
            file_id = photo[-1].file_id if photo else document.file_id

            file_info = bot.get_file(file_id)
            image_buffer = bot.download_file(file_info.file_path)

            enhanced_image_bytes, error = asyncio.run(upscale(image_buffer))

            if enhanced_image_bytes:
                with daily_limits_lock:
                    user_daily_limits[user_id] -= 1

                img_io = BytesIO(enhanced_image_bytes)
                img_io.name = "enhanced.png"

                bot.delete_message(message.chat.id, loading_message.id)
                bot.send_document(
                    message.chat.id,
                    document=img_io,
                    caption=f"✅ Face enhanced!\n{user_daily_limits[user_id]} enhancements remaining today.",
                    reply_to_message_id=message.message_id
                )
            else:
                bot.edit_message_text(
                    chat_id=loading_message.chat.id,
                    message_id=loading_message.id,
                    text="**Sorry Enhancer API Dead**",
                    parse_mode="Markdown"
                )
                if error:
                    LOGGER.error(f"Enhancer error: {error}")
        except Exception as e:
            LOGGER.error(f"Enhancer error: {str(e)}")
            bot.edit_message_text(
                chat_id=loading_message.chat.id,
                message_id=loading_message.id,
                text=f"**Sorry Enhancer API Dead. Error: {str(e)}**",
                parse_mode="Markdown"
            )
