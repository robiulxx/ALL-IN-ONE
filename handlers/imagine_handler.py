import os
import asyncio
import aiohttp
import aiofiles
import json
from telebot.types import Message, InputMediaPhoto

os.makedirs("cache", exist_ok=True)

async def download_image(url, path):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            resp.raise_for_status()
            if resp.status == 200:
                f = await aiofiles.open(path, mode='wb')
                await f.write(await resp.read())
                await f.close()

def register(bot, custom_command_handler, command_prefixes_list): 
    @custom_command_handler("imagine")
    def handle_imagine(message: Message):

        command_text = message.text.split(" ", 1)[0].lower()
        actual_command_len = 0
        for prefix in command_prefixes_list: 
            if command_text.startswith(f"{prefix}imagine"):
                actual_command_len = len(f"{prefix}imagine")
                break

        prompt_raw = message.text[actual_command_len:].strip()

        if not prompt_raw:
            bot.reply_to(message, f"❌ প্রম্পট অনুপস্থিত। উদাহরণ: `{command_prefixes_list[0]}imagine cat with sunglasses`, `{command_prefixes_list[1]}imagine a fantasy landscape`", parse_mode="Markdown") 
            return

        search_prompt = prompt_raw
        bot.reply_to(message, "🧠 ছবি তৈরি হচ্ছে, অনুগ্রহ করে অপেক্ষা করুন...")

        async def process():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://raw.githubusercontent.com/MOHAMMAD-NAYAN-07/Nayan/main/api.json") as resp:
                        resp.raise_for_status() 
                        text = await resp.text()
                        apidata = json.loads(text)
                        api_base = apidata["api"]
                        image_api = f"{api_base}/nayan/img?prompt={aiohttp.helpers.quote(search_prompt)}"

                    async with session.get(image_api) as img_resp:
                        img_resp.raise_for_status() 
                        res = await img_resp.json()
                        images = res.get("imageUrls", [])

                        if not images:
                            await bot.send_message(message.chat.id, "❌ কোনো ছবি পাওয়া যায়নি।")
                            return

                        photo_files = []
                        for idx, url in enumerate(images):
                            filename = f"temp_{idx}.jpg"
                            path = os.path.join("cache", filename)
                            await download_image(url, path)
                            photo_files.append(open(path, 'rb'))

                        bot.send_media_group(
                            message.chat.id,
                            [InputMediaPhoto(p) for p in photo_files]
                        )

                        for file in photo_files:
                            file.close()
                            os.remove(file.name)

            except Exception as e:
                bot.send_message(message.chat.id, f"❌ ত্রুটি: {e}")

        asyncio.run(process())