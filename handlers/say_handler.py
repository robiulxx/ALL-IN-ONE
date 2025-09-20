import os
import asyncio
import aiohttp
import aiofiles
from telebot.types import Message
from langdetect import detect, DetectorFactory

DetectorFactory.seed = 0  

async def download_file(url, path):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            resp.raise_for_status()
            if resp.status == 200:
                f = await aiofiles.open(path, mode='wb')
                await f.write(await resp.read())
                await f.close()
            else:
                raise Exception(f"Failed to download file: HTTP {resp.status}")

def register(bot, custom_command_handler, command_prefixes_list): 
    @custom_command_handler("say")
    def handle_say2(message: Message):
        
        command_text = message.text.split(" ", 1)[0].lower()
        actual_command_len = 0
        for prefix in command_prefixes_list: 
            if command_text.startswith(f"{prefix}say"):
                actual_command_len = len(f"{prefix}say")
                break

        content_raw = message.text[actual_command_len:].strip()

        if not content_raw:
            bot.reply_to(message, f"❌ টেক্সট অনুপস্থিত! ব্যবহারের নিয়ম: `{command_prefixes_list[0]}say তোমার টেক্সট`\nউদাহরণ: `{command_prefixes_list[1]}say হ্যালো পৃথিবী`", parse_mode="Markdown") 
            return

        content = content_raw

        # অটো detect language
        try:
            lang_code = detect(content)
        except:
            lang_code = "en"  # ডিফল্ট ইংরেজি যদি detect না হয়

        allowed_langs = ["ru", "en", "ko", "ja", "tl", "bn", "si", "fr", "de", "es"]

        if lang_code not in allowed_langs:
            lang_code = "en"  # fallback

        async def process():
            try:
                filename = f"tts_{message.chat.id}_{message.message_id}.mp3"
                filepath = os.path.join("cache", filename)

                # prompt কে URL-encode করা হয়েছে
                tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={aiohttp.helpers.quote(content)}&tl={lang_code}&client=tw-ob"

                await download_file(tts_url, filepath)

                with open(filepath, "rb") as voice:
                    bot.send_voice(message.chat.id, voice, reply_to_message_id=message.message_id)

                os.remove(filepath)

            except Exception as e:
                bot.send_message(message.chat.id, f"❌ ত্রুটি হয়েছে: {str(e)}")

        asyncio.run(process())