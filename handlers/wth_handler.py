import os
import re
import requests
import pytz
import pycountry
from telebot import TeleBot
from telebot.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from telebot.apihelper import ApiTelegramException

executor = ThreadPoolExecutor()

def get_timezone_from_coordinates(lat, lon):
    try:
        from timezonefinder import TimezoneFinder
        tf = TimezoneFinder()
        timezone_str = tf.timezone_at(lat=lat, lng=lon)
        if timezone_str:
            return pytz.timezone(timezone_str)
    except Exception:
        pass
    timezone_mapping = {
        'BD': 'Asia/Dhaka', 'IN': 'Asia/Kolkata', 'PK': 'Asia/Karachi',
        'US': 'America/New_York', 'GB': 'Europe/London', 'FR': 'Europe/Paris',
        'DE': 'Europe/Berlin', 'JP': 'Asia/Tokyo', 'CN': 'Asia/Shanghai',
        'AU': 'Australia/Sydney', 'CA': 'America/Toronto', 'BR': 'America/Sao_Paulo',
        'RU': 'Europe/Moscow', 'AE': 'Asia/Dubai', 'SA': 'Asia/Riyadh'
    }
    return pytz.timezone(timezone_mapping.get('BD', 'UTC'))

def get_country_name(country_code):
    try:
        country = pycountry.countries.get(alpha_2=country_code)
        return country.name if country else country_code
    except Exception:
        return country_code

def create_weather_image(weather_data, output_path="weather_output.png"):
    img_width, img_height = 1200, 600
    background_color = (30, 39, 50)
    img = Image.new("RGB", (img_width, img_height), color=background_color)
    draw = ImageDraw.Draw(img)

    try:
        timezone = get_timezone_from_coordinates(weather_data["lat"], weather_data["lon"])
        local_time = datetime.now(timezone)
        time_text = local_time.strftime("%I:%M %p")
    except Exception:
        time_text = datetime.now().strftime("%I:%M %p")

    current = weather_data["current"]
    temp_text = f"{current['temp']}°C"
    condition_text = current["weather"]
    realfeel_text = f"Real Feel {current['feels_like']}°C"
    country_name = get_country_name(weather_data['country_code'])
    location_text = f"{weather_data['city']}, {country_name}"

    white = (255, 255, 255)
    light_gray = (200, 200, 200)

    # Use default font to avoid external font loading errors
    # I have increased the font sizes significantly for better visibility
    font_extra_large = ImageFont.load_default(size=120)
    font_large = ImageFont.load_default(size=50)
    font_medium = ImageFont.load_default(size=35)
    font_small = ImageFont.load_default(size=30)

    # Left aligned content
    left_margin = 60
    current_y = 50
    draw.text((left_margin, current_y), "Current Weather", font=font_small, fill=white)

    temp_y = 230
    draw.text((left_margin + 100, temp_y), temp_text, font=font_extra_large, fill=white)

    condition_y = temp_y + 130
    draw.text((left_margin + 100, condition_y), condition_text, font=font_large, fill=light_gray)

    realfeel_y = condition_y + 60
    draw.text((left_margin + 100, realfeel_y), realfeel_text, font=font_medium, fill=light_gray)

    location_y = 540
    draw.text((left_margin, location_y), location_text, font=font_large, fill=white)

    # Right aligned content
    right_margin = img_width - 60
    time_y = 50
    draw.text((right_margin, time_y), time_text, font=font_small, fill=light_gray, anchor="ra")

    # Simple weather icon
    draw.text((left_margin, temp_y + 10), "T", font=font_large, fill=white)

    img.save(output_path)
    return output_path

