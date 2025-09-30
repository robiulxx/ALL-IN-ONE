# handlers/sessiongen_handler.py
import asyncio
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telethon.sync import TelegramClient as TeleClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, PasswordHashInvalidError
from pyrogram import Client as PyroClient
from pyrogram.errors import SessionPasswordNeeded, PasswordHashInvalid

try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

user_steps = {}
user_temp_data = {}

def cleanup_user(user_id):
    try:
        if user_id in user_steps:
            del user_steps[user_id]
        if user_id in user_temp_data:
            temp_client = user_temp_data[user_id].get("temp_client")
            if temp_client:
                try:
                    if isinstance(temp_client, PyroClient):
                        asyncio.run_coroutine_threadsafe(temp_client.stop(), loop)
                    else:
                        temp_client.disconnect()
                except:
                    pass
            del user_temp_data[user_id]
    except:
        pass

def register(bot, custom_command_handler, COMMAND_PREFIXES):
    @custom_command_handler("sessiongen")
    def sessiongen_handler(message):
        user_id = message.from_user.id
        cleanup_user(user_id)

        keyboard = InlineKeyboardMarkup()
        keyboard.row(
            InlineKeyboardButton("Pyrogram", callback_data="gen_pyrogram"),
            InlineKeyboardButton("Telethon", callback_data="gen_telethon")
        )
        keyboard.row(
            InlineKeyboardButton("Cancel", callback_data="gen_cancel")
        )
        user_steps[user_id] = "choosing_session_type"
        bot.send_message(
            user_id,
            "Which library do you want to generate the session for?\nPress Cancel to abort.",
            reply_markup=keyboard
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("gen_"))
    def callback_handler(call):
        user_id = call.from_user.id
        data = call.data

        if data == "gen_cancel":
            cleanup_user(user_id)
            bot.delete_message(user_id, call.message.message_id)
            bot.answer_callback_query(call.id, "Process cancelled.", show_alert=True)
            return

        session_type = data.split("_")[1]
        user_temp_data[user_id] = {"session_type": session_type}
        user_steps[user_id] = "waiting_for_api_id"
        bot.delete_message(user_id, call.message.message_id)
        bot.send_message(user_id, "Enter your API_ID (number only).")

    @bot.message_handler(func=lambda message: True)
    def handle_text(message):
        user_id = message.from_user.id
        step = user_steps.get(user_id)
        if not step:
            return
        text = message.text.strip()

        if step == "waiting_for_api_id":
            try:
                api_id = int(text)
            except:
                bot.send_message(user_id, "API_ID must be a number. Try again.")
                return
            user_temp_data[user_id]["api_id"] = api_id
            user_steps[user_id] = "waiting_for_api_hash"
            bot.send_message(user_id, "Enter your API_HASH.")
            return

        if step == "waiting_for_api_hash":
            api_hash = text
            user_temp_data[user_id]["api_hash"] = api_hash
            user_steps[user_id] = "waiting_for_phone_number"
            bot.send_message(user_id, "Enter your PHONE NUMBER (e.g., +8801712345678).")
            return

        if step == "waiting_for_phone_number":
            phone = text
            user_temp_data[user_id]["phone_number"] = phone
            user_steps[user_id] = "waiting_for_code"
            asyncio.run_coroutine_threadsafe(send_code_async(bot, user_id), loop)
            return

        if step == "waiting_for_code":
            user_temp_data[user_id]["otp_code"] = text
            user_steps[user_id] = "waiting_for_password"
            asyncio.run_coroutine_threadsafe(sign_in_async(bot, user_id), loop)
            return

        if step == "waiting_for_password":
            user_temp_data[user_id]["password"] = text
            asyncio.run_coroutine_threadsafe(check_password_async(bot, user_id), loop)
            return

    @custom_command_handler("cancel")
    def cancel_handler(message):
        user_id = message.from_user.id
        cleanup_user(user_id)
        bot.send_message(user_id, "Process cancelled.")

async def send_code_async(bot, user_id):
    data = user_temp_data[user_id]
    api_id = data["api_id"]
    api_hash = data["api_hash"]
    phone = data["phone_number"]
    session_type = data["session_type"]

    try:
        if session_type == "pyrogram":
            temp_client = PyroClient(":memory:", api_id=api_id, api_hash=api_hash)
            data["temp_client"] = temp_client
            await temp_client.start()
            sent = await temp_client.send_code(phone)
            data["sent_code_info"] = sent
        elif session_type == "telethon":
            temp_client = TeleClient(StringSession(), api_id, api_hash)
            data["temp_client"] = temp_client
            await asyncio.to_thread(temp_client.connect)
            await asyncio.to_thread(temp_client.send_code_request, phone)
        bot.send_message(user_id, "Verification code sent. Enter the code.")
    except Exception as e:
        bot.send_message(user_id, f"Error sending code: {e}")
        cleanup_user(user_id)

async def sign_in_async(bot, user_id):
    data = user_temp_data[user_id]
    phone = data["phone_number"]
    otp_code = data["otp_code"]
    session_type = data["session_type"]
    temp_client = data["temp_client"]

    try:
        if session_type == "pyrogram":
            phone_code_hash = getattr(data["sent_code_info"], "phone_code_hash", None)
            await temp_client.sign_in(phone, phone_code_hash, otp_code)
            session_string = await temp_client.export_session_string()
            bot.send_message(user_id, f"Pyrogram session:\n{session_string}")
        elif session_type == "telethon":
            await asyncio.to_thread(temp_client.sign_in, phone, otp_code)
            session_string = temp_client.session.save()
            bot.send_message(user_id, f"Telethon session:\n{session_string}")
    except (SessionPasswordNeeded, SessionPasswordNeededError):
        user_steps[user_id] = "waiting_for_password"
        bot.send_message(user_id, "Enter 2FA password.")
        return
    except Exception as e:
        bot.send_message(user_id, f"Sign-in error: {e}")
    finally:
        if session_type == "pyrogram":
            await temp_client.stop()
        else:
            await asyncio.to_thread(temp_client.disconnect)
        cleanup_user(user_id)

async def check_password_async(bot, user_id):
    data = user_temp_data[user_id]
    session_type = data["session_type"]
    temp_client = data["temp_client"]
    password = data["password"]

    try:
        if session_type == "pyrogram":
            await temp_client.check_password(password)
            session_string = await temp_client.export_session_string()
            bot.send_message(user_id, f"Pyrogram session (2FA):\n{session_string}")
        elif session_type == "telethon":
            await asyncio.to_thread(temp_client.sign_in, password=password)
            session_string = temp_client.session.save()
            bot.send_message(user_id, f"Telethon session (2FA):\n{session_string}")
    except (PasswordHashInvalid, PasswordHashInvalidError):
        bot.send_message(user_id, "Wrong password! Process aborted.")
    except Exception as e:
        bot.send_message(user_id, f"Password verification error: {e}")
    finally:
        if session_type == "pyrogram":
            await temp_client.stop()
        else:
            await asyncio.to_thread(temp_client.disconnect)
        cleanup_user(user_id)
