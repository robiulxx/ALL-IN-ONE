import os
import asyncio
import aiohttp
import telebot
import logging
from typing import Dict, Any
from urllib.parse import urlparse
import tempfile
import html

# Configure logging
logger = logging.getLogger(__name__)

# API endpoints
FB_PFP_API = "https://insta-fb-pp.vercel.app/api/pfp?url={url}"
INSTA_PFP_API = "https://insta-fb-pp.vercel.app/api/instagram?url={url}"


async def get_profile_picture(url: str) -> Dict[str, Any]:
    """Downloads a profile picture from a given URL using the appropriate API."""
    try:
        parsed_url = urlparse(url)
        if "facebook.com" in parsed_url.netloc:
            api_url = FB_PFP_API.format(url=url)
        elif "instagram.com" in parsed_url.netloc:
            api_url = INSTA_PFP_API.format(url=url)
        else:
            return {
                "status": "error",
                "error": "❌ শুধুমাত্র ফেসবুক বা ইনস্টাগ্রাম প্রোফাইলের URL দিন।"
            }

        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as res:
                res.raise_for_status()

                # Check the content type to decide how to handle the response
                content_type = res.headers.get('Content-Type', '')
                if 'image' in content_type:
                    image_bytes = await res.read()

                    # Save the image to a temporary file
                    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                        tmp.write(image_bytes)
                        temp_path = tmp.name

                    return {
                        "status": "success",
                        "image_path": temp_path
                    }
                else:
                    data = await res.json()
                    return {
                        "status": "error",
                        "error": data.get("error", "❌ API থেকে কোনো তথ্য পাওয়া যায়নি।")
                    }

    except aiohttp.ClientResponseError as e:
        return {"status": "error", "error": f"API ত্রুটি: {e.status} - {e.message}"}
    except Exception as e:
        return {"status": "error", "error": f"একটি অপ্রত্যাশিত ত্রুটি হয়েছে: {str(e)}"}


def register(bot: telebot.TeleBot, custom_command_handler, command_prefixes_list):
    @custom_command_handler("pfp", "profilepic")
    def handle_pfp_command(message):
        command_text = message.text.split(" ", 1)[0].lower()
        actual_command_len = 0
        for prefix in command_prefixes_list:
            if command_text.startswith(f"{prefix}pfp") or command_text.startswith(f"{prefix}profilepic"):
                actual_command_len = len(command_text)
                break

        url = message.text[actual_command_len:].strip()

        if not url:
            bot.reply_to(message, "❌ অনুগ্রহ করে একটি ফেসবুক বা ইনস্টাগ্রাম প্রোফাইল URL দিন। যেমন: `/pfp https://www.facebook.com/...`", parse_mode="Markdown")
            return

        thinking_message = bot.reply_to(message, "⏳ প্রোফাইল ছবিটি ডাউনলোড করা হচ্ছে...")

        image_path = None
        try:
            result = asyncio.run(get_profile_picture(url))

            if result['status'] == 'success':
                image_path = result['image_path']

                with open(image_path, 'rb') as f:
                    bot.send_photo(
                        message.chat.id,
                        f,
                        caption=f"✅ সফল! এখানে আপনার প্রোফাইল ছবিটি আছে।",
                        reply_to_message_id=message.message_id
                    )
                bot.delete_message(thinking_message.chat.id, thinking_message.message_id)
            else:
                bot.edit_message_text(
                    chat_id=thinking_message.chat.id,
                    message_id=thinking_message.message_id,
                    text=result['error']
                )
        except Exception as e:
            bot.edit_message_text(
                chat_id=thinking_message.chat.id,
                message_id=thinking_message.message_id,
                text=f"❌ একটি ত্রুটি হয়েছে: {str(e)}"
            )
        finally:
            if image_path and os.path.exists(image_path):
                os.remove(image_path)
