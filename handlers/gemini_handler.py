import os
import json
import asyncio
import telebot
import google.generativeai as genai
import logging
from typing import Optional, Dict, Any, Union

# Configure logging
logger = logging.getLogger(__name__)

# 🔐 Gemini API Key from environment or hardcoded
GEMINI_API_KEY = "AIzaSyB5TpGTpHOY1UFsggmpr25vgRdhMRTKfUA"
genai.configure(api_key=GEMINI_API_KEY)

MAX_TURNS = 100

# --- CUSTOM PERSONA PROMPT ---
# এই প্রম্পটটি জেমিনিকে তার ব্যক্তিত্ব এবং ভাষার ব্যাপারে নির্দেশনা দেবে।
CUSTOM_PERSONA_PROMPT = "তুমি একজন বুদ্ধিমতী মেয়ে আর তুমি সবার সাথে তাদের গার্লফ্রেন্ড এর মত কেয়ারিং হয়ে কথা বলবে, তোমার উত্তর সংক্ষিপ্ত এবং অল্প কথায় হবে। তোমার সাথে কেউ যেই ভাষাতে কথা বলবে তুমি সাথে সাথেই সেই ভাষাতেই উত্তর দিবে ।"


class PerUserChatClient:
    """
    Manages a single chat session for a specific user.
    """
    def __init__(self, model_name: str = "gemini-1.5-flash-8b"):
        self.model = genai.GenerativeModel(model_name)
        # Add the custom persona prompt to the initial chat history
        initial_history = [
            {"role": "user", "parts": [CUSTOM_PERSONA_PROMPT]},
            {"role": "model", "parts": ["হাই! আমি তোমার জেমিনি। কেমন আছো?"]}
        ]
        self.chat = self.model.start_chat(history=initial_history)
        self.history = initial_history
        self.model_name = model_name
        logger.info(f"New chat client created for model: {model_name}")

    async def send_message(self, prompt: str) -> Dict[str, Any]:
        try:
            response = await asyncio.to_thread(self.chat.send_message, prompt)

            if response.text:
                self.history.append({"role": "user", "parts": [prompt]})
                self.history.append({"role": "model", "parts": [response.text]})

                if len(self.history) > MAX_TURNS * 2:
                    self.history = self.history[-MAX_TURNS * 2:]
                    self.chat = self.model.start_chat(history=self.history)

                return {
                    'status': 'success',
                    'answer': response.text
                }
            else:
                return {
                    'status': 'error',
                    'error': 'কোনো উত্তর তৈরি হয়নি। অনুগ্রহ করে আবার চেষ্টা করুন।'
                }
        except Exception as e:
            return {
                'status': 'error',
                'error': f'জেমিনি ত্রুটি: {str(e)}'
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
    if not hasattr(bot, 'gemini_auto_reply_status'):
        bot.gemini_auto_reply_status = {}
    if not hasattr(bot, 'gemini_chat_clients'):
        bot.gemini_chat_clients = {}

    def get_or_create_client(chat_id) -> PerUserChatClient:
        if chat_id not in bot.gemini_chat_clients:
            bot.gemini_chat_clients[chat_id] = PerUserChatClient()
        return bot.gemini_chat_clients[chat_id]

    @custom_command_handler("gemini")
    def handle_gemini(message):
        command_text = message.text.split(" ", 1)[0].lower()
        actual_command_len = 0
        for prefix in command_prefixes_list:
            if command_text.startswith(f"{prefix}gemini"):
                actual_command_len = len(f"{prefix}gemini")
                break

        prompt_raw = message.text[actual_command_len:].strip()

        if not prompt_raw:
            bot.reply_to(message, f"❓ `{command_prefixes_list[0]}gemini [প্রশ্ন]` লিখুন। উদাহরণ: `{command_prefixes_list[0]}gemini তুমি কেমন আছো?`", parse_mode="Markdown")
            return

        thinking_message = bot.reply_to(message, "🤖 জেমিনি ভাবছে...")

        try:
            client = get_or_create_client(message.chat.id)
            result = asyncio.run(client.send_message(prompt_raw))

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

    @custom_command_handler("ongem")
    def enable_autoreply(message):
        if not is_admin(bot, message.chat.id, message.from_user.id):
            bot.reply_to(message, "❌ এই কমান্ডটি শুধুমাত্র গ্রুপের অ্যাডমিনরা ব্যবহার করতে পারবে।")
            return

        bot.gemini_auto_reply_status[message.chat.id] = True
        bot.reply_to(message, "✅ জেমিনির অটো-রিপ্লাই চালু হয়েছে।")

    @custom_command_handler("offgem")
    def disable_autoreply(message):
        if not is_admin(bot, message.chat.id, message.from_user.id):
            bot.reply_to(message, "❌ এই কমান্ডটি শুধুমাত্র গ্রুপের অ্যাডমিনরা ব্যবহার করতে পারবে।")
            return

        bot.gemini_auto_reply_status[message.chat.id] = False
        if message.chat.id in bot.gemini_chat_clients:
            del bot.gemini_chat_clients[message.chat.id]
        bot.reply_to(message, "❌ জেমিনির অটো-রিপ্লাই বন্ধ করা হয়েছে এবং চ্যাট হিস্টরি মুছে ফেলা হয়েছে।")

    @bot.message_handler(func=lambda msg: bot.gemini_auto_reply_status.get(msg.chat.id, False) and msg.content_type == 'text' and not any(msg.text.lower().startswith(p) for p in command_prefixes_list))
    def auto_reply(message):
        chat_id = message.chat.id

        is_reply_to_me = message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id
        is_group_chat = message.chat.type in ["group", "supergroup"]
        is_at_mentioned = False
        if is_group_chat:
            if f"@{bot.get_me().username.lower()}" in message.text.lower():
                is_at_mentioned = True

        if is_group_chat and not is_reply_to_me and not is_at_mentioned:
            return

        thinking_message = bot.reply_to(message, "🤖 জেমিনি ভাবছে...")

        try:
            client = get_or_create_client(chat_id)
            reply = asyncio.run(client.send_message(message.text))

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
