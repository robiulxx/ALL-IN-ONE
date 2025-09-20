import os
import requests
from telebot import types

REMOVE_BG_API_KEYS = [
    "u8cWMJmGKnptLUQfKcL7voU9",
    "61CPM5y7DqYQM6wHMa1fcvnw",
    "JE33ny8A49mfhXWGn6R7jXWV"
]

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def register(bot, custom_command_handler, command_prefixes_list): 
    @custom_command_handler("bgremove")
    def bgremove_handler(message):
        if not message.reply_to_message or not message.reply_to_message.photo:
            bot.reply_to(message, "⚠️ অনুগ্রহ করে কোনো ছবির উপর রিপ্লাই করে `/bgremove`, `.bgremove` অথবা `,bgremove` কমান্ড পাঠান।", parse_mode='Markdown')
            return

        photo = message.reply_to_message.photo[-1]  
        file_info = bot.get_file(photo.file_id)
        file_url = f'https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}'

        input_path = os.path.join(CACHE_DIR, f"input_{message.message_id}.png")
        output_path = os.path.join(CACHE_DIR, f"output_{message.message_id}.png")

        try:
            bot.reply_to(message, "🖼️ ছবি ডাউনলোড হচ্ছে... একটু অপেক্ষা করুন।")

            # ছবি ডাউনলোড
            r = requests.get(file_url)
            with open(input_path, 'wb') as f:
                f.write(r.content)

            # remove.bg API কল
            api_key = REMOVE_BG_API_KEYS[message.message_id % len(REMOVE_BG_API_KEYS)]  

            files = {'image_file': open(input_path, 'rb')}
            data = {'size': 'auto'}
            headers = {'X-Api-Key': api_key}

            response = requests.post('https://api.remove.bg/v1.0/removebg', files=files, data=data, headers=headers, stream=True)

            if response.status_code != 200:
                bot.reply_to(message, f"❌ ব্যাকগ্রাউন্ড রিমুভ করতে সমস্যা হয়েছে: {response.status_code} {response.text}")
                return

            # আউটপুট ছবি সেভ
            with open(output_path, 'wb') as out_f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        out_f.write(chunk)

            # ছবি পাঠানো
            with open(output_path, 'rb') as out_f:
                bot.send_photo(message.chat.id, out_f, caption="🖼️ ব্যাকগ্রাউন্ড রিমুভ করা ছবি")

        except Exception as e:
            bot.reply_to(message, f"❌ এরর হয়েছে: {str(e)}")

        finally:
            # টেম্প ফাইল ডিলিট
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)