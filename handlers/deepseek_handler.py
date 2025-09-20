import os
import asyncio
import aiohttp
import telebot
import logging
from typing import Optional, Dict, Any, Union
import json

# Configure logging
logger = logging.getLogger(__name__)

# Deepseek API URL
DEEPSEEK_API_URL = "https://deepseek-r1v3.vercel.app/api/ds-chat-v3-1?q={}"

# System prompt for Deepseek
SYSTEM_PROMPT = "তুমি একজন বাংলাতে কথা বলা চ্যাটবট। তোমার উত্তর সংক্ষিপ্ত এবং অল্প কথায় হবে। সব সময় বাংলাতে কথা বলবে, তবে প্রয়োজনে ইংরেজিতে উত্তর দেবে।"

MAX_HISTORY_TURNS = 10

# Helper function to get the full prompt with history
def get_full_prompt(history: list, new_prompt: str) -> str:
    full_prompt = SYSTEM_PROMPT
    for turn in history:
        full_prompt += f"\n\nuser: {turn['user']}\nassistant: {turn['assistant']}"
    full_prompt += f"\n\nuser: {new_prompt}\nassistant:"
    return full_prompt

# Main async function to ask Deepseek
async def ask_deepseek(bot, prompt: str, chat_id: int) -> Dict[str, Any]:
    if not hasattr(bot, 'deepseek_histories'):
        bot.deepseek_histories = {}

    if chat_id not in bot.deepseek_histories:
        bot.deepseek_histories[chat_id] = []

    history = bot.deepseek_histories[chat_id]

    full_prompt = get_full_prompt(history, prompt)

    encoded_prompt = aiohttp.helpers.quote(full_prompt)
    api_url = DEEPSEEK_API_URL.format(encoded_prompt)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as res:
                res.raise_for_status()
                data = await res.json()

                if data and data.get("reply"):
                    deepseek_response_text = data.get("reply")

                    history.append({"user": prompt, "assistant": deepseek_response_text})

                    if len(history) > MAX_HISTORY_TURNS:
                        history.pop(0)

                    bot.deepseek_histories[chat_id] = history
                    return {
                        'status': 'success',
                        'answer': deepseek_response_text
                    }

                return {
                    'status': 'error',
                    'error': data.get("reply", "API থেকে কোনো উত্তর পাওয়া যায়নি।")
                }
    except Exception as e:
        logger.error(f"Error asking Deepseek: {e}")
        return {
            'status': 'error',
            'error': f'Deepseek ত্রুটি: {str(e)}'
        }

# Helper function to check if a user is an admin in a group
def is_admin(bot, chat_id, user_id):
    if chat_id > 0:
        return True
    try:
        member = bot.get_chat_member(chat_id, user_id)
        if member.status in ['administrator', 'creator']:
            return True
    except Exception as e:
        print(f"Error checking admin status: {e}")
    return False