def get_weather_data(city):
    try:
        geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
        requests.get(geocode_url).raise_for_status()
        geocode_data = requests.get(geocode_url).json()
        if not geocode_data or "results" not in geocode_data or not geocode_data["results"]:
            return None
        result = geocode_data["results"][0]
        lat, lon = result["latitude"], result["longitude"]
        country_code = result.get("country_code", "").upper()
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&"
            f"current=temperature_2m,relative_humidity_2m,apparent_temperature,weathercode,"
            f"wind_speed_10m,wind_direction_10m&"
            f"hourly=temperature_2m,apparent_temperature,relative_humidity_2m,weathercode,"
            f"precipitation_probability&"
            f"daily=temperature_2m_max,temperature_2m_min,sunrise,sunset,weathercode&"
            f"timezone=auto"
        )
        aqi_url = (
            f"https://air-quality-api.open-meteo.com/v1/air-quality?"
            f"latitude={lat}&longitude={lon}&"
            f"hourly=pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,ozone&"
            f"timezone=auto"
        )
        requests.get(weather_url).raise_for_status()
        requests.get(aqi_url).raise_for_status()
        weather_data = requests.get(weather_url).json()
        aqi_data = requests.get(aqi_url).json()
        if not weather_data or not aqi_data:
            return None
        current = weather_data["current"]
        hourly = weather_data["hourly"]
        daily = weather_data["daily"]
        aqi = aqi_data["hourly"]
        weather_code = {
            0: "Clear", 1: "Scattered Clouds", 2: "Scattered Clouds", 3: "Overcast Clouds",
            45: "Fog", 48: "Haze", 51: "Light Drizzle", 53: "Drizzle",
            55: "Heavy Drizzle", 61: "Light Rain", 63: "Moderate Rain", 65: "Heavy Rain",
            66: "Freezing Rain", 67: "Heavy Freezing Rain", 71: "Light Snow",
            73: "Snow", 75: "Heavy Snow", 77: "Snow Grains", 80: "Showers",
            81: "Heavy Showers", 82: "Violent Showers", 95: "Thunderstorm",
            96: "Thunderstorm", 99: "Heavy Thunderstorm"
        }
        current_weather = weather_code.get(current["weathercode"], "Unknown")
        hourly_data = [
            (time.split("T")[1][:5], temp, weather_code.get(code, "Unknown"))
            for time, temp, code in zip(hourly["time"][:12], hourly["temperature_2m"][:12], hourly["weathercode"][:12])
        ]
        hourly_strings = []
        for time, temp, weather in hourly_data:
            hour = int(time[:2])
            time_format = f"{hour % 12 or 12} {'AM' if hour < 12 else 'PM'}"
            hourly_strings.append(f"{time_format}: {temp}°C {weather}")
        current_date = datetime.now()
        daily_strings = []
        for i in range(7):
            day_date = (current_date + timedelta(days=i)).strftime('%a, %b %d')
            min_temp = daily["temperature_2m_min"][i]
            max_temp = daily["temperature_2m_max"][i]
            weather = weather_code.get(daily["weathercode"][i], "Unknown")
            daily_strings.append(f"{day_date}: {min_temp} / {max_temp}°C {weather}")
        aqi_level = "ভালো" if aqi["pm2_5"][0] <= 12 else "মাঝারি" if aqi["pm2_5"][0] <= 35 else "মোটামুটি" if aqi["pm2_5"][0] <= 55 else "খারাপ"
        try:
            timezone = get_timezone_from_coordinates(lat, lon)
            local_time = datetime.now(timezone)
            current_time = local_time.strftime("%I:%M %p")
        except Exception:
            current_time = datetime.now().strftime("%I:%M %p")
        return {
            "current": {
                "temp": current["temperature_2m"],
                "feels_like": current["apparent_temperature"],
                "humidity": current["relative_humidity_2m"],
                "wind_speed": current["wind_speed_10m"],
                "wind_dir": current["wind_direction_10m"],
                "weather": current_weather,
                "sunrise": daily["sunrise"][0].split("T")[1][:5] + " AM",
                "sunset": daily["sunset"][0].split("T")[1][:5] + " PM",
                "time": current_time
            },
            "hourly": hourly_strings,
            "daily": daily_strings,
            "aqi": {
                "pm25": aqi["pm2_5"][0],
                "pm10": aqi["pm10"][0],
                "co": aqi["carbon_monoxide"][0],
                "no2": aqi["nitrogen_dioxide"][0],
                "o3": aqi["ozone"][0],
                "level": aqi_level
            },
            "city": city.capitalize(),
            "country": get_country_name(country_code),
            "country_code": country_code,
            "lat": lat,
            "lon": lon
        }
    except Exception as e:
        print(f"Error fetching weather data: {e}")
        return None

