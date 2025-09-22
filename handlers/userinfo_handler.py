import logging
import requests
from datetime import datetime, timedelta
from telebot.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
import html
from io import BytesIO
import re

logger = logging.getLogger(__name__)

# Configuration
PROFILE_ERROR_URL = "https://t.me/allccgen_bot"

DC_LOCATIONS = {
    1: "MIA, Miami, USA, US",
    2: "AMS, Amsterdam, Netherlands, NL",
    3: "MBA, Mumbai, India, IN",
    4: "STO, Stockholm, Sweden, SE",
    5: "SIN, Singapore, SG",
    6: "LHR, London, United Kingdom, GB",
    7: "FRA, Frankfurt, Germany, DE",
    8: "JFK, New York, USA, US",
    9: "HKG, Hong Kong, HK",
    10: "TYO, Tokyo, Japan, JP",
    11: "SYD, Sydney, Australia, AU",
    12: "GRU, São Paulo, Brazil, BR",
    13: "DXB, Dubai, UAE, AE",
    14: "CDG, Paris, France, FR",
    15: "ICN, Seoul, South Korea, KR",
}

START_MESSAGE = """
<b>Welcome to the Telegram Info Bot 🌟</b>

Get quick and detailed insights about any Telegram user or group.

<b>Features:</b>
👤 Full Name  
🆔 User ID  
🔖 Username  
💬 Chat ID  
🌐 Data Center Location  
💎 Premium Status  
🛡 Verified Badge  
🚩 Account Flags  
🕒 Online Status  
📅 Account Creation Date  
⏳ Account Age

Use /info or /id to get started! 🚀
"""

