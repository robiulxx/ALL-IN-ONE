import os
import asyncio
import aiohttp
import aiofiles
import telebot
import base64
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import re

# Defined Styles and Aspect Ratios based on the provided images
STYLES = [
    "Photorealistic", "Cartoon", "Abstract Art", "Impressionist", "Cyberpunk",
    "Anime", "Oil Painting", "Watercolor", "Sketch", "Digital Art"
]

ASPECT_RATIOS = [
    "1:1", "16:9", "9:16", "4:3", "3:4"
]

async def generate_image(prompt, style, aspect_ratio):
    payload = {
        "prompt": prompt,
        "style": style,
        "aspect_ratio": aspect_ratio,
        "provider": "gemini"
    }

    url = "https://gemini-ai-one-for-all.vercel.app/api/generate"

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as res:
            res.raise_for_status()
            data = await res.json()

            if data.get("status") != "success":
                raise Exception(data.get("response_text", "Unknown API error"))

            image_base64 = data.get("image_base64")
            if not image_base64:
                raise Exception("Base64 image data not found in API response")

            image_bytes = base64.b64decode(image_base64)
            img_path = f"generated_image_{os.urandom(4).hex()}.png"

            async with aiofiles.open(img_path, mode='wb') as f:
                await f.write(image_bytes)

            return img_path

def register(bot: telebot.TeleBot, custom_command_handler, command_prefixes_list):

    @custom_command_handler("gmeg")
    def imagine_command(message):
        arg_string = message.text.split(" ", 1)[-1].strip()

        if not arg_string or arg_string.lower().startswith(tuple(command_prefixes_list)):
            bot.reply_to(message, "অনুগ্রহ করে একটি প্রম্পট দিন। যেমন: `/imagine a cat sitting on a moon`", parse_mode="Markdown")
            return

        # Store prompt and a temporary reference for state management
        bot.imagine_prompts = getattr(bot, 'imagine_prompts', {})
        user_id = message.from_user.id
        bot.imagine_prompts[user_id] = arg_string

        # Create inline keyboard for style
        style_keyboard = InlineKeyboardMarkup()
        style_keyboard.row_width = 2
        for style in STYLES:
            style_keyboard.add(InlineKeyboardButton(style, callback_data=f"imagine_style_{style}"))

        bot.send_message(
            message.chat.id,
            f"<b>🖼️ স্টাইল বেছে নিন:</b>\n\nপ্রম্পট: <code>{arg_string}</code>",
            reply_markup=style_keyboard,
            parse_mode="HTML"
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith('imagine_style_'))
    def select_style_callback(call):
        user_id = call.from_user.id
        if user_id not in bot.imagine_prompts:
            bot.answer_callback_query(call.id, "আপনার অনুরোধের সময় শেষ হয়ে গেছে। নতুন করে শুরু করুন।")
            return

        prompt = bot.imagine_prompts[user_id]
        selected_style = call.data.split('_', 2)[-1]
        bot.imagine_prompts[user_id] = {"prompt": prompt, "style": selected_style}

        # Create inline keyboard for aspect ratio
        ratio_keyboard = InlineKeyboardMarkup()
        ratio_keyboard.row_width = 3
        # Corrected variable name from ASPECTS_RATIOS to ASPECT_RATIOS
        for ratio in ASPECT_RATIOS: 
            ratio_keyboard.add(InlineKeyboardButton(ratio, callback_data=f"imagine_ratio_{ratio}"))

        bot.edit_message_text(
            f"<b>📏 অনুপাত বেছে নিন:</b>\n\nপ্রম্পট: <code>{prompt}</code>\nস্টাইল: <code>{selected_style}</code>",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=ratio_keyboard,
            parse_mode="HTML"
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith('imagine_ratio_'))
    def select_ratio_callback(call):
        user_id = call.from_user.id
        if user_id not in bot.imagine_prompts or not isinstance(bot.imagine_prompts[user_id], dict):
            bot.answer_callback_query(call.id, "আপনার অনুরোধের সময় শেষ হয়ে গেছে। নতুন করে শুরু করুন।")
            return

        prompt_info = bot.imagine_prompts[user_id]
        prompt = prompt_info["prompt"]
        style = prompt_info["style"]
        aspect_ratio = call.data.split('_', 2)[-1]

        bot.delete_message(call.message.chat.id, call.message.message_id)

        generating_msg = bot.send_message(
            call.message.chat.id,
            "⏳ আপনার ছবিটি তৈরি করা হচ্ছে। অনুগ্রহ করে অপেক্ষা করুন..."
        )

        try:
            image_path = asyncio.run(generate_image(prompt, style, aspect_ratio))

            with open(image_path, 'rb') as f:
                bot.send_photo(
                    call.message.chat.id,
                    f,
                    caption=f"🔍 <b>ইমেজ জেনারেশন রেজাল্ট</b>\n\n📝 <b>প্রম্পট:</b> <code>{prompt}</code>\n🎨 <b>স্টাইল:</b> <code>{style}</code>\n📏 <b>অনুপাত:</b> <code>{aspect_ratio}</code>",
                    parse_mode="HTML"
                )

            bot.delete_message(call.message.chat.id, generating_msg.message_id)

        except Exception as e:
            bot.edit_message_text(
                f"❌ ছবি তৈরি করতে সমস্যা হয়েছে: {str(e)}",
                chat_id=generating_msg.chat.id,
                message_id=generating_msg.message_id
            )
        finally:
            if 'image_path' in locals() and os.path.exists(image_path):
                os.remove(image_path)
            if user_id in bot.imagine_prompts:
                del bot.imagine_prompts[user_id]
