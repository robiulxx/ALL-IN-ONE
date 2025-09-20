import os
import re
import requests
import subprocess
from telebot import TeleBot
from telebot.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    InputMediaPhoto
)
import threading
import json
import time
from typing import Optional
import tempfile
from urllib.parse import urlparse

# === APIs ===
SEARCH_API = "https://smartytdl.vercel.app/search?q="
DOWNLOAD_API = "https://smartytdl.vercel.app/dl?url="

# === Store user-specific data ===
user_search_results = {}
user_sent_messages = {}
user_thumbnail_files = {}

# === Helper Functions ===
def download_file(url, filename, bot=None, chat_id=None):
    try:
        with requests.get(url, stream=True, timeout=15) as r:
            r.raise_for_status()
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        if bot and chat_id:
                            try:
                                bot.send_chat_action(chat_id, 'upload_document')
                            except Exception:
                                pass
        return True
    except Exception as e:
        print(f"[!] Direct download failed: {e}")
        return False

def download_thumbnail(url, chat_id, index):
    """Download thumbnail and return file path for media group"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Create temp file for thumbnail
        temp_dir = f"temp_thumbnails/{chat_id}"
        os.makedirs(temp_dir, exist_ok=True)
        file_path = f"{temp_dir}/thumb_{index}.jpg"
        
        with open(file_path, 'wb') as f:
            f.write(response.content)
        
        return file_path
    except Exception as e:
        print(f"[!] Thumbnail download failed: {e}")
        return None

def fallback_ytdlp(link, filename, audio=False):
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        # Use better quality settings
        if audio:
            format_str = 'bestaudio[ext=m4a]/bestaudio'
        else:
            # Get 360p with audio, fallback to best available with audio
            format_str = '(best[height<=360][acodec!=none]/best[acodec!=none]/best)[ext=mp4]'
        
        cmd = [
            "yt-dlp",
            "-f", format_str,
            "-o", filename,
            link
        ]
        subprocess.run(cmd, check=True)
        return True
    except Exception as e:
        print(f"[!] yt-dlp fallback failed: {e}")
        return False

def cleanup_thumbnails(chat_id):
    """Clean up downloaded thumbnails for a chat"""
    try:
        temp_dir = f"temp_thumbnails/{chat_id}"
        if os.path.exists(temp_dir):
            for file in os.listdir(temp_dir):
                os.remove(os.path.join(temp_dir, file))
            os.rmdir(temp_dir)
    except Exception as e:
        print(f"[!] Cleanup failed: {e}")

def register(bot: TeleBot, custom_command_handler, command_prefixes_list):

    # Define the regex pattern for sanitizing filenames outside the f-string
    FILENAME_SANITIZE_PATTERN = r'[\\/:*?"<>|]'

    @custom_command_handler("yt")
    def yt_command(message: Message):
        # Clean up any existing thumbnails for this user before new search
        cleanup_thumbnails(message.chat.id)
        if message.chat.id in user_thumbnail_files:
            del user_thumbnail_files[message.chat.id]
            
        if not message.text:
            bot.reply_to(message, f"দয়া করে ইউটিউব সার্চ করার জন্য কিছু লিখুন।\nUsage: `{command_prefixes_list[0]}yt <search query>` অথবা `{command_prefixes_list[1]}yt <YouTube link>`", parse_mode="Markdown")
            return
        
        command_text_full = message.text.split(" ", 1)[0].lower()
        actual_command_len = 0
        for prefix in command_prefixes_list:
            if command_text_full.startswith(f"{prefix}yt"):
                actual_command_len = len(f"{prefix}yt")
                break

        query_raw = message.text[actual_command_len:].strip()

        if not query_raw:
            bot.reply_to(message, f"দয়া করে ইউটিউব সার্চ করার জন্য কিছু লিখুন।\nUsage: `{command_prefixes_list[0]}yt <search query>` অথবা `{command_prefixes_list[1]}yt <YouTube link>`", parse_mode="Markdown")
            return

        query = query_raw

        if "youtu" in query:
            try:
                res = requests.get(DOWNLOAD_API + query)
                res.raise_for_status()
                data = res.json()

                if not data.get("success") or not data.get("title"):
                    bot.reply_to(message, "❌ ভিডিও ডেটা আনতে সমস্যা হয়েছে।")
                    return

                title = re.sub(FILENAME_SANITIZE_PATTERN, '', data["title"])
                thumb = data.get("thumbnail")
                duration = data.get("duration", "Unknown")
                caption = f"🕒 {duration}\n{title}"

                user_search_results[message.chat.id] = [{
                    "title": title,
                    "imageUrl": thumb,
                    "duration": duration,
                    "link": query
                }]

                markup = InlineKeyboardMarkup()
                markup.add(
                    InlineKeyboardButton("🎵 অডিও", callback_data=f"download_{0}_audio"),
                    InlineKeyboardButton("🎬 ভিডিও", callback_data=f"download_{0}_video")
                )

                sent_msg = bot.send_photo(message.chat.id, photo=thumb, caption=caption, reply_markup=markup)
                user_sent_messages[message.chat.id] = [sent_msg.message_id]

            except Exception as e:
                print(f"[YT LINK ERROR] {e}")
                bot.reply_to(message, "❌ ভিডিও প্রসেস করতে সমস্যা হয়েছে।")
            return

        try:
            resp = requests.get(SEARCH_API + query, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            if "result" not in data or not data["result"]:
                bot.reply_to(message, "❌ কোনো রেজাল্ট পাওয়া যায়নি।")
                return

            results = data["result"][:10]
            user_search_results[message.chat.id] = results

            # Send initial message
            wait_msg = bot.reply_to(message, "📥 সার্চ রেজাল্ট প্রস্তুত করা হচ্ছে... অপেক্ষা করুন")

            # Download all thumbnails
            media_group = []
            downloaded_thumbs = []
            file_handles = []
            
            try:
                for i, video in enumerate(results):
                    thumb_url = video.get("imageUrl")
                    if thumb_url:
                        thumb_path = download_thumbnail(thumb_url, message.chat.id, i)
                        if thumb_path:
                            downloaded_thumbs.append(thumb_path)
                            
                            title = re.sub(FILENAME_SANITIZE_PATTERN, '', video["title"])
                            duration = video.get("duration", "Unknown")
                            caption = f"[{i+1}] 🕒 {duration}\n🎵 {title}"
                            
                            # Add numbered captions to each thumbnail as requested
                            # Keep file handles open until after sending media group
                            file_handle = open(thumb_path, 'rb')
                            file_handles.append(file_handle)
                            media_group.append(InputMediaPhoto(file_handle, caption=caption))

                if media_group:
                    # Send media group with thumbnails
                    bot.send_media_group(message.chat.id, media_group)
                    
                    # Close file handles after successful send
                    for handle in file_handles:
                        handle.close()
                    file_handles = []
                
                    # Create numbered buttons
                    markup = InlineKeyboardMarkup(row_width=5)
                    buttons = [InlineKeyboardButton(str(i+1), callback_data=f"select_{i}") for i in range(len(results))]
                    markup.add(*buttons)
                    
                    # Send description with all video info
                    desc_text = "🔍 সার্চ রেজাল্ট - নম্বর সিলেক্ট করুন:\n\n"
                    for i, video in enumerate(results):
                        title = re.sub(FILENAME_SANITIZE_PATTERN, '', video["title"])
                        duration = video.get("duration", "Unknown")
                        desc_text += f"[{i+1}] 🕒 {duration} | 🎵 {title}\n"
                    
                    bot.send_message(message.chat.id, desc_text, reply_markup=markup)
                    
                    # Store thumbnail paths for cleanup
                    user_thumbnail_files[message.chat.id] = downloaded_thumbs
                    
                    # Delete wait message
                    bot.delete_message(message.chat.id, wait_msg.message_id)
                else:
                    bot.edit_message_text("❌ থাম্বনেইল ডাউনলোড করতে সমস্যা হয়েছে।", chat_id=message.chat.id, message_id=wait_msg.message_id)
            finally:
                # Ensure file handles are closed even on error
                for handle in file_handles:
                    try:
                        handle.close()
                    except:
                        pass

        except Exception as e:
            print(f"[SEARCH ERROR] {e}")
            bot.reply_to(message, "❌ সার্চ করতে সমস্যা হয়েছে।")
            # Clean up any partial downloads on error
            cleanup_thumbnails(message.chat.id)


    @bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("select_"))
    def handle_select(call: CallbackQuery):
        if not call.data:
            bot.answer_callback_query(call.id, "Invalid request")
            return
        
        idx = int(call.data.split("_")[1])
        chat_id = call.message.chat.id

        if chat_id not in user_search_results:
            bot.answer_callback_query(call.id, "সেশন শেষ হয়ে গেছে। দয়া করে আবার সার্চ করুন।")
            return
        
        if idx >= len(user_search_results[chat_id]):
            bot.answer_callback_query(call.id, "Invalid selection")
            return

        video = user_search_results[chat_id][idx]
        title = re.sub(FILENAME_SANITIZE_PATTERN, '', video["title"])
        duration = video.get("duration", "Unknown")
        thumb_url = video.get("imageUrl")
        link = video["link"]

        caption = f"🕒 {duration}\n🎵 {title}\n\n📹 কোয়ালিটি সিলেক্ট করুন:"
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("🎵 অডিও (সেরা কোয়ালিটি)", callback_data=f"download_{idx}_audio"),
            InlineKeyboardButton("🎬 ভিডিও (360p)", callback_data=f"download_{idx}_video")
        )

        # Use existing thumbnail if available, otherwise use URL
        if chat_id in user_thumbnail_files and idx < len(user_thumbnail_files[chat_id]):
            thumb_path = user_thumbnail_files[chat_id][idx]
            if os.path.exists(thumb_path):
                with open(thumb_path, 'rb') as photo:
                    sent_msg = bot.send_photo(chat_id, photo=photo, caption=caption, reply_markup=markup)
            else:
                sent_msg = bot.send_photo(chat_id, photo=thumb_url, caption=caption, reply_markup=markup)
        else:
            sent_msg = bot.send_photo(chat_id, photo=thumb_url, caption=caption, reply_markup=markup)

        if chat_id not in user_sent_messages:
            user_sent_messages[chat_id] = []
        user_sent_messages[chat_id].append(sent_msg.message_id)

        bot.answer_callback_query(call.id, f"✅ [{idx+1}] নির্বাচিত")

    def process_download(bot, chat_id, idx, choice):
        # Initialize variables to prevent unbound variable errors
        wait_msg = None
        filename = None
        title = "Downloaded File"
        
        try:
            wait_msg = bot.send_message(chat_id, f"📥 ডাউনলোড হচ্ছে... অপেক্ষা করুন")

            video = user_search_results.get(chat_id, [])[idx]
            link = video["link"]

            res = requests.get(DOWNLOAD_API + link, timeout=15)
            res.raise_for_status()
            ddata = res.json()

            if ddata.get("success"):
                medias = ddata.get("medias", [])
                media_url = None

                if choice == "audio":
                    # Find best audio quality by bitrate or filesize
                    best_audio = None
                    for media in medias:
                        if media.get("type") == "audio":
                            if best_audio is None:
                                best_audio = media
                            else:
                                # Compare by bitrate first, then filesize
                                current_bitrate = media.get("abr", 0) or media.get("bitrate", 0)
                                best_bitrate = best_audio.get("abr", 0) or best_audio.get("bitrate", 0)
                                
                                if current_bitrate > best_bitrate:
                                    best_audio = media
                                elif current_bitrate == best_bitrate:
                                    # If same bitrate, compare by filesize
                                    current_size = media.get("filesize", 0)
                                    best_size = best_audio.get("filesize", 0)
                                    if current_size > best_size:
                                        best_audio = media
                    
                    if best_audio:
                        media_url = best_audio.get("url")
                else:
                    # Find 360p video with audio, fallback to any video with audio
                    for media in medias:
                        if (
                            media.get("type") == "video"
                            and media.get("has_audio") == True
                            and media.get("extension") == "mp4"
                            and "360" in str(media.get("quality", ""))
                        ):
                            media_url = media.get("url")
                            break
                    
                    if not media_url:
                        # Fallback to any video with audio
                        for media in medias:
                            if media.get("type") == "video" and media.get("has_audio") == True:
                                media_url = media.get("url")
                                break

                if media_url:
                    title = "Downloaded File"
                    try:
                        title = ddata.get("title", "Downloaded File")
                    except:
                        pass

                    filename = f"downloads/{re.sub(FILENAME_SANITIZE_PATTERN, '', title)}.mp4" if choice == "video" else f"downloads/{re.sub(FILENAME_SANITIZE_PATTERN, '', title)}.m4a"

                    success = download_file(media_url, filename, bot, chat_id)
                    if not success:
                        raise Exception("Direct download failed")
                else:
                    raise Exception("No valid media URL found")
            else:
                raise Exception("API failed")

            try:
                bot.send_message(chat_id, f"✅ সফলভাবে ডাউনলোড হয়েছে!")
                with open(filename, "rb") as f:
                    if choice == "audio":
                        bot.send_audio(chat_id, f, caption=f"🎵 {title}")
                    else:
                        bot.send_video(chat_id, f, caption=f"🎬 {title} (360p)")
                bot.delete_message(chat_id, wait_msg.message_id)
                
                # Clean up thumbnails after successful download
                cleanup_thumbnails(chat_id)
                if chat_id in user_thumbnail_files:
                    del user_thumbnail_files[chat_id]
            except Exception as e:
                bot.send_message(chat_id, f"❌ ফাইল পাঠাতে সমস্যা হয়েছে:\n{str(e)}")
            finally:
                if filename and os.path.exists(filename):
                    os.remove(filename)

        except Exception as e:
            print(f"[x] Direct method failed: {e}")
            if wait_msg:
                try:
                    bot.edit_message_text(f"❌ ডাউনলোড করতে সমস্যা হয়েছে: {str(e)}\nবিকল্প পদ্ধতি ব্যবহার করা হচ্ছে...", chat_id=chat_id, message_id=wait_msg.message_id)
                except:
                    bot.send_message(chat_id, f"❌ ডাউনলোড করতে সমস্যা হয়েছে: {str(e)}\nবিকল্প পদ্ধতি ব্যবহার করা হচ্ছে...")

            try:
                video = user_search_results.get(chat_id, [])[idx]
                link = video["link"]
                title = video.get("title", "Downloaded File")
                filename = f"downloads/{re.sub(FILENAME_SANITIZE_PATTERN, '', title)}.mp4" if choice == "video" else f"downloads/{re.sub(FILENAME_SANITIZE_PATTERN, '', title)}.m4a"
                fallback_success = fallback_ytdlp(link, filename, audio=(choice == "audio"))
                if not fallback_success:
                    bot.send_message(chat_id, f"❌ বিকল্প পদ্ধতিতেও ডাউনলোড ব্যর্থ হয়েছে।")
                    if filename and os.path.exists(filename): 
                        os.remove(filename)
                    return

                with open(filename, "rb") as f:
                    if choice == "audio":
                        bot.send_audio(chat_id, f, caption=f"🎵 {title} (Best Quality)")
                    else:
                        bot.send_video(chat_id, f, caption=f"🎬 {title} (360p)")
                if wait_msg:
                    bot.delete_message(chat_id, wait_msg.message_id)
                
                # Clean up thumbnails after successful fallback download
                cleanup_thumbnails(chat_id)
                if chat_id in user_thumbnail_files:
                    del user_thumbnail_files[chat_id]
            except Exception as e:
                bot.send_message(chat_id, f"❌ বিকল্প পদ্ধতিতে ফাইল পাঠাতে সমস্যা হয়েছে:\n{str(e)}")
            finally:
                if filename and os.path.exists(filename):
                    os.remove(filename)


    @bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("download_"))
    def handle_download(call: CallbackQuery):
        if not call.data:
            bot.answer_callback_query(call.id, "Invalid request")
            return
        
        parts = call.data.split("_")
        idx_or_link = parts[1]
        choice = parts[2]
        chat_id = call.message.chat.id

        if chat_id not in user_search_results:
            bot.answer_callback_query(call.id, "সেশন শেষ হয়ে গেছে। দয়া করে আবার সার্চ করুন।")
            return

        try:
            idx = int(idx_or_link)
            if idx >= len(user_search_results[chat_id]):
                bot.answer_callback_query(call.id, "Invalid selection")
                return
                
            # Start download in separate thread
            threading.Thread(target=process_download, args=(bot, chat_id, idx, choice)).start()
        except (ValueError, IndexError):
            bot.answer_callback_query(call.id, "Invalid selection")
            return

        # Removed duplicate answer_callback_query call as per architect feedback
