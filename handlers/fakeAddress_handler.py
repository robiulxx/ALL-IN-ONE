import requests
from telebot.types import Message
from fakexyz import FakeXYZ

# Initialize FakeXYZ outside handlers for efficiency
xyz = FakeXYZ()

def register(bot, custom_command_handler, command_prefixes_list):

    @custom_command_handler("fake")
    def handle_fake(message: Message):
        command_text = message.text.split(" ", 1)[0].lower()
        actual_command_len = 0
        for prefix in command_prefixes_list:
            if command_text.startswith(f"{prefix}fake"):
                actual_command_len = len(f"{prefix}fake")
                break

        user_input_raw = message.text[actual_command_len:].strip()
        args = user_input_raw.split(" ", 1)

        if not user_input_raw:
            bot.reply_to(message, f"❌ Country name or code missing.\n\n উদাহরণ:\n`{command_prefixes_list[0]}fake US`\n`{command_prefixes_list[1]}fake bangladesh`\n`{command_prefixes_list[2]}fake kzt`", parse_mode="HTML")
            return

        user_input = user_input_raw.strip()

        try:
            # Let fakexyz handle country resolution and data fetching
            address = xyz.get_random_address(country=user_input)
            username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name

            avatar_url = address.get('avatar_url')
            if avatar_url:
                try:
                    # Download the image content
                    response = requests.get(avatar_url)
                    if response.status_code == 200:
                        # Send the photo from content
                        bot.send_photo(message.chat.id, response.content)
                    else:
                        print(f"Failed to download avatar from {avatar_url}. Status: {response.status_code}")
                except Exception as e:
                    print(f"Could not send avatar for {address.get('country_code', '')}. Error: {e}")

            msg = (
                f"<b>{address.get('country_flag', '')} Address for {address.get('country', 'Unknown')}</b> (<code>{address.get('country_code', '').upper()}</code>)\n"
                f"•{'━'*10}•\n"
                f"𝗡𝗮𝗺𝗲: <code>{address.get('name', 'N/A')}</code>\n"
                f"𝗚𝗲𝗻𝗱𝗲𝗿: <code>{address.get('gender', 'N/A')}</code>\n"
                f"𝗣𝗵𝗼𝗻𝗲: <code>{address.get('phone_number', 'N/A')}</code>\n"
                f"•{'━'*5} 𝗔𝗱𝗱𝗿𝗲𝘀𝘀 {'━'*5}•\n"
                f"𝗦𝘁𝗿𝗲𝗲𝘁: <code>{address.get('street_name', 'N/A')}</code>\n"
                f"𝗕𝘂𝗶𝗹𝗱𝗶𝗻𝗴: <code>{address.get('building_number', 'N/A')}</code>\n"
                f"𝗖𝗶𝘁𝘆: <code>{address.get('city', 'N/A')}</code>\n"
                f"𝗦𝘁𝗮𝘁𝗲: <code>{address.get('state', 'N/A')}</code>\n"
                f"𝗣𝗼𝘀𝘁𝗮𝗹 𝗖𝗼𝗱𝗲: <code>{address.get('postal_code', 'N/A')}</code>\n"
                f"𝗖𝗼𝘂𝗻𝘁𝗿𝘆: <code>{address.get('country', 'N/A')}</code>\n"
                f"•{'━'*5} 𝗔𝗱𝗱𝗶𝘁𝗶𝗼𝗻𝗮𝗹 𝗜𝗻𝗳𝗼 {'━'*5}•\n"
                f"𝗖𝘂𝗿𝗿𝗲𝗻𝗰𝘆: <code>{address.get('currency', 'N/A')}</code>\n"
                f"𝗧𝗶𝗺𝗲𝘇𝗼𝗻𝗲: <code>{address.get('time_zone', 'N/A')}</code> ({address.get('description', 'N/A')})\n"
                f"•{'━'*10}•\n"
                f"👤 𝗥𝗲𝗤𝘂𝗲𝘀𝘁 𝗯𝘆: {username}  |  𝗝𝗼𝗶𝗻: @rszone24"
            )
            bot.send_message(message.chat.id, msg, parse_mode="HTML")

        except ValueError as e: # Catch ValueError from fakexyz for country not found/suggestion
            bot.send_message(message.chat.id, f"❌ {str(e)}", parse_mode="HTML")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ An unexpected error occurred: {str(e)}")

    @custom_command_handler("country")
    def handle_countries(message: Message):
        try:
            # Get all country metadata by iterating over internal country codes
            countries_meta = [xyz.data[code]['meta'] for code in xyz.countries]

            if not countries_meta:
                bot.send_message(message.chat.id, "⚠️ No countries available at the moment.")
                return

            # Sort alphabetically by full country name
            countries_sorted = sorted(countries_meta, key=lambda x: x["country"])

            country_lines = [
                f"• {c.get('country_flag', '')} {c['country']} (<code>{c['country_code'].upper()}</code>)"
                for c in countries_sorted
            ]

            msg = (
                f"<b>🌐 Supported Countries (Total: {len(countries_sorted)})</b>\n"
                f"{'━'*34}\n"
                f"{chr(10).join(country_lines)}\n"
                f"{'━'*34}\n"
                "✅ You can now use full country names (e.g., 'Bangladesh') or country codes (e.g., 'BD').\n"
                f"উদাহরণ: <code>{command_prefixes_list[0]}fake US</code> বা <code>{command_prefixes_list[1]}fake bangladesh</code>"
            )

            bot.send_message(message.chat.id, msg, parse_mode="HTML")

        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Failed to load country list.\nError: {str(e)}")
