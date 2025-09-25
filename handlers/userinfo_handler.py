# handlers/userinfo_handler.py

import requests
import os

# আপনার Render ওয়েবসাইটের API URL টি এখানে বসান
# এই URL টি os.environ.get ব্যবহার করে নিলে সবচেয়ে ভালো হয়
WEBSITE_API_URL = os.environ.get("WEBSITE_API_URL", "https://your-render-app.onrender.com/api/info")

def get_info_from_api(query):
    """
    Calls the website API to get entity information.
    """
    try:
        response = requests.get(WEBSITE_API_URL, params={'query': query}, timeout=30)
        response.raise_for_status()  # HTTP error থাকলে exception raise করবে
        return response.json()
    except requests.exceptions.RequestException as e:
        return {'error': f"API connection error: {e}"}

def format_reply(info):
    """
    Formats the JSON data from the API into a readable string.
    """
    reply_text = ""
    entity_type = info.get('type')

    if entity_type in ['User', 'Bot']:
        reply_text = (
            f"👤 <b>{info.get('type')} Information</b>\n\n"
            f"<b>Name:</b> {info.get('first_name')} {info.get('last_name', '')}\n"
            f"<b>User ID:</b> <code>{info.get('id')}</code>\n"
            f"<b>Username:</b> @{info.get('username')}\n"
            f"<b>Verified:</b> {'✅ Yes' if info.get('is_verified') else '❌ No'}\n"
        )
        if entity_type == 'Bot':
            reply_text += f"<b>Can Join Groups:</b> {'✅ Yes' if info.get('can_join_groups') else '❌ No'}\n"
        else:
            reply_text += f"<b>Premium:</b> {'✅ Yes' if info.get('is_premium') else '❌ No'}\n"
            reply_text += f"<b>Status:</b> {info.get('status')}\n"
        
        reply_text += (
            f"<b>Account Created:</b> {info.get('account_created')}\n"
            f"<b>Account Age:</b> {info.get('account_age')}\n"
        )
    
    elif entity_type in ['গ্রুপ', 'চ্যানেল']:
        reply_text = (
            f"🏢 <b>{info.get('type')} Information</b>\n\n"
            f"<b>Name:</b> {info.get('title')}\n"
            f"<b>ID:</b> <code>{info.get('id')}</code>\n"
            f"<b>Username:</b> @{info.get('username')}\n"
            f"<b>Type:</b> {info.get('type_detail')}\n"
            f"<b>Status:</b> {info.get('status')}\n"
            f"<b>Verified:</b> {'✅ Yes' if info.get('is_verified') else '❌ No'}\n"
            f"<b>Members:</b> {info.get('participants_count'):,}\n"
        )
    
    return reply_text

def register(bot, custom_command_handler, COMMAND_PREFIXES):
    """
    Registers the /info and /id command handler.
    """
    @custom_command_handler('info', 'id')
    def info_command(message):
        query = ""
        # ইনপুট নির্ধারণ করা হচ্ছে
        if message.reply_to_message:
            query = str(message.reply_to_message.from_user.id)
        else:
            parts = message.text.split(maxsplit=1)
            if len(parts) > 1:
                query = parts[1]
            else:
                query = str(message.from_user.id)
        
        # বটকে "Typing..." অ্যাকশন দেখাতে বলা হচ্ছে
        bot.send_chat_action(message.chat.id, 'typing')
        
        # API থেকে ডেটা আনা হচ্ছে
        response_data = get_info_from_api(query)
        
        if response_data.get('status') == 'error':
            bot.reply_to(message, f"❌ <b>Error:</b> {response_data.get('message', 'Unknown error')}")
            return
        
        info = response_data.get('data', {})
        photo_url = info.get('photo_url')
        reply_text = format_reply(info)

        # ছবি থাকলে ছবির সাথে মেসেজ পাঠানো হবে, নাহলে শুধু টেক্সট
        if photo_url and photo_url != 'N/A':
            # সম্পূর্ণ URL তৈরি করা হচ্ছে
            full_photo_url = f"https://{WEBSITE_API_URL.split('/')[2]}{photo_url}"
            try:
                bot.send_photo(message.chat.id, photo=full_photo_url, caption=reply_text, reply_to_message_id=message.message_id)
            except Exception:
                # ছবি পাঠাতে সমস্যা হলে শুধু টেক্সট পাঠানো হবে
                bot.reply_to(message, reply_text)
        else:
            bot.reply_to(message, reply_text)
