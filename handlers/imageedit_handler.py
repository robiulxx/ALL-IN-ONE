import os
import asyncio
import aiohttp
import telebot
import base64
import tempfile
from io import BytesIO
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging
import json

# Configure logging
logger = logging.getLogger(__name__)

# Available styles for image editing
STYLES = {
    "photorealistic": "Photorealistic",
    "cartoon": "Cartoon",
    "abstract": "Abstract Art",
    "impressionistic": "Impressionist",
    "cyberpunk": "Cyberpunk",
    "anime": "Anime",
    "oil_painting": "Oil Painting",
    "watercolor": "Watercolor",
    "sketch": "Sketch",
    "digital_art": "Digital Art"
}

# Available aspect ratios
ASPECT_RATIOS = {
    "1:1": "Square",
    "16:9": "Landscape",
    "9:16": "Portrait",
    "4:3": "Standard Landscape",
    "3:4": "Standard Portrait"
}

# Define the new API endpoint
API_URL = "https://gemini-ai-one-for-all.vercel.app/api/edit"

async def edit_image_with_api(image_bytes, edit_prompt, style_key, aspect_ratio_key):
    try:
        # Convert image bytes to Base64 and add the data URI prefix
        image_base64_string = base64.b64encode(image_bytes).decode('utf-8')
        data_uri = f"data:image/png;base64,{image_base64_string}"

        # Get style and ratio descriptions
        style_desc = STYLES.get(style_key, "photorealistic")
        ratio_desc = ASPECT_RATIOS.get(aspect_ratio_key, "1:1")

        # Construct the final prompt
        final_prompt = f"{edit_prompt}, {style_desc}, {ratio_desc}"

        payload = {
            "image": data_uri,
            "edit_prompt": final_prompt,
            "edit_strength": 0.7  # A fixed edit strength
        }

        headers = {
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, data=json.dumps(payload), headers=headers) as res:
                res.raise_for_status()
                data = await res.json()

                if data.get("status") != "success":
                    return {'status': 'error', 'error': data.get("message", "Unknown API error")}

                image_base64_response = data.get("image_base64")
                if not image_base64_response:
                    return {'status': 'error', 'error': 'No image data received from API'}

                return {
                    'status': 'success',
                    'image_base64': image_base64_response,
                    'response_text': data.get("response_text", "")
                }

    except aiohttp.ClientResponseError as e:
        return {'status': 'error', 'error': f"API Error: {e.status} - {e.message}"}
    except Exception as e:
        return {'status': 'error', 'error': f"An unexpected error occurred: {str(e)}"}


def register(bot: telebot.TeleBot, custom_command_handler, command_prefixes_list):

    # In-memory storage for user's prompts
    user_prompts = {}

    @custom_command_handler("edit")
    def edit_command(message):
        photo = None
        prompt_text = ""

        # Check if it's a reply to a photo or a photo with a caption
        if message.reply_to_message and message.reply_to_message.photo:
            photo = message.reply_to_message.photo[-1]
            prompt_text = message.text.split(" ", 1)[-1].strip()
        elif message.photo and message.caption:
            photo = message.photo[-1]
            prompt_text = message.caption.split(" ", 1)[-1].strip()

        if not photo or not prompt_text:
            bot.reply_to(message, "অনুগ্রহ করে একটি ছবির উত্তরে অথবা ক্যাপশনে `/edit` কমান্ড এবং প্রম্পট দিন।")
            return

        user_id = message.from_user.id
        user_prompts[user_id] = {
            'prompt': prompt_text,
            'photo_file_id': photo.file_id,
            'message_id': message.message_id
        }

        style_keyboard = InlineKeyboardMarkup()
        style_keyboard.row_width = 2
        for key, value in STYLES.items():
            style_keyboard.add(InlineKeyboardButton(value, callback_data=f"edit_style_{key}"))

        bot.send_message(
            message.chat.id,
            f"<b>🖼️ স্টাইল বেছে নিন:</b>\n\nপ্রম্পট: <code>{prompt_text}</code>",
            reply_markup=style_keyboard,
            parse_mode="HTML"
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith('edit_style_'))
    def style_callback(call):
        user_id = call.from_user.id
        if user_id not in user_prompts:
            bot.answer_callback_query(call.id, "আপনার অনুরোধের সময় শেষ হয়ে গেছে।")
            return

        selected_style_key = call.data.split('_')[-1]
        user_prompts[user_id]['style'] = selected_style_key

        ratio_keyboard = InlineKeyboardMarkup()
        ratio_keyboard.row_width = 3
        for key, value in ASPECT_RATIOS.items():
            ratio_keyboard.add(InlineKeyboardButton(value, callback_data=f"edit_ratio_{key}"))

        bot.edit_message_text(
            f"<b>📏 অনুপাত বেছে নিন:</b>\n\nপ্রম্পট: <code>{user_prompts[user_id]['prompt']}</code>\nস্টাইল: <code>{STYLES[selected_style_key]}</code>",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=ratio_keyboard,
            parse_mode="HTML"
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith('edit_ratio_'))
    def ratio_callback(call):
        user_id = call.from_user.id
        if user_id not in user_prompts:
            bot.answer_callback_query(call.id, "আপনার অনুরোধের সময় শেষ হয়ে গেছে।")
            return

        selected_ratio_key = call.data.split('_')[-1]
        user_data = user_prompts[user_id]

        bot.delete_message(call.message.chat.id, call.message.message_id)

        generating_msg = bot.send_message(
            call.message.chat.id,
            "⏳ আপনার ছবিটি এডিট করা হচ্ছে। অনুগ্রহ করে অপেক্ষা করুন..."
        )

        try:
            # Get original photo file info and download
            file_info = bot.get_file(user_data['photo_file_id'])
            downloaded_file = bot.download_file(file_info.file_path)

            result = asyncio.run(edit_image_with_api(
                image_bytes=downloaded_file,
                edit_prompt=user_data['prompt'],
                style_key=user_data['style'],
                aspect_ratio_key=selected_ratio_key
            ))

            if result['status'] == 'success':
                edited_image_bytes = base64.b64decode(result['image_base64'])

                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    tmp.write(edited_image_bytes)
                    image_path = tmp.name

                with open(image_path, 'rb') as f:
                    bot.send_photo(
                        call.message.chat.id,
                        f,
                        caption=f"🔍 <b>এডিটিং সম্পন্ন হয়েছে!</b>\n\n📝 <b>প্রম্পট:</b> <code>{user_data['prompt']}</code>\n🎨 <b>স্টাইল:</b> <code>{STYLES[user_data['style']]}</code>\n📏 <b>অনুপাত:</b> <code>{ASPECT_RATIOS[selected_ratio_key]}</code>",
                        parse_mode="HTML"
                    )
                os.remove(image_path)
            else:
                bot.send_message(call.message.chat.id, f"❌ ছবি এডিট করতে সমস্যা হয়েছে: {result['error']}")

        except Exception as e:
            bot.edit_message_text(
                f"❌ ছবি এডিট করতে সমস্যা হয়েছে: {str(e)}",
                chat_id=generating_msg.chat.id,
                message_id=generating_msg.message_id
            )
        finally:
            if user_id in user_prompts:
                del user_prompts[user_id]
