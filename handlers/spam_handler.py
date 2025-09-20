import threading
import time
import telebot.apihelper
from telebot.types import Message, InputFile
import re
import os

spam_threads = {}

# --- নরমাল স্প্যাম হ্যান্ডেলার: যতক্ষণ না বন্ধ করা হয় ---
def _run_normal_spam_task(bot, current_chat_id, text_to_spam, current_number):
    thread = spam_threads.get(current_chat_id)
    if not thread:
        return

    message_sent_count = 0
    while not thread.stop_spam:
        try:
            if current_number is not None:
                bot.send_message(current_chat_id, f"{text_to_spam} {current_number}")
                current_number += 1
            else:
                bot.send_message(current_chat_id, text_to_spam)

            message_sent_count += 1
            time.sleep(0.3) # প্রতি মেসেজের মধ্যে 0.3 সেকেন্ডের বিরতি

        except telebot.apihelper.ApiTelegramException as e:
            print(f"Telegram API Error in spam_task for chat {current_chat_id}: {e}")
            bot.send_message(current_chat_id, f"⚠️ স্প্যামিং বন্ধ হয়েছে: একটি টেলিগ্রাম API ত্রুটি হয়েছে (যেমন রেট লিমিট)।\nত্রুটি: `{e}`", parse_mode="Markdown")
            thread.stop_spam = True
            break
        except Exception as e:
            print(f"Generic Error in spam_task for chat {current_chat_id}: {e}")
            bot.send_message(current_chat_id, f"⚠️ স্প্যামিং বন্ধ হয়েছে: একটি অপ্রত্যাশিত ত্রুটি হয়েছে।\nত্রুটি: `{e}`", parse_mode="Markdown")
            thread.stop_spam = True
            break

    if current_chat_id in spam_threads:
        del spam_threads[current_chat_id]
    print(f"Normal spamming stopped for chat {current_chat_id}. Messages sent: {message_sent_count}")


def register(bot, custom_command_handler, command_prefixes_list): 

    def is_admin(chat_id, user_id):
        if chat_id > 0:  
            return True
        try:
            member = bot.get_chat_member(chat_id, user_id)
            return member.status in ['creator', 'administrator']
        except telebot.apihelper.ApiTelegramException as e:
            print(f"Error checking admin status for chat {chat_id}, user {user_id}: {e}")
            return False 

    @custom_command_handler("spam")
    def handle_spam(message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id

        if not is_admin(chat_id, user_id):
            bot.reply_to(message, "⛔ এই কমান্ডটি শুধুমাত্র গ্রুপের অ্যাডমিনরা ব্যবহার করতে পারবে।")
            return

        command_text = message.text.split(" ", 1)[0].lower()
        actual_command_len = 0
        for prefix in command_prefixes_list: 
            if command_text.startswith(f"{prefix}spam"):
                actual_command_len = len(f"{prefix}spam")
                break

        user_input_raw = message.text[actual_command_len:].strip()

        if chat_id in spam_threads and spam_threads[chat_id].is_alive():
            spam_threads[chat_id].stop_spam = True
            bot.reply_to(message, "✅ স্প্যামিং বন্ধ করা হয়েছে।")
            return

        if not user_input_raw:
            bot.reply_to(message, f"❌ স্প্যাম করার জন্য কিছু টেক্সট দিন। উদাহরণ:\n`{command_prefixes_list[0]}spam Hello World`\n`{command_prefixes_list[1]}spam Number 1`", parse_mode="Markdown") 
            return

        full_text = user_input_raw
        base_text = full_text
        start_number = None

        match = re.search(r'\s(\d+)$', full_text)
        if match:
            potential_number = int(match.group(1))
            if full_text.endswith(match.group(0)):
                start_number = potential_number
                base_text = full_text[:-len(match.group(0))].strip()

        spam_thread = threading.Thread(target=_run_normal_spam_task, args=(bot, chat_id, base_text, start_number))
        spam_thread.stop_spam = False
        spam_threads[chat_id] = spam_thread
        spam_thread.daemon = True
        spam_thread.start()

        bot.reply_to(message, f"🚀 স্প্যামিং শুরু হয়েছে! বন্ধ করতে আবার `{command_prefixes_list[0]}spam` অথবা `{command_prefixes_list[1]}spam` অথবা `{command_prefixes_list[2]}spam` লিখুন।", parse_mode="Markdown") 

    # --- টেক্সট ফাইল জেনারেটর হ্যান্ডেলার (/spmtxt) ---
    @custom_command_handler("spmtxt")
    def handle_spmtxt(message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id

        command_text_spmtxt = message.text.split(" ", 1)[0].lower()
        actual_command_len_spmtxt = 0
        for prefix in command_prefixes_list: 
            if command_text_spmtxt.startswith(f"{prefix}spmtxt"):
                actual_command_len_spmtxt = len(f"{prefix}spmtxt")
                break

        user_input_raw_spmtxt = message.text[actual_command_len_spmtxt:].strip()
        user_input_parts = user_input_raw_spmtxt.split(None, 1)

        if len(user_input_parts) < 2 or not user_input_parts[0].isdigit():
            bot.reply_to(message,
                         f"❌ টেক্সট ফাইল তৈরির জন্য সঠিক ফরম্যাট ব্যবহার করুন। উদাহরণ:\n"
                         f"`{command_prefixes_list[0]}spmtxt 100 Hello World`\n"
                         f"`{command_prefixes_list[1]}spmtxt 50 Number 1` (এখানে 1 থেকে শুরু হবে)",
                         parse_mode="Markdown")
            return

        spam_count = int(user_input_parts[0])
        full_text_to_process = user_input_parts[1].strip() if len(user_input_parts) > 1 else ""

        if not full_text_to_process:
            bot.reply_to(message, f"❌ টেক্সট ফাইল তৈরির জন্য কিছু টেক্সট দিন। উদাহরণ: `{command_prefixes_list[0]}spmtxt 100 Hello World`", parse_mode="Markdown") 
            return

        base_text = full_text_to_process
        start_number = None

        match = re.search(r'\s(\d+)$', full_text_to_process)
        if match:
            potential_number = int(match.group(1))
            if full_text_to_process.endswith(match.group(0)):
                start_number = potential_number
                base_text = full_text_to_process[:-len(match.group(0))].strip()

        bot.send_message(chat_id, "⏳ আপনার ফাইল তৈরি করা হচ্ছে, একটু অপেক্ষা করুন...")

        generated_lines = []
        for i in range(spam_count):
            if start_number is not None:
                generated_lines.append(f"{base_text} {start_number + i}")
            else:
                generated_lines.append(base_text)

        file_content = "\n".join(generated_lines)
        file_name = f"generated_spam_{chat_id}_{int(time.time())}.txt"

        try:
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(file_content)

            with open(file_name, "rb") as f:
                bot.send_document(chat_id, InputFile(f), caption=f"✅ আপনার `{spam_count}`টি লাইনসহ ফাইল তৈরি হয়ে গেছে!")

        except Exception as e:
            print(f"Error generating or sending file for chat {chat_id}: {e}")
            bot.send_message(chat_id, f"❌ ফাইল তৈরিতে বা পাঠাতে সমস্যা হয়েছে: `{e}`", parse_mode="Markdown")
        finally:
            if os.path.exists(file_name):
                os.remove(file_name)
                print(f"Cleaned up file: {file_name}")