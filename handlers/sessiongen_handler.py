# handlers/sessiongen_handler.py
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telethon.sync import TelegramClient as TeleClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, PasswordHashInvalidError
from pyrogram import Client as PyroClient
from pyrogram.errors import SessionPasswordNeeded, PasswordHashInvalid

user_steps = {}      # {user_id: step_name}
user_temp_data = {}  # {user_id: {api_id, api_hash, phone_number, sent_code_info, session_type, temp_client}}

def cleanup_user(user_id):
    try:
        if user_id in user_steps:
            del user_steps[user_id]
        if user_id in user_temp_data:
            temp_client = user_temp_data[user_id].get("temp_client")
            if temp_client:
                try:
                    temp_client.disconnect()
                except:
                    pass
            del user_temp_data[user_id]
    except:
        pass

def register(bot, custom_command_handler, COMMAND_PREFIXES):
    # ----------------------------
    # /sessiongen command
    # ----------------------------
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
            "Which library do you want to generate the session for?\n\n"
            "Press Cancel to abort.",
            reply_markup=keyboard
        )

    # ----------------------------
    # Callback query handler
    # ----------------------------
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

    # ----------------------------
    # Text input handler
    # ----------------------------
    @bot.message_handler(func=lambda message: True)
    def handle_text(message):
        user_id = message.from_user.id
        step = user_steps.get(user_id)
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
            send_code_and_ask_for_otp(bot, user_id)
            return

        if step == "waiting_for_code":
            user_temp_data[user_id]["otp_code"] = text
            user_steps[user_id] = "waiting_for_password"
            sign_in_and_generate_session(bot, user_id)
            return

        if step == "waiting_for_password":
            user_temp_data[user_id]["password"] = text
            check_password_and_generate_session(bot, user_id)
            return

    # ----------------------------
    # /cancel command
    # ----------------------------
    @custom_command_handler("cancel")
    def cancel_handler(message):
        user_id = message.from_user.id
        cleanup_user(user_id)
        bot.send_message(user_id, "Process cancelled.")

# ----------------------------
# Helper functions (sync version)
# ----------------------------
def send_code_and_ask_for_otp(bot, user_id):
    data = user_temp_data[user_id]
    phone = data["phone_number"]
    api_id = data["api_id"]
    api_hash = data["api_hash"]
    session_type = data["session_type"]

    if session_type == "pyrogram":
        temp_client = PyroClient(":memory:", api_id=api_id, api_hash=api_hash)
        data["temp_client"] = temp_client
        try:
            temp_client.start()
            sent = temp_client.send_code(phone)
            data["sent_code_info"] = sent
            bot.send_message(user_id, "Verification code sent. Enter the code.")
        except Exception as e:
            bot.send_message(user_id, f"Error sending code: {e}")
            cleanup_user(user_id)

    elif session_type == "telethon":
        temp_client = TeleClient(StringSession(), api_id, api_hash)
        data["temp_client"] = temp_client
        try:
            temp_client.connect()
            temp_client.send_code_request(phone)
            bot.send_message(user_id, "Verification code sent. Enter the code.")
        except Exception as e:
            bot.send_message(user_id, f"Error sending code: {e}")
            cleanup_user(user_id)

def sign_in_and_generate_session(bot, user_id):
    data = user_temp_data[user_id]
    phone = data["phone_number"]
    otp_code = data["otp_code"]
    session_type = data["session_type"]
    temp_client = data["temp_client"]

    if session_type == "pyrogram":
        try:
            phone_code_hash = getattr(data["sent_code_info"], "phone_code_hash", None)
            temp_client.sign_in(phone, phone_code_hash, otp_code)
            session_string = temp_client.export_session_string()
            bot.send_message(user_id, f"Pyrogram session:\n{session_string}")
        except SessionPasswordNeeded:
            user_steps[user_id] = "waiting_for_password"
            bot.send_message(user_id, "Enter 2FA password.")
            return
        except Exception as e:
            bot.send_message(user_id, f"Sign-in error: {e}")
        finally:
            temp_client.stop()
            cleanup_user(user_id)

    elif session_type == "telethon":
        try:
            temp_client.sign_in(phone, otp_code)
            session_string = temp_client.session.save()
            bot.send_message(user_id, f"Telethon session:\n{session_string}")
        except SessionPasswordNeededError:
            user_steps[user_id] = "waiting_for_password"
            bot.send_message(user_id, "Enter 2FA password.")
            return
        except Exception as e:
            bot.send_message(user_id, f"Sign-in error: {e}")
        finally:
            temp_client.disconnect()
            cleanup_user(user_id)

def check_password_and_generate_session(bot, user_id):
    data = user_temp_data[user_id]
    session_type = data["session_type"]
    temp_client = data["temp_client"]
    password = data["password"]

    if session_type == "pyrogram":
        try:
            temp_client.check_password(password)
            session_string = temp_client.export_session_string()
            bot.send_message(user_id, f"Pyrogram session (2FA):\n{session_string}")
        except PasswordHashInvalid:
            bot.send_message(user_id, "Wrong password! Process aborted.")
        except Exception as e:
            bot.send_message(user_id, f"Password verification error: {e}")
        finally:
            temp_client.stop()
            cleanup_user(user_id)

    elif session_type == "telethon":
        try:
            temp_client.sign_in(password=password)
            session_string = temp_client.session.save()
            bot.send_message(user_id, f"Telethon session (2FA):\n{session_string}")
        except PasswordHashInvalidError:
            bot.send_message(user_id, "Wrong password! Process aborted.")
        except Exception as e:
            bot.send_message(user_id, f"Password verification error: {e}")
        finally:
            temp_client.disconnect()
            cleanup_user(user_id)
