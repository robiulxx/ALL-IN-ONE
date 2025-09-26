import requests
from telebot.types import Message, InputFile
from io import BytesIO
import html

def register(bot, custom_command_handler, command_prefixes_list): 
    def fetch_info(bot, message: Message, target_type: str):
        identifier = None

        command_text_full = message.text.split(" ", 1)[0].lower()
        actual_command_len = 0
        
        full_command_with_prefix = message.text.split(maxsplit=1)[0].lower() 
        user_input_raw_after_command = ""
        if len(message.text.split(maxsplit=1)) > 1:
            user_input_raw_after_command = message.text.split(maxsplit=1)[1].strip()

        args_after_command = user_input_raw_after_command.split(maxsplit=1) 

        # USER or BOT
        if target_type in ["user", "bot"]:
            if len(args_after_command) > 0 and args_after_command[0]: 
                identifier = args_after_command[0].strip()
                if not identifier.startswith("@") and not identifier.isdigit():
                    identifier = "@" + identifier
            elif message.reply_to_message:
                user = message.reply_to_message.from_user or message.reply_to_message.forward_from
                if user:
                    identifier = f"@{user.username}" if user.username else str(user.id)
                else:
                    bot.reply_to(message, f"❌ রিপ্লাই করা মেসেজ থেকে ইউজার পাওয়া যায়নি। উদাহরণ: `{command_prefixes_list[0]}{full_command_with_prefix.lstrip(command_prefixes_list[0])} @username`", parse_mode="HTML")
                    return
            else: 
                identifier = f"@{message.from_user.username}" if message.from_user.username else str(message.from_user.id)

        # GROUP
        elif target_type == "group":
            if message.chat.type in ["group", "supergroup"] and not user_input_raw_after_command: 
                if message.chat.username:
                    identifier = f"@{message.chat.username}"
                else:
                    local_msg = f"""✘《 Group Information ↯ 》
↯ Title: {message.chat.title}
↯ Chat ID: {message.chat.id}
↯ Type: {message.chat.type.title()}
↯ Username: Not set
↯ Description: Not available

↯ API Owner: Rabiul Islam 𝗝𝗼𝗶𝗻: @rszone24
"""
                    escaped_local_msg = html.escape(local_msg)
                    bot.send_message(message.chat.id, f"<b>{escaped_local_msg}</b>", parse_mode="HTML")
                    return
            elif len(args_after_command) > 0 and args_after_command[0]: 
                identifier = args_after_command[0].strip()
                if not identifier.startswith("@") and not identifier.lstrip("-").isdigit():
                    identifier = "@" + identifier
            else:
                bot.reply_to(message, f"ℹ️ গ্রুপ ইনফো পেতে গ্রুপের ইউজারনেম দিন অথবা গ্রুপে কমান্ড দিন। উদাহরণ: `{command_prefixes_list[0]}{full_command_with_prefix.lstrip(command_prefixes_list[0])} @groupusername`", parse_mode="HTML")
                return

        # CHANNEL
        elif target_type == "channel":
            if len(args_after_command) > 0 and args_after_command[0]: 
                identifier = args_after_command[0].strip()
                if not identifier.startswith("@") and not identifier.lstrip("-").isdigit():
                    identifier = "@" + identifier
            else:
                bot.reply_to(message, f"ℹ️ চ্যানেলের ইনফো পেতে অবশ্যই ইউজারনেম দিতে হবে। উদাহরণ: `{command_prefixes_list[0]}{full_command_with_prefix.lstrip(command_prefixes_list[0])} @channelusername`", parse_mode="HTML")
                return

        # API Call
        try:
            api_url = f"https://web-production-39d6.up.railway.app/get_user_info?username={identifier}"
            response = requests.get(api_url, timeout=15)

            if response.status_code != 200 or not response.text.strip():
                bot.reply_to(message, "❌ API থেকে তথ্য পাওয়া যায়নি।")
                return

            lines = response.text.strip().splitlines()
            profile_pic_url = None
            msg_lines = []

            for line in lines:
                if "profile pic url" in line.lower():
                    profile_pic_url = line.split(":", 1)[1].strip()
                else:
                    msg_lines.append(line)

            final_msg = "\n".join(msg_lines)
            # Escape HTML characters to prevent parsing errors with Unicode characters
            escaped_msg = html.escape(final_msg)

            if profile_pic_url and profile_pic_url.startswith("http"):
                try:
                    pic = requests.get(profile_pic_url, timeout=10)
                    pic.raise_for_status()
                    img = BytesIO(pic.content)
                    img.name = "profile.jpg"

                    bot.send_photo(
                        chat_id=message.chat.id,
                        photo=InputFile(img),
                        caption=f"<b>{escaped_msg}</b>",
                        parse_mode="HTML"
                    )
                    return
                except:
                    escaped_msg += "\n⚠️ প্রোফাইল ছবি লোড করা যায়নি।"

            bot.send_message(message.chat.id, f"<b>{escaped_msg}</b>", parse_mode="HTML")

        except requests.exceptions.Timeout:
            bot.reply_to(message, "❌ টাইমআউট! আবার চেষ্টা করুন।")
        except requests.exceptions.ConnectionError:
            bot.reply_to(message, "❌ ইন্টারনেট সমস্যা হয়েছে।")
        except Exception as e:
            bot.reply_to(message, f"❌ ত্রুটি: {str(e)}")

    # Command Handlers
    @custom_command_handler("usr")
    def handle_usr(message: Message):
        fetch_info(bot, message, target_type="user")

    @custom_command_handler("bot")
    def handle_bot(message: Message):
        fetch_info(bot, message, target_type="bot")

    @custom_command_handler("grp")
    def handle_grp(message: Message):
        fetch_info(bot, message, target_type="group")

    @custom_command_handler("cnnl")
    def handle_cnnl(message: Message):
        fetch_info(bot, message, target_type="channel")

    @custom_command_handler("info")
    def handle_info(message: Message):
        
        command_text_full = message.text.split(" ", 1)[0].lower() 
        actual_command_len = 0
        for prefix in command_prefixes_list: 
            if command_text_full.startswith(f"{prefix}info"):
                actual_command_len = len(f"{prefix}info")
                break

        user_input_raw_info = message.text[actual_command_len:].strip()
        args_info = user_input_raw_info.split(maxsplit=1) 
        username_or_type = args_info[0] if len(args_info) > 0 else None


        if username_or_type:
            uname = username_or_type.lower()
            if uname.endswith("bot"):
                fetch_info(bot, message, target_type="bot")
            elif "channel" in uname or uname.startswith("@c"):
                fetch_info(bot, message, target_type="channel")
            elif "group" in uname or uname.startswith("@g"):
                fetch_info(bot, message, target_type="group")
            else: 
                fetch_info(bot, message, target_type="user")
        elif message.reply_to_message:
            user = message.reply_to_message.from_user
            if user and user.is_bot:
                fetch_info(bot, message, target_type="bot")
            else:
                fetch_info(bot, message, target_type="user")
        else: 
            fetch_info(bot, message, target_type="user")
