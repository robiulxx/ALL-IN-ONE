# handlers/userinfo_handler.py

import requests
import os

# আপনার Render ওয়েবসাইটের API URL টি এখানে বসান
WEBSITE_API_URL = os.environ.get("WEBSITE_API_URL", "https://info-8nee.onrender.com/api/info")

def get_info_from_api(query):
    """
    Calls the website API to get entity information.
    """
    try:
        response = requests.get(WEBSITE_API_URL, params={'query': query}, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {'status': 'error', 'message': f"API connection error: {e}"}

def format_reply(info):
    """
    আপনার দেওয়া নতুন ফরম্যাট অনুযায়ী ডেটা সাজানো হচ্ছে।
    """
    entity_type = info.get('type')
    lines = []

    if entity_type in ['User', 'Bot']:
        header = f"✘「 {entity_type} Info 」"
        lines.append(header)
        lines.append(f"↯ Name: {info.get('first_name')} {info.get('last_name', '')}")
        lines.append(f"↯ Username: @{info.get('username')}")
        lines.append(f"↯ User ID: <code>{info.get('id')}</code>")
        
        if entity_type == 'Bot':
            lines.append(f"↯ Verified: {'Yes' if info.get('is_verified') else 'No'}")
            lines.append(f"↯ Can Join Groups: {'Yes' if info.get('can_join_groups') else 'No'}")
        else: # User
            lines.append(f"↯ Premium: {'Yes' if info.get('is_premium') else 'No'}")
            lines.append(f"↯ Verified: {'Yes' if info.get('is_verified') else 'No'}")
            lines.append(f"↯ Status: {info.get('status')}")
        
        lines.append(f"↯ Account Created: {info.get('account_created')}")
        lines.append(f"↯ Age: {info.get('account_age')}")
    
    elif entity_type in ['Group', 'Channel']:
        header = f"✘「 {entity_type} Info 」"
        lines.append(header)
        lines.append(f"↯ Name: {info.get('title')}")
        lines.append(f"↯ ID: <code>{info.get('id')}</code>")
        lines.append(f"↯ Username: @{info.get('username')}")
        lines.append(f"↯ Type: {info.get('type_detail')}")
        lines.append(f"↯ Status: {info.get('status')}")
        lines.append(f"↯ Verified: {'Yes' if info.get('is_verified') else 'No'}")
        lines.append(f"↯ Members: {info.get('participants_count'):,}")

    return "\n".join(lines)

def register(bot, custom_command_handler, COMMAND_PREFIXES):
    """
    Registers the /info and /id command handler.
    """
    @custom_command_handler('info', 'id')
    def info_command(message):
        query = ""
        if message.reply_to_message:
            query = str(message.reply_to_message.from_user.id)
        else:
            parts = message.text.split(maxsplit=1)
            if len(parts) > 1:
                query = parts[1]
            else:
                query = str(message.from_user.id)
        
        bot.send_chat_action(message.chat.id, 'typing')
        response_data = get_info_from_api(query)
        
        if response_data.get('status') == 'error':
            error_message = f"❌ <b>Error:</b> {response_data.get('message', 'Unknown error')}"
            # ১ নম্বর পরিবর্তন: message.reply_to এর বদলে send_message ব্যবহার করা হয়েছে
            bot.send_message(message.chat.id, error_message)
            return
        
        info = response_data.get('data', {})
        photo_url = info.get('photo_url')
        # ৩ নম্বর পরিবর্তন: নতুন ফরম্যাট অনুযায়ী রিপ্লাই তৈরি
        reply_text = format_reply(info)

        # ২ নম্বর পরিবর্তন: বটের ছবি দেখানোর জন্য লজিকটি ইউজার এবং বট উভয়ের জন্যই কাজ করার কথা
        if photo_url and photo_url != 'N/A':
            full_photo_url = f"https://{WEBSITE_API_URL.split('/')[2]}{photo_url}"
            try:
                # ১ নম্বর পরিবর্তন: reply_to_message_id ছাড়া ছবি পাঠানো হচ্ছে
                bot.send_photo(message.chat.id, photo=full_photo_url, caption=reply_text)
            except Exception:
                bot.send_message(message.chat.id, reply_text)
        else:
            bot.send_message(message.chat.id, reply_text)