def register(bot: TeleBot, custom_command_handler, command_prefixes_list):
    @custom_command_handler("wth")
    def handle_weather(message: Message):
        parts = message.text.split()
        if len(parts) < 2 or not parts:
            bot.reply_to(message, "**শহরের নাম দিন। উদাহরণ: `/wth Faridpur`**", parse_mode="Markdown")
            return
        city = parts[1].lower()
        loading_msg = bot.reply_to(message, "**আবহাওয়ার ফলাফল প্রসেস হচ্ছে...**", parse_mode="Markdown")
        try:
            data = get_weather_data(city)
            if not data:
                bot.edit_message_text(f"🔍 `{city.capitalize()}` এর জন্য আবহাওয়ার তথ্য পাওয়া যায়নি। শহরের নাম চেক করে আবার চেষ্টা করুন।", message.chat.id, loading_msg.message_id, parse_mode="Markdown")
                return
            image_path = f"weather_{city}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            executor.submit(create_weather_image, data, image_path).result()
            user_fullname = f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
            keyboard = [
                [InlineKeyboardButton("🕒 ১২ ঘণ্টার পূর্বাভাস", callback_data=f"12h_{message.from_user.id}_{city}"), InlineKeyboardButton("📅 ৭ দিনের পূর্বাভাস", callback_data=f"7d_{message.from_user.id}_{city}")],
                [InlineKeyboardButton("🌬 বায়ু মান", callback_data=f"aqi_{message.from_user.id}_{city}"), InlineKeyboardButton("⚠️ আবহাওয়া সতর্কতা", callback_data=f"alert_{message.from_user.id}_{city}")],
                [InlineKeyboardButton("🔄 রিফ্রেশ", callback_data=f"refresh_{message.from_user.id}_{city}"), InlineKeyboardButton("🗺 ম্যাপ ও রাডার", callback_data=f"map_{message.from_user.id}_{city}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            caption = (
                f"**🔍 `{data['city']}` এর আবহাওয়া**\n"
                f"**━━━━━━━━━━━━━━━━━**\n"
                f"**🌍 অবস্থান:** {data['city']}, {data['country']}\n"
                f"**🕒 সময়:** {data['current']['time']}\n"
                f"**🌡 তাপমাত্রা:** {data['current']['temp']}°C\n"
                f"**🌡 অনুভূত:** {data['current']['feels_like']}°C\n"
                f"**💧 আর্দ্রতা:** {data['current']['humidity']}%\n"
                f"**🌬 বাতাস:** {data['current']['wind_speed']} m/s from {data['current']['wind_dir']}°\n"
                f"**🌅 সূর্যোদয়:** {data['current']['sunrise']}\n"
                f"**🌆 সূর্যাস্ত:** {data['current']['sunset']}\n"
                f"**🌤 আবহাওয়া:** {data['current']['weather']}\n"
                f"**━━━━━━━━━━━━━━━━━**\n"
                f"👁 অনুরোধ করেছেন: {user_fullname} (ID: {message.from_user.id})\n"
                f"👁 নেভিগেট করতে নিচের বাটনগুলো ব্যবহার করুন ✅"
            )
            with open(image_path, "rb") as image_file:
                bot.send_photo(
                    chat_id=message.chat.id,
                    photo=image_file,
                    caption=caption,
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
            os.remove(image_path)
            bot.delete_message(message.chat.id, loading_msg.message_id)
        except Exception as e:
            bot.edit_message_text(f"❌ ডাউনলোডে সমস্যা হয়েছে:\n`{str(e)}`", message.chat.id, loading_msg.message_id, parse_mode="Markdown")

    @bot.callback_query_handler(func=lambda call: call.data.startswith(('12h_', '7d_', 'aqi_', 'alert_', 'map_', 'refresh_', 'wth_menu_')))
    def callback_button(call: CallbackQuery):
        match = re.match(r"^(12h|7d|aqi|alert|map|refresh|wth_menu)_(\d+)_(.+)$", call.data)
        if not match:
            bot.answer_callback_query(call.id, "Error: Invalid button data.", show_alert=True)
            return
        action, original_user_id, city = match.groups()
        original_user_id = int(original_user_id)
        callback_user_id = call.from_user.id
        if callback_user_id != original_user_id:
            user_fullname = call.message.caption.split("অনুরোধ করেছেন: ")[1].split(" (ID:")[0]
            bot.answer_callback_query(
                call.id,
                f"Action Disallowed: This Button Only For {user_fullname}",
                show_alert=True
            )
            return
        bot.answer_callback_query(call.id, "Loading.....")
        data = get_weather_data(city)
        if not data:
            try:
                bot.edit_message_caption(call.message.chat.id, call.message.message_id, f"🔍 `{city.capitalize()}` এর জন্য আবহাওয়ার তথ্য পাওয়া যায়নি। আবার চেষ্টা করুন।", parse_mode="Markdown")
            except ApiTelegramException:
                bot.send_message(call.message.chat.id, f"🔍 `{city.capitalize()}` এর জন্য আবহাওয়ার তথ্য পাওয়া যায়নি। আবার চেষ্টা করুন।", parse_mode="Markdown")
            return
        user_fullname = f"{call.from_user.first_name} {call.from_user.last_name or ''}".strip()
        keyboard_back = [[InlineKeyboardButton("🔙 ফিরে যান", callback_data=f"wth_menu_{original_user_id}_{city}")]]
        keyboard_main = [
            [InlineKeyboardButton("🕒 ১২ ঘণ্টার পূর্বাভাস", callback_data=f"12h_{original_user_id}_{city}"), InlineKeyboardButton("📅 ৭ দিনের পূর্বাভাস", callback_data=f"7d_{original_user_id}_{city}")],
            [InlineKeyboardButton("🌬 বায়ু মান", callback_data=f"aqi_{original_user_id}_{city}"), InlineKeyboardButton("⚠️ আবহাওয়া সতর্কতা", callback_data=f"alert_{original_user_id}_{city}")],
            [InlineKeyboardButton("🔄 রিফ্রেশ", callback_data=f"refresh_{original_user_id}_{city}"), InlineKeyboardButton("🗺 ম্যাপ ও রাডার", callback_data=f"map_{original_user_id}_{city}")]
        ]
        reply_markup_main = InlineKeyboardMarkup(keyboard_main)
        if action == "12h":
            hourly_text = "\n".join(data['hourly'])
            message_text = (
                f"🕒 `{data['city']}` এর ১২-ঘণ্টার পূর্বাভাস\n"
                f"━━━━━━━━━━━━━━━━━\n"
                f"{hourly_text}\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"নেভিগেট করতে নিচের বাটনগুলো ব্যবহার করুন"
            )
            try:
                bot.edit_message_caption(call.message.chat.id, call.message.message_id, message_text, reply_markup=InlineKeyboardMarkup(keyboard_back), parse_mode="Markdown")
            except ApiTelegramException:
                bot.send_message(call.message.chat.id, message_text, reply_markup=InlineKeyboardMarkup(keyboard_back), parse_mode="Markdown")
        elif action == "7d":
            daily_text = "\n".join(data['daily'])
            message_text = (
                f"📅 `{data['city']}` এর ৭-দিনের পূর্বাভাস\n"
                f"━━━━━━━━━━━━━━━━━\n"
                f"{daily_text}\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"নেভিগেট করতে নিচের বাটনগুলো ব্যবহার করুন"
            )
            try:
                bot.edit_message_caption(call.message.chat.id, call.message.message_id, message_text, reply_markup=InlineKeyboardMarkup(keyboard_back), parse_mode="Markdown")
            except ApiTelegramException:
                bot.send_message(call.message.chat.id, message_text, reply_markup=InlineKeyboardMarkup(keyboard_back), parse_mode="Markdown")
        elif action == "aqi":
            aqi = data["aqi"]
            message_text = (
                f"🌬 `{data['city']}` এর বায়ু মান\n"
                f"━━━━━━━━━━━━━━━━━\n"
                f"সামগ্রিক বায়ু মান: {aqi['level']} 🟡\n"
                f"CO: {aqi['co']} µg/m³\n"
                f"NO2: {aqi['no2']} µg/m³\n"
                f"O3: {aqi['o3']} µg/m³\n"
                f"PM2.5: {aqi['pm25']} µg/m³\n"
                f"PM10: {aqi['pm10']} µg/m³\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"নেভিগেট করতে নিচের বাটনগুলো ব্যবহার করুন"
            )
            try:
                bot.edit_message_caption(call.message.chat.id, call.message.message_id, message_text, reply_markup=InlineKeyboardMarkup(keyboard_back), parse_mode="Markdown")
            except ApiTelegramException:
                bot.send_message(call.message.chat.id, message_text, reply_markup=InlineKeyboardMarkup(keyboard_back), parse_mode="Markdown")
        elif action == "alert":
            message_text = (
                f"🛡 `{data['city']}` এর আবহাওয়া সতর্কতা\n"
                f"━━━━━━━━━━━━━━━━━\n"
                f"✅ বর্তমানে কোনো সক্রিয় আবহাওয়া সতর্কতা নেই।\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"নেভিগেট করতে নিচের বাটনগুলো ব্যবহার করুন"
            )
            try:
                bot.edit_message_caption(call.message.chat.id, call.message.message_id, message_text, reply_markup=InlineKeyboardMarkup(keyboard_back), parse_mode="Markdown")
            except ApiTelegramException:
                bot.send_message(call.message.chat.id, message_text, reply_markup=InlineKeyboardMarkup(keyboard_back), parse_mode="Markdown")
        elif action == "map":
            lat, lon = data["lat"], data["lon"]
            map_links = [
                f"[🌡 তাপমাত্রা ম্যাপ](https://openweathermap.org/weathermap?basemap=map&cities=true&layer=temperature&lat={lat}&lon={lon}&zoom=8)",
                f"[☁️ মেঘের আবরণ](https://openweathermap.org/weathermap?basemap=map&cities=true&layer=clouds&lat={lat}&lon={lon}&zoom=8)",
                f"[🌧 বৃষ্টিপাত](https://openweathermap.org/weathermap?basemap=map&cities=true&layer=precipitation&lat={lat}&lon={lon}&zoom=8)",
                f"[💨 বাতাসের গতি](https://openweathermap.org/weormap?basemap=map&cities=true&layer=wind&lat={lat}&lon={lon}&zoom=8)",
                f"[🌊 চাপ](https://openweathermap.org/weathermap?basemap=map&cities=true&layer=pressure&lat={lat}&lon={lon}&zoom=8)"
            ]
            maps_text = "\n".join(map_links)
            message_text = (
                f"🗺 `{data['city']}` এর আবহাওয়া ম্যাপ\n"
                f"━━━━━━━━━━━━━━━━━\n"
                f"{maps_text}\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"নেভিগেট করতে নিচের বাটনগুলো ব্যবহার করুন"
            )
            try:
                bot.edit_message_caption(call.message.chat.id, call.message.message_id, message_text, reply_markup=InlineKeyboardMarkup(keyboard_back), parse_mode="Markdown")
            except ApiTelegramException:
                bot.send_message(call.message.chat.id, message_text, reply_markup=InlineKeyboardMarkup(keyboard_back), parse_mode="Markdown")
        elif action == "refresh":
            new_data = get_weather_data(city)
            if not new_data or (new_data and new_data["current"] == data["current"]):
                bot.answer_callback_query(call.id, "ডেটা পরিবর্তন হয়নি।", show_alert=True)
                return
            new_image_path = f"weather_{city}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            executor.submit(create_weather_image, new_data, new_image_path).result()
            caption = (
                f"**🔍 `{new_data['city']}` এর আবহাওয়া**\n"
                f"**━━━━━━━━━━━━━━━━━**\n"
                f"**🌍 অবস্থান:** {new_data['city']}, {new_data['country']}\n"
                f"**🕒 সময়:** {new_data['current']['time']}\n"
                f"**🌡 তাপমাত্রা:** {new_data['current']['temp']}°C\n"
                f"**🌡 অনুভূত:** {new_data['current']['feels_like']}°C\n"
                f"**💧 আর্দ্রতা:** {new_data['current']['humidity']}%\n"
                f"**🌬 বাতাস:** {new_data['current']['wind_speed']} m/s from {new_data['current']['wind_dir']}°\n"
                f"**🌅 সূর্যোদয়:** {new_data['current']['sunrise']}\n"
                f"**🌆 সূর্যাস্ত:** {new_data['current']['sunset']}\n"
                f"**🌤 আবহাওয়া:** {new_data['current']['weather']}\n"
                f"**━━━━━━━━━━━━━━━━━**\n"
                f"👁 অনুরোধ করেছেন: {user_fullname} (ID: {original_user_id})\n"
                f"👁 নেভিগেট করতে নিচের বাটনগুলো ব্যবহার করুন ✅"
            )
            with open(new_image_path, "rb") as image_file:
                media = InputMediaPhoto(media=image_file, caption=caption, parse_mode="Markdown")
                try:
                    bot.edit_message_media(media, call.message.chat.id, call.message.message_id, reply_markup=reply_markup_main)
                except ApiTelegramException:
                    bot.send_photo(
                        chat_id=call.message.chat.id,
                        photo=image_file,
                        caption=caption,
                        reply_markup=reply_markup_main,
                        parse_mode="Markdown"
                    )
            os.remove(new_image_path)
        elif action == "wth_menu":
            caption = (
                f"**🔍 `{data['city']}` এর আবহাওয়া**\n"
                f"**━━━━━━━━━━━━━━━━━**\n"
                f"**🌍 অবস্থান:** {data['city']}, {data['country']}\n"
                f"**🕒 সময়:** {data['current']['time']}\n"
                f"**🌡 তাপমাত্রা:** {data['current']['temp']}°C\n"
                f"**🌡 অনুভূত:** {data['current']['feels_like']}°C\n"
                f"**💧 আর্দ্রতা:** {data['current']['humidity']}%\n"
                f"**🌬 বাতাস:** {data['current']['wind_speed']} m/s from {data['current']['wind_dir']}°\n"
                f"**🌅 সূর্যোদয়:** {data['current']['sunrise']}\n"
                f"**🌆 সূর্যাস্ত:** {data['current']['sunset']}\n"
                f"**🌤 আবহাওয়া:** {data['current']['weather']}\n"
                f"**━━━━━━━━━━━━━━━━━**\n"
                f"👁 অনুরোধ করেছেন: {user_fullname} (ID: {original_user_id})"
            )
            try:
                bot.edit_message_caption(call.message.chat.id, call.message.message_id, caption, reply_markup=reply_markup_main, parse_mode="Markdown")
            except ApiTelegramException:
                bot.send_message(call.message.chat.id, caption, reply_markup=reply_markup_main, parse_mode="Markdown")