class AdvancedUserInfoHandler:
    def __init__(self):
        self.api_base_url = "https://api.telegram.org/bot"
    
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
    
    def get_user_info_via_bot_api(self, bot_token, user_id):
        """Get user info via Telegram Bot API"""
        try:
            url = f"{self.api_base_url}{bot_token}/getChat"
            response = requests.post(url, json={"chat_id": user_id}, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"API Error: {str(e)}")
            return None
    
    def get_profile_photo_url(self, bot_token, user_id):
        """Get profile photo URL via Telegram Bot API"""
        try:
            # Get user profile photos
            url = f"{self.api_base_url}{bot_token}/getUserProfilePhotos"
            response = requests.post(url, json={"user_id": user_id, "limit": 1}, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('result', {}).get('total_count', 0) > 0:
                    # Get the largest photo
                    photo_data = data['result']['photos'][0][-1]
                    file_id = photo_data['file_id']
                    
                    # Get file path
                    file_url = f"{self.api_base_url}{bot_token}/getFile"
                    file_response = requests.post(file_url, json={"file_id": file_id})
                    
                    if file_response.status_code == 200:
                        file_path = file_response.json()['result']['file_path']
                        return f"{self.api_base_url}{bot_token}/{file_path}"
            
            return PROFILE_ERROR_URL
        except Exception as e:
            logger.error(f"Photo Error: {str(e)}")
            return PROFILE_ERROR_URL
    
    def create_user_info_response(self, user_data, chat_id=None, is_bot=False):
        """Create formatted user info response"""
        try:
            user = user_data.get('result', {})
            
            first_name = user.get('first_name', 'N/A')
            last_name = user.get('last_name', '')
            username = user.get('username', 'N/A')
            user_id = user.get('id', 'N/A')
            
            # These fields are not available in Bot API, so we'll use estimates/placeholders
            dc_id = 4  # Default DC
            dc_location = DC_LOCATIONS.get(dc_id, "Unknown")
            is_premium = user.get('is_premium', False)
            is_verified = False  # Not available in Bot API
            is_scam = user.get('is_scam', False)
            is_fake = user.get('is_fake', False)
            
            premium_status = "✅ Yes" if is_premium else "❌ No"
            verified_status = "✅ Yes" if is_verified else "❌ No"
            
            # Flags status
            flags = "✅ Clean"
            if is_scam:
                flags = "⚠️ Scam"
            elif is_fake:
                flags = "⚠️ Fake"
            
            # Estimate account creation for actual user IDs
            account_created_str = "N/A"
            account_age = "N/A"
            
            if user_id != 'N/A' and isinstance(user_id, int):
                try:
                    account_created = self.estimate_account_creation_date(user_id)
                    account_created_str = account_created.strftime("%B %d, %Y")
                    account_age = self.calculate_account_age(account_created)
                except:
                    pass
            
            chat_id_display = chat_id if chat_id else user_id
            
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
                    f"💬 **Chat ID:** `{chat_id_display}`\n"
                    f"🌐 **Data Center:** {dc_id} ({dc_location})\n"
                    f"💎 **Premium User:** {premium_status}\n"
                    f"🛡 **Verified:** {verified_status}\n"
                    f"🚩 **Flags:** {flags}\n"
                    f"🕒 **Status:** ⚪️ Unknown\n"  # Status not available in Bot API
                    f"📅 **Account Created On:** {account_created_str}\n"
                    f"⏳ **Account Age:** {account_age}"
                )
                
        except Exception as e:
            logger.error(f"Error creating response: {str(e)}")
            return "❌ Error generating user information."
    
    def create_chat_info_response(self, chat_data):
        """Create formatted chat info response"""
        try:
            chat = chat_data.get('result', {})
            
            title = chat.get('title', 'N/A')
            chat_id = chat.get('id', 'N/A')
            chat_type = chat.get('type', 'N/A')
            members_count = chat.get('members_count', 'N/A')
            
            dc_id = 4  # Default DC
            dc_location = DC_LOCATIONS.get(dc_id, "Unknown")
            
            return (
                f"🌟 **Chat Information** 🌟\n\n"
                f"📛 **Title:** {title}\n"
                f"🆔 **ID:** `{chat_id}`\n"
                f"📌 **Type:** {chat_type.title()}\n"
                f"👥 **Member Count:** {members_count}\n"
                f"🌐 **Data Center:** {dc_id} ({dc_location})"
            )
        except Exception as e:
            logger.error(f"Error creating chat response: {str(e)}")
            return "❌ Error generating chat information."
    
    def create_user_buttons(self, user_id, username):
        """Create inline buttons for user"""
        buttons = []
        if username != 'N/A':
            buttons.append([
                InlineKeyboardButton("✨ Android Link", url=f"tg://openmessage?user_id={user_id}"),
                InlineKeyboardButton("⚡️ iOS Link", url=f"tg://user?id={user_id}")
            ])
            buttons.append([
                InlineKeyboardButton("💥 Permanent Link", url=f"https://t.me/{username}")
            ])
        return InlineKeyboardMarkup(buttons) if buttons else None
    
    def create_chat_buttons(self, chat_id, username):
        """Create inline buttons for chat"""
        chat_id_str = str(chat_id).replace('-100', '')
        buttons = []
        if username != 'N/A':
            buttons.append([
                InlineKeyboardButton("⚡️ Joining Link", url=f"t.me/{username}"),
                InlineKeyboardButton("💥 Permanent Link", url=f"t.me/{username}")
            ])
        elif chat_id != 'N/A':
            buttons.append([
                InlineKeyboardButton("⚡️ Share Link", url=f"t.me/c/{chat_id_str}/100")
            ])
        return InlineKeyboardMarkup(buttons) if buttons else None
    
    def extract_identifier(self, message_text, target_type):
        """Extract username/ID from message text"""
        try:
            parts = message_text.split(maxsplit=1)
            if len(parts) > 1:
                identifier = parts[1].split()[0].strip()
                # Clean the identifier
                identifier = re.sub(r'https?://t\.me/', '', identifier)
                identifier = identifier.strip('@')
                return identifier
            return None
        except Exception as e:
            logger.error(f"Error extracting identifier: {str(e)}")
            return None

