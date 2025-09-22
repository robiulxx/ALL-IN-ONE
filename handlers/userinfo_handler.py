# -*- coding: utf-8 -*-

import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Chat, User
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode

# লগিং সেটআপ
logger = logging.getLogger(__name__)

# প্রোফাইল ছবি না পাওয়া গেলে ডিফল্ট ছবি
PROFILE_ERROR_URL = "https://telegra.ph/file/de3464973405308fd8727.jpg"

# অ্যাকাউন্ট তৈরির তারিখ অনুমান করার ফাংশন
def _estimate_account_creation_date(user_id: int) -> datetime:
    """ইউজার আইডির উপর ভিত্তি করে অ্যাকাউন্ট তৈরির তারিখ অনুমান করে।"""
    # এই পদ্ধতিটি ইউজার আইডির প্রথম ২২ বিট ব্যবহার করে, যা টেলিগ্রামের ইন্টারনাল টাইমস্ট্যাম্প।
    timestamp = ((user_id >> 22) + 1291560300)
    return datetime.fromtimestamp(timestamp)

# অ্যাকাউন্টের বয়স গণনা করার ফাংশন
def _calculate_account_age(creation_date: datetime) -> str:
    """অ্যাকাউন্ট তৈরির তারিখ থেকে বর্তমান বয়স গণনা করে।"""
    today = datetime.now()
    delta = relativedelta(today, creation_date)
    return f"{delta.years} বছর, {delta.months} মাস, {delta.days} দিন"

# ব্যবহারকারী বা চ্যাটের তথ্য ফর্ম্যাট করার ফাংশন
async def _format_user_or_chat_info(entity: User | Chat, context: ContextTypes.DEFAULT_TYPE) -> dict:
    """ব্যবহারকারী বা চ্যাটের তথ্য সংগ্রহ করে একটি ডিকশনারিতে প্রদান করে।"""
    info = {}
    photo_url = PROFILE_ERROR_URL

    if isinstance(entity, User):
        # ব্যবহারকারীর তথ্য
        info['type'] = "ব্যবহারকারী"
        info['title'] = "🌟 ব্যবহারকারীর তথ্য 🌟"
        info['নাম'] = f"{entity.first_name} {entity.last_name or ''}".strip()
        info['আইডি'] = f"`{entity.id}`"
        info['ইউজারনেম'] = f"@{entity.username}" if entity.username else "নেই"
        info['বট'] = "✅ হ্যাঁ" if entity.is_bot else "❌ না"

        # অ্যাকাউন্ট তৈরির তারিখ এবং বয়স
        creation_date = _estimate_account_creation_date(entity.id)
        info['অ্যাকাউন্ট তৈরি'] = creation_date.strftime("%B %d, %Y")
        info['অ্যাকাউন্টের বয়স'] = _calculate_account_age(creation_date)

        # প্রোফাইল ছবি
        try:
            photos = await context.bot.get_user_profile_photos(entity.id, limit=1)
            if photos and photos.photos:
                file = await context.bot.get_file(photos.photos[0][-1].file_id)
                photo_url = file.file_path
        except Exception as e:
            logger.warning(f"প্রোফাইল ছবি পাওয়া যায়নি: {e}")

    elif isinstance(entity, Chat):
        # চ্যাট/গ্রুপ/চ্যানেলের তথ্য
        info['type'] = "চ্যাট"
        info['title'] = "🌟 চ্যাট তথ্য 🌟"
        info['নাম'] = entity.title
        info['আইডি'] = f"`{entity.id}`"
        info['ইউজারনেম'] = f"@{entity.username}" if entity.username else "নেই"
        info['টাইপ'] = entity.type.capitalize()
        try:
            info['সদস্য সংখ্যা'] = await context.bot.get_chat_member_count(entity.id)
        except Exception as e:
            info['সদস্য সংখ্যা'] = "N/A"
            logger.warning(f"সদস্য সংখ্যা পাওয়া যায়নি: {e}")

        # চ্যাটের ছবি
        try:
            if entity.photo:
                file = await context.bot.get_file(entity.photo.big_file_id)
                photo_url = file.file_path
        except Exception as e:
            logger.warning(f"চ্যাটের ছবি পাওয়া যায়নি: {e}")

    caption = f"<b>{info.pop('title')}</b>\n\n"
    # তথ্যগুলোকে মার্কডাউন হিসেবে ফর্ম্যাট করা
    caption += "\n".join([f"<b>{key.replace('_', ' ').capitalize()}:</b> {value}" for key, value in info.items()])

    return {"caption": caption.replace('`', ''), "photo_url": photo_url, "entity": entity} # HTML parse mode এর জন্য backtick (` `) সরানো হয়েছে


async def user_info_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/info এবং /id কমান্ড হ্যান্ডলার।"""
    message = update.effective_message
    chat = update.effective_chat
    user_to_find = None
    entity_id = None

    progress_message = await message.reply_text("✨ তথ্য সংগ্রহ করা হচ্ছে...")

    try:
        if message.reply_to_message:
            user_to_find = message.reply_to_message.from_user
        elif context.args:
            arg = context.args[0]
            entity_id = arg.lstrip('@') if arg.startswith('@') else int(arg)
        else:
            user_to_find = message.from_user

        if user_to_find:
            entity_id = user_to_find.id

        if not entity_id:
             await progress_message.edit_text("অনুগ্রহ করে একজন ব্যবহারকারীকে উল্লেখ করুন অথবা কোনো মেসেজে রিপ্লাই দিন।")
             return

        try:
            entity = await context.bot.get_chat(chat_id=entity_id)
        except Exception as e:
            logger.error(f"তথ্য পেতে সমস্যা হয়েছে: {e}")
            await progress_message.edit_text("দুঃখিত, এই ব্যবহারকারী বা চ্যাটটি খুঁজে পাওয়া যায়নি অথবা আমার অ্যাক্সেস নেই।")
            return

        result = await _format_user_or_chat_info(entity, context)
        caption = result['caption']
        photo_url = result['photo_url']
        found_entity = result['entity']

        buttons = []
        if isinstance(found_entity, User):
            buttons.append([InlineKeyboardButton("🔗 পার্মানেন্ট লিংক", url=f"tg://user?id={found_entity.id}")])
        
        await context.bot.send_photo(
            chat_id=chat.id,
            photo=photo_url,
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons) if buttons else None
        )
        await progress_message.delete()

    except ValueError:
        await progress_message.edit_text("ভুল ইনপুট। অনুগ্রহ করে একটি সঠিক ইউজারনেম (@username) অথবা ইউজার আইডি দিন।")
    except Exception as e:
        logger.error(f"info কমান্ডে একটি ত্রুটি হয়েছে: {e}")
        await progress_message.edit_text("একটি অপ্রত্যাশিত সমস্যা হয়েছে। অনুগ্রহ করে আবার চেষ্টা করুন।")


def register(application: Application) -> None:
    """
    এই ফাংশনটি আপনার টেলিগ্রাম বট অ্যাপ্লিকেশনে /info এবং /id কমান্ড হ্যান্ডলারগুলো রেজিস্টার করে।
    """
    info_handler = CommandHandler(["info", "id"], user_info_command)
    application.add_handler(info_handler)
    logger.info("User Info handler সফলভাবে রেজিস্টার করা হয়েছে।")

