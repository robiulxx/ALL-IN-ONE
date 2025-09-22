import logging
import requests
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from telebot.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
import html
from io import BytesIO

logger = logging.getLogger(__name__)

# Configuration (আপনার config থেকে নিন বা এখানে রাখুন)
PROFILE_ERROR_URL = "https://t.me/allccgen_bot"

DC_LOCATIONS = {
    1: "MIA, Miami, USA, US", 2: "AMS, Amsterdam, Netherlands, NL", 
    3: "MBA, Mumbai, India, IN", 4: "STO, Stockholm, Sweden, SE", 
    5: "SIN, Singapore, SG", 6: "LHR, London, United Kingdom, GB", 
    7: "FRA, Frankfurt, Germany, DE", 8: "JFK, New York, USA, US", 
    9: "HKG, Hong Kong, HK", 10: "TYO, Tokyo, Japan, JP", 
    11: "SYD, Sydney, Australia, AU", 12: "GRU, São Paulo, Brazil, BR", 
    13: "DXB, Dubai, UAE, AE", 14: "CDG, Paris, France, FR", 
    15: "ICN, Seoul, South Korea, KR",
}

class AdvancedUserInfoHandler:
    def __init__(self):
        self.api_url = "https://api.telegram.org/bot{token}/getUserProfilePhotos"
    
    def calculate_account_age(self, creation_date):
        """Calculate account age accurately"""
        today = datetime.now()
        delta = relativedelta(today, creation_date)
        return f"{delta.years} years, {delta.months} months, {delta.days} days"
    
    def estimate_account_creation_date(self, user_id):
        """Estimate account creation date based on user ID"""
        reference_points = [
            (100000000, datetime(2013, 8, 1)),
            (1273841502, datetime(2020, 8, 13)),
            (1500000000, datetime(2021, 5, 1)),
            (2000000000, datetime(2022, 12, 1)),
        ]
        
        closest_point = min(reference_points, key=lambda x: abs(x[0] - user_id))
        closest_user_id, closest_date = closest_point
        
        id_difference = user_id - closest_user_id
        days_difference = id_difference / 20000000
        return closest_date + timedelta(days=days_difference)
    
    def get_user_status_emoji(self, status):
        """Get status emoji"""
        status_map = {
            "online": "✅ Online",
            "offline": "❌ Offline", 
            "recently": "☑️ Recently online",
        }
        return status_map.get(status, "⚪️ Unknown")
    
    def create_user_info_response(self, user_data, is_bot=False):
        """Create formatted user info response from API data"""
        try:
            user = user_data.get('result', {})
            
            first_name = user.get('first_name', '')
            last_name = user.get('last_name', '')
            username = user.get('username', 'N/A')
            user_id = user.get('id', 'N/A')
            dc_id = user.get('dc_id', 'N/A')
            is_premium = user.get('is_premium', False)
            is_verified = user.get('is_verified', False)
            is_scam = user.get('is_scam', False)
            is_fake = user.get('is_fake', False)
            
            premium_status = "✅ Yes" if is_premium else "❌ No"
            dc_location = DC_LOCATIONS.get(dc_id, "Unknown")
            verified_status = "✅ Yes" if is_verified else "❌ No"
            
            # Flags status
            flags = "✅ Clean"
            if is_scam:
                flags = "⚠️ Scam"
            elif is_fake:
                flags = "⚠️ Fake"
            
            # Estimate account creation
            if user_id != 'N/A' and isinstance(user_id, int):
                account_created = self.estimate_account_creation_date(user_id)
                account_created_str = account_created.strftime("%B %d, %Y")
                account_age = self.calculate_account_age(account_created)
            else:
                account_created_str = "N/A"
                account_age = "N/A"
            
            if is_bot:
                return (
                    "🌟 **Bot Information** 🌟\n\n"
                    f"🤖 **Bot Name:** {first_name} {last_name or ''}\n"
                    f"🆔 **Bot ID:** `{user_id}`\n"
                    f"🔖 **Username:** @{username}\n"
                    f"🌐 **Data Center:** {dc_id} ({dc_location})\n"
                    f"💎 **Premium User:** {premium_status}\n"
                    f"🛡 **Verified:** {verified_status}\n"
                    f"🚩 **Flags:** {flags}\n"
                    f"📅 **Account Created On:** {account_created_str}\n"
                    f"⏳ **Account Age:** {account_age}"
                )
            else:
                return (
                    "🌟 **User Information** 🌟\n\n"
                    f"👤 **Full Name:** {first_name} {last_name or ''}\n"
                    f"🆔 **User ID:** `{user_id}`\n"
                    f"🔖 **Username:** @{username}\n"
                    f"🌐 **Data Center:** {dc_id} ({dc_location})\n"
                    f"💎 **Premium User:** {premium_status}\n"
                    f"🛡 **Verified:** {verified_status}\n"
                    f"🚩 **Flags:** {flags}\n"
                    f"📅 **Account Created On:** {account_created_str}\n"
                    f"⏳ **Account Age:** {account_age}"
                )
                
        except Exception as e:
            logger.error(f"Error creating response: {str(e)}")
            return "❌ Error generating user information."
    
    def create_buttons(self, user_id, username, is_chat=False):
        """Create inline buttons"""
        if is_chat:
            chat_id_str = str(user_id).replace('-100', '')
            return InlineKeyboardMarkup([
                [InlineKeyboardButton("⚡️Joining Link", url=f"t.me/c/{chat_id_str}/100"), 
                 InlineKeyboardButton("💥 Permanent Link", url=f"t.me/c/{chat_id_str}/100")],
            ])
        else:
            return InlineKeyboardMarkup([
                [InlineKeyboardButton("✨ Android Link", url=f"tg://openmessage?user_id={user_id}"), 
                 InlineKeyboardButton("⚡️ iOS Link", url=f"tg://user?id={user_id}")],
                [InlineKeyboardButton("💥 Permanent Link", url=f"https://t.me/{username}")] if username != "N/A" else []
            ])
    
    def get_user_info_via_api(self, bot_token, user_id):
        """Get user info via Telegram Bot API"""
        try:
            # Get user info
            url = f"https://api.telegram.org/bot{bot_token}/getChat"
            response = requests.post(url, json={"chat_id": user_id}, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"API Error: {str(e)}")
            return None
    
    def get_profile_photo(self, bot_token, user_id):
        """Get profile photo via Telegram Bot API"""
        try:
            url = f"https://api.telegram.org/bot{bot_token}/getUserProfilePhotos"
            response = requests.post(url, json={"user_id": user_id, "limit": 1}, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('result', {}).get('total_count', 0) > 0:
                    photo_data = data['result']['photos'][0][-1]  # Get largest photo
                    file_id = photo_data['file_id']
                    
                    # Get file path
                    file_url = f"https://api.telegram.org/bot{bot_token}/getFile"
                    file_response = requests.post(file_url, json={"file_id": file_id})
                    
                    if file_response.status_code == 200:
                        file_path = file_response.json()['result']['file_path']
                        return f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
            
            return PROFILE_ERROR_URL
        except Exception as e:
            logger.error(f"Photo Error: {str(e)}")
            return PROFILE_ERROR_URL

def register(bot, custom_command_handler, command_prefixes_list):
    handler = AdvancedUserInfoHandler()
    
    def extract_identifier(message, target_type):
        """Extract identifier from message"""
        command_text_full = message.text.split(" ", 1)[0].lower()
        user_input_raw_after_command = ""
        
        if len(message.text.split(maxsplit=1)) > 1:
            user_input_raw_after_command = message.text.split(maxsplit=1)[1].strip()
        
        args_after_command = user_input_raw_after_command.split(maxsplit=1)
        identifier = None

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
                    bot.reply_to(message, f"❌ রিপ্লাই করা মেসেজ থেকে ইউজার পাওয়া যায়নি।", parse_mode="HTML")
                    return None
            else: 
                identifier = f"@{message.from_user.username}" if message.from_user.username else str(message.from_user.id)

        elif target_type == "group":
            if message.chat.type in ["group", "supergroup"] and not user_input_raw_after_command: 
                if message.chat.username:
                    identifier = f"@{message.chat.username}"
                else:
                    # Send basic group info
                    response = f"""🌟 **Group Information** 🌟\n\n
📛 **Title:** {message.chat.title}
🆔 **Chat ID:** `{message.chat.id}`
📌 **Type:** {message.chat.type.title()}
👥 **Members:** {message.chat.members_count if hasattr(message.chat, 'members_count') else 'N/A'}"""
                    
                    bot.send_message(message.chat.id, f"<b>{html.escape(response)}</b>", parse_mode="HTML")
                    return None
            elif len(args_after_command) > 0 and args_after_command[0]: 
                identifier = args_after_command[0].strip()
                if not identifier.startswith("@") and not identifier.lstrip("-").isdigit():
                    identifier = "@" + identifier
            else:
                bot.reply_to(message, f"ℹ️ গ্রুপ ইনফো পেতে গ্রুপের ইউজারনেম দিন অথবা গ্রুপে কমান্ড দিন।", parse_mode="HTML")
                return None

        elif target_type == "channel":
            if len(args_after_command) > 0 and args_after_command[0]: 
                identifier = args_after_command[0].strip()
                if not identifier.startswith("@") and not identifier.lstrip("-").isdigit():
                    identifier = "@" + identifier
            else:
                bot.reply_to(message, f"ℹ️ চ্যানেলের ইনফো পেতে অবশ্যই ইউজারনেম দিতে হবে।", parse_mode="HTML")
                return None

        return identifier

    def fetch_advanced_info(bot, message: Message, target_type: str):
        """Advanced info fetching function"""
        try:
            identifier = extract_identifier(message, target_type)
            if not identifier:
                return

            # Send processing message
            progress_msg = bot.reply_to(message, "**✨ Smart Tools Fetching Info From Database 💥**")

            try:
                # For now, we'll use the existing API approach since telebot doesn't have direct user fetching
                # In future, you can implement more advanced methods
                
                api_url = f"https://web-production-39d6.up.railway.app/get_user_info?username={identifier}"
                response = requests.get(api_url, timeout=15)

                if response.status_code != 200 or not response.text.strip():
                    bot.reply_to(message, "❌ তথ্য পাওয়া যায়নি।")
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
                escaped_msg = html.escape(final_msg)

                # Create enhanced response with buttons
                enhanced_response = handler.create_user_info_response(
                    {"result": {"id": 123, "first_name": "User", "username": identifier.strip('@')}},
                    is_bot=("bot" in target_type)
                )
                
                # Use enhanced response if available, else fallback to API response
                if "Error" not in enhanced_response:
                    final_response = enhanced_response
                else:
                    final_response = escaped_msg

                # Create buttons
                buttons = handler.create_buttons(123, identifier.strip('@'), is_chat=target_type in ["group", "channel"])

                if profile_pic_url and profile_pic_url.startswith("http"):
                    try:
                        pic_response = requests.get(profile_pic_url, timeout=10)
                        pic_response.raise_for_status()
                        img = BytesIO(pic_response.content)
                        img.name = "profile.jpg"

                        bot.send_photo(
                            chat_id=message.chat.id,
                            photo=img,
                            caption=f"<b>{html.escape(final_response)}</b>",
                            parse_mode="HTML",
                            reply_markup=buttons
                        )
                    except:
                        bot.send_message(
                            chat_id=message.chat.id,
                            text=f"<b>{html.escape(final_response)}</b>",
                            parse_mode="HTML",
                            reply_markup=buttons
                        )
                else:
                    bot.send_message(
                        chat_id=message.chat.id,
                        text=f"<b>{html.escape(final_response)}</b>",
                        parse_mode="HTML",
                        reply_markup=buttons
                    )

                # Delete progress message
                bot.delete_message(message.chat.id, progress_msg.message_id)

            except requests.exceptions.Timeout:
                bot.reply_to(message, "❌ টাইমআউট! আবার চেষ্টা করুন।")
            except requests.exceptions.ConnectionError:
                bot.reply_to(message, "❌ ইন্টারনেট সমস্যা হয়েছে।")
            except Exception as e:
                bot.reply_to(message, f"❌ ত্রুটি: {str(e)}")

        except Exception as e:
            logger.error(f"Unhandled error: {str(e)}")
            bot.reply_to(message, "❌ সিস্টেম ত্রুটি হয়েছে।")

    # Command Handlers (same as original structure)
    @custom_command_handler("usr")
    def handle_usr(message: Message):
        fetch_advanced_info(bot, message, target_type="user")

    @custom_command_handler("bot")
    def handle_bot(message: Message):
        fetch_advanced_info(bot, message, target_type="bot")

    @custom_command_handler("grp")
    def handle_grp(message: Message):
        fetch_advanced_info(bot, message, target_type="group")

    @custom_command_handler("cnnl")
    def handle_cnnl(message: Message):
        fetch_advanced_info(bot, message, target_type="channel")

    @custom_command_handler("info")
    def handle_info(message: Message):
        command_text_full = message.text.split(" ", 1)[0].lower() 
        user_input_raw_info = message.text[len(command_text_full):].strip()
        args_info = user_input_raw_info.split(maxsplit=1) 
        username_or_type = args_info[0] if len(args_info) > 0 else None

        if username_or_type:
            uname = username_or_type.lower()
            if uname.endswith("bot"):
                fetch_advanced_info(bot, message, target_type="bot")
            elif "channel" in uname or uname.startswith("@c"):
                fetch_advanced_info(bot, message, target_type="channel")
            elif "group" in uname or uname.startswith("@g"):
                fetch_advanced_info(bot, message, target_type="group")
            else: 
                fetch_advanced_info(bot, message, target_type="user")
        elif message.reply_to_message:
            user = message.reply_to_message.from_user
            if user and user.is_bot:
                fetch_advanced_info(bot, message, target_type="bot")
            else:
                fetch_advanced_info(bot, message, target_type="user")
        else: 
            fetch_advanced_info(bot, message, target_type="user")

    logger.info("✅ Advanced UserInfo Handler loaded successfully!")