def register(bot, custom_command_handler, command_prefixes_list):
    handler = AdvancedUserInfoHandler()
    
    @custom_command_handler("start")
    def handle_start(message: Message):
        """Handle /start command"""
        try:
            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("Update Channel", url="https://t.me/Modvip_rm"),
                 InlineKeyboardButton("My Dev👨‍💻", url="https://t.me/RS_Zone24")]
            ])
            
            bot.send_message(
                message.chat.id,
                START_MESSAGE,
                parse_mode="HTML",
                disable_web_page_preview=True,
                reply_markup=buttons
            )
        except Exception as e:
            logger.error(f"Start command error: {str(e)}")
    
    def handle_info_command(message: Message, target_type="user"):
        """Main info command handler"""
        try:
            # Send processing message
            progress_msg = bot.reply_to(message, "**✨ Smart Tools Fetching Info From Database 💥**")
            
            identifier = None
            user_data = None
            is_bot = False
            
            # Case 1: No arguments - current user
            if not handler.extract_identifier(message.text, target_type) and not message.reply_to_message:
                user_data = {
                    'result': {
                        'id': message.from_user.id,
                        'first_name': message.from_user.first_name,
                        'last_name': message.from_user.last_name or '',
                        'username': message.from_user.username or 'N/A',
                        'is_premium': getattr(message.from_user, 'is_premium', False),
                        'is_bot': message.from_user.is_bot
                    }
                }
                identifier = message.from_user.username or str(message.from_user.id)
                is_bot = message.from_user.is_bot
            
            # Case 2: Reply to message
            elif message.reply_to_message:
                user = message.reply_to_message.from_user
                user_data = {
                    'result': {
                        'id': user.id,
                        'first_name': user.first_name,
                        'last_name': user.last_name or '',
                        'username': user.username or 'N/A',
                        'is_premium': getattr(user, 'is_premium', False),
                        'is_bot': user.is_bot
                    }
                }
                identifier = user.username or str(user.id)
                is_bot = user.is_bot
                target_type = "bot" if user.is_bot else "user"
            
            # Case 3: Username provided
            else:
                identifier = handler.extract_identifier(message.text, target_type)
                if identifier:
                    # Try to get user info via Bot API
                    user_data = handler.get_user_info_via_bot_api(bot.token, identifier)
                    if not user_data or not user_data.get('ok'):
                        # If user not found, try as chat
                        user_data = handler.get_user_info_via_bot_api(bot.token, f"@{identifier}")
            
            # Generate response
            if user_data and user_data.get('ok'):
                if target_type in ["user", "bot"]:
                    response = handler.create_user_info_response(
                        user_data, 
                        message.chat.id, 
                        is_bot=(target_type == "bot" or user_data['result'].get('is_bot', False))
                    )
                    buttons = handler.create_user_buttons(
                        user_data['result']['id'], 
                        user_data['result'].get('username', 'N/A')
                    )
                else:  # group/channel
                    response = handler.create_chat_info_response(user_data)
                    buttons = handler.create_chat_buttons(
                        user_data['result']['id'],
                        user_data['result'].get('username', 'N/A')
                    )
                
                # Get profile photo
                photo_url = handler.get_profile_photo_url(bot.token, user_data['result']['id'])
                
                # Send response with photo
                if photo_url and photo_url != PROFILE_ERROR_URL:
                    try:
                        photo_response = requests.get(photo_url, timeout=10)
                        if photo_response.status_code == 200:
                            img = BytesIO(photo_response.content)
                            img.name = "profile.jpg"
                            
                            bot.send_photo(
                                chat_id=message.chat.id,
                                photo=img,
                                caption=f"<code>{html.escape(response)}</code>",
                                parse_mode="HTML",
                                reply_markup=buttons
                            )
                        else:
                            raise Exception("Photo download failed")
                    except:
                        bot.send_message(
                            chat_id=message.chat.id,
                            text=f"<code>{html.escape(response)}</code>",
                            parse_mode="HTML",
                            reply_markup=buttons
                        )
                else:
                    bot.send_message(
                        chat_id=message.chat.id,
                        text=f"<code>{html.escape(response)}</code>",
                        parse_mode="HTML",
                        reply_markup=buttons
                    )
            else:
                bot.reply_to(message, "❌ User/chat not found or access denied.")
            
            # Delete progress message
            try:
                bot.delete_message(message.chat.id, progress_msg.message_id)
            except:
                pass
                
        except Exception as e:
            logger.error(f"Info command error: {str(e)}")
            try:
                bot.reply_to(message, f"❌ Error: {str(e)}")
            except:
                pass
    
    # Command handlers
    @custom_command_handler("info", "id")
    def handle_info(message: Message):
        handle_info_command(message, "user")
    
    @custom_command_handler("usr")
    def handle_usr(message: Message):
        handle_info_command(message, "user")
    
    @custom_command_handler("bot")
    def handle_bot(message: Message):
        handle_info_command(message, "bot")
    
    @custom_command_handler("grp")
    def handle_grp(message: Message):
        handle_info_command(message, "group")
    
    @custom_command_handler("cnnl")
    def handle_cnnl(message: Message):
        handle_info_command(message, "channel")
    
    logger.info("✅ UserInfo Handler loaded successfully!")

# Test function
if __name__ == "__main__":
    print("🧪 UserInfo Handler module loaded successfully!")