def register(bot: telebot.TeleBot, custom_command_handler, command_prefixes_list):
    if not hasattr(bot, 'deepseek_auto_reply_status'):
        bot.deepseek_auto_reply_status = {}
    if not hasattr(bot, 'deepseek_histories'):
        bot.deepseek_histories = {}

    # তিন ধরণের কমান্ডের জন্য একটি ডেকোরেটর ব্যবহার করুন
    @custom_command_handler("deepseek", "deep", "ds")
    def handle_deepseek(message):
        command_text = message.text.split(" ", 1)[0].lower()
        actual_command_len = 0
        for prefix in command_prefixes_list:
            if command_text.startswith(f"{prefix}deepseek"):
                actual_command_len = len(f"{prefix}deepseek")
                break

        prompt_raw = message.text[actual_command_len:].strip()

        if not prompt_raw:
            bot.reply_to(message, f"❓ `{command_prefixes_list[0]}deepseek [প্রশ্ন]` লিখুন। উদাহরণ: `{command_prefixes_list[0]}deepseek তুমি কেমন আছো?`", parse_mode="Markdown")
            return

        thinking_message = bot.reply_to(message, "🤖 Deepseek ভাবছে...")

        try:
            result = asyncio.run(ask_deepseek(bot, prompt_raw, message.chat.id))

            if result['status'] == 'success':
                bot.edit_message_text(
                    chat_id=thinking_message.chat.id,
                    message_id=thinking_message.message_id,
                    text=f"🤖 {result['answer']}"
                )
            else:
                bot.edit_message_text(
                    chat_id=thinking_message.chat.id,
                    message_id=thinking_message.message_id,
                    text=f"❌ ত্রুটি: {result['error']}"
                )
        except Exception as e:
            bot.edit_message_text(
                chat_id=thinking_message.chat.id,
                message_id=thinking_message.message_id,
                text=f"❌ ত্রুটি: {e}"
            )

    @custom_command_handler("ondeepseek")
    def enable_deepseek_autoreply(message):
        if not is_admin(bot, message.chat.id, message.from_user.id):
            bot.reply_to(message, "❌ এই কমান্ডটি শুধুমাত্র গ্রুপের অ্যাডমিনরা ব্যবহার করতে পারবে।")
            return

        bot.deepseek_auto_reply_status[message.chat.id] = True
        bot.reply_to(message, "✅ Deepseek অটো-রিপ্লাই চালু হয়েছে।")

    @custom_command_handler("offdeepseek")
    def disable_deepseek_autoreply(message):
        if not is_admin(bot, message.chat.id, message.from_user.id):
            bot.reply_to(message, "❌ এই কমান্ডটি শুধুমাত্র গ্রুপের অ্যাডমিনরা ব্যবহার করতে পারবে।")
            return

        bot.deepseek_auto_reply_status[message.chat.id] = False
        if message.chat.id in bot.deepseek_histories:
            del bot.deepseek_histories[message.chat.id]
        bot.reply_to(message, "❌ Deepseek অটো-রিপ্লাই বন্ধ করা হয়েছে এবং চ্যাট হিস্টরি মুছে ফেলা হয়েছে।")

    @custom_command_handler("reset_deepseek")
    def reset_deepseek_history(message):
        chat_id = message.chat.id
        if hasattr(bot, 'deepseek_histories') and chat_id in bot.deepseek_histories:
            del bot.deepseek_histories[chat_id]
            bot.reply_to(message, "✅ Deepseek চ্যাট হিস্টরি মুছে ফেলা হয়েছে।")
        else:
            bot.reply_to(message, "ℹ️ কোনো সক্রিয় Deepseek চ্যাট হিস্টরি নেই।")

    @bot.message_handler(func=lambda msg: bot.deepseek_auto_reply_status.get(msg.chat.id, False) and msg.content_type == 'text' and not any(msg.text.lower().startswith(p) for p in command_prefixes_list))
    def auto_reply_deepseek(message):
        chat_id = message.chat.id

        is_reply_to_me = message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id
        is_group_chat = message.chat.type in ["group", "supergroup"]
        is_at_mentioned = False
        if is_group_chat:
            if f"@{bot.get_me().username.lower()}" in message.text.lower():
                is_at_mentioned = True

        if is_group_chat and not is_reply_to_me and not is_at_mentioned:
            return

        thinking_message = bot.reply_to(message, "🤖 Deepseek ভাবছে...")

        try:
            reply = asyncio.run(ask_deepseek(bot, message.text, chat_id))

            if reply['status'] == 'success':
                bot.edit_message_text(
                    chat_id=thinking_message.chat.id,
                    message_id=thinking_message.message_id,
                    text=f"🤖 {reply['answer']}"
                )
            else:
                bot.edit_message_text(
                    chat_id=thinking_message.chat.id,
                    message_id=thinking_message.message_id,
                    text=f"❌ ত্রুটি: {reply['error']}"
                )
        except Exception as e:
            bot.edit_message_text(
                chat_id=thinking_message.chat.id,
                message_id=thinking_message.message_id,
                text=f"❌ ত্রুটি: {e}"
            )
