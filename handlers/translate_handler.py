import requests
from telebot.types import Message

def register(bot, custom_command_handler, command_prefixes_list): 
    @custom_command_handler("translate")
    def translate_handler(message: Message):

        command_text_full = message.text.split(" ", 1)[0].lower()
        actual_command_len = 0
        for prefix in command_prefixes_list: 
            if command_text_full.startswith(f"{prefix}translate"):
                actual_command_len = len(f"{prefix}translate")
                break

        text_after_command = message.text[actual_command_len:].strip()
        args = text_after_command.split(" ", 1) 

        if not args[0] and not message.reply_to_message: 
            bot.reply_to(message, f"❌ ব্যবহারের নিয়ম: `{command_prefixes_list[0]}translate <ভাষা_কোড> <টেক্সট>` অথবা কোনো টেক্সটে রিপ্লাই দিন।\nউদাহরণ: `{command_prefixes_list[0]}translate fr Hello!`, `{command_prefixes_list[1]}translate bn আমি ভালো আছি`", parse_mode="Markdown") 
            return

        # Detect target language and text
        if message.reply_to_message:
            text_to_translate = message.reply_to_message.text or message.reply_to_message.caption or ""
            target_lang = args[0] if args[0] else "en" 
        else:
            target_lang = args[0]
            text_to_translate = args[1] if len(args) > 1 else "" 

        if not text_to_translate:
            bot.reply_to(message, "❌ অনুগ্রহ করে অনুবাদযোগ্য টেক্সট দিন।", parse_mode="Markdown")
            return

        if not target_lang:
            target_lang = "en" 

        try:
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                "client": "gtx",
                "sl": "auto",
                "tl": target_lang,
                "dt": "t",
                "q": text_to_translate
            }

            resp = requests.get(url, params=params)
            if resp.status_code != 200:
                bot.reply_to(message, f"❌ অনুবাদ ব্যর্থ হলো (status {resp.status_code})")
                return

            data = resp.json()

            translated = ''.join([item[0] for item in data[0] if item[0]])
            source_lang = data[2] if data[2] != data[8][0][0] else data[8][0][0]

            reply_msg = (
                f"✅ <b>অনুবাদ:</b> {translated}\n"
                f"🌐 <i>{source_lang.upper()} থেকে {target_lang.upper()}</i>"
            )
            bot.send_message(
                message.chat.id,
                reply_msg,
                reply_to_message_id=message.message_id,
                parse_mode="HTML"
            )

        except Exception as e:
            bot.reply_to(message, f"❌ ত্রুটি: {str(e)}")