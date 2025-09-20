import aiohttp
import asyncio
import telebot
import pycountry

def register(bot: telebot.TeleBot, custom_command_handler, command_prefixes_list):
    @custom_command_handler("bin")
    def handle_bin_command(message):
        command_text = message.text.split(" ", 1)[0].lower()
        actual_command = ""
        for prefix in command_prefixes_list:
            if command_text.startswith(f"{prefix}bin"):
                actual_command = f"{prefix}bin"
                break

        if not message.text[len(actual_command):].strip():
            bot.reply_to(message, "❗ একটি BIN দিন যেমন: `/bin 426633`, `.bin 426633` অথবা `,bin 426633`", parse_mode="Markdown")
            return

        bin_number_raw = message.text[len(actual_command):].strip().split()[0]
        bin_number = ''.join(filter(str.isdigit, bin_number_raw))

        if not bin_number or len(bin_number) < 6:
            bot.reply_to(message, "❌ একটি বৈধ BIN (কমপক্ষে ৬ সংখ্যা) দিন।")
            return
            
        bot.send_chat_action(message.chat.id, "typing")

        try:
            bin_info = asyncio.run(lookup_bin(bin_number))

            if "error" in bin_info:
                bot.reply_to(message, f"❌ ত্রুটি: {bin_info['error']}")
                return

            user = message.from_user
            request_by = (
                f"@{user.username}" if user.username else
                f"{user.first_name or ''} {user.last_name or ''}".strip() if (user.first_name or user.last_name) else
                f"User ID: {user.id}"
            )

            formatted = (
                f"💳 <b>BIN:</b> <code>{bin_info.get('bin', 'N/A')}</code>\n"
                f"🌐 <b>Status:</b> <code>{bin_info.get('source', '❓ UNKNOWN')}</code>\n\n"
                f"•──────────────────────•\n"
                f"<b>Type:</b> <code>{bin_info.get('type', 'Error').upper()}</code> (<code>{bin_info.get('scheme', 'Error').upper()}</code>)\n"
                f"<b>Brand:</b> <code>{bin_info.get('tier', 'Error').upper()}</code>\n"
                f"<b>Issuer:</b> <code>{bin_info.get('bank', 'Error').upper()}</code>\n"
                f"<b>Country:</b> <code>{bin_info.get('country', 'Error').upper()}</code> {bin_info.get('flag', '🏳️')}\n"
                f"<b>Currency:</b> <code>{bin_info.get('currency', 'N/A')}</code> | <b>Code:</b> <code>{bin_info.get('country_code', 'N/A')}</code>\n"
                f"•──────────────────────•\n\n"
                f"<b>Request by:</b> {request_by}    |    <b>Join:</b> @rszone24"
            )

            bot.reply_to(message, formatted, parse_mode="HTML")

        except Exception as e:
            bot.reply_to(message, f"❌ অভ্যন্তরীণ ত্রুটি: {str(e)}")


async def lookup_bin(bin_number: str) -> dict:
    bin_to_use = ''.join(filter(str.isdigit, bin_number))[:6]
    headers = { "User-Agent": "Mozilla/5.0" }

    # 1️⃣ Vercel API
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://bin-db.vercel.app/api/bin?bin={bin_to_use}", headers=headers) as res:
                if res.status == 200:
                    data = await res.json()
                    if data and data.get("status") == "SUCCESS" and data.get("data"):
                        bin_data = data["data"][0]
                        country_code = bin_data.get("country_code", "N/A")
                        country_info = get_country_info(country_code)
                        return {
                            "bin": bin_data.get("bin"),
                            "type": bin_data.get("Type") or bin_data.get("type"),
                            "scheme": bin_data.get("brand"),
                            "tier": bin_data.get("CardTier") or bin_data.get("category"),
                            "bank": bin_data.get("issuer"),
                            "country": (bin_data.get("Country", {}).get("Name") or "N/A"),
                            "currency": country_info["currency"],
                            "country_code": country_code,
                            "flag": country_info["flag"],
                            "source": "Valid Bin ✅"
                        }
    except Exception as e:
        print(f"Vercel API fallback for {bin_to_use}: {e}")

    # 2️⃣ HandyAPI
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://data.handyapi.com/bin/{bin_to_use}",
                headers={**headers, "x-api-key": "handyapi-PUB-0YI0cklUYMv1njw6Q597r4C7KqB"}
            ) as res:
                if res.status == 200:
                    data = await res.json()
                    if data and data.get("Status") == "SUCCESS":
                        country_code = data.get("Country", {}).get("A2", "N/A")
                        country_info = get_country_info(country_code)
                        return {
                            "bin": bin_to_use,
                            "type": data.get("Type"),
                            "scheme": data.get("Scheme"),
                            "tier": data.get("CardTier"),
                            "bank": data.get("Issuer"),
                            "country": (data.get("Country", {}).get("Name") or "N/A"),
                            "currency": country_info["currency"],
                            "country_code": country_code,
                            "flag": country_info["flag"],
                            "source": "Valid Bin ✅"
                        }
    except Exception as e:
        print(f"HandyAPI fallback for {bin_to_use}: {e}")

    return {"error": "BIN তথ্য কোনো সোর্স থেকে পাওয়া যায়নি।"}


def get_country_info(country_code):
    info = {
        "flag": "🏳️",
        "currency": "N/A"
    }
    try:
        if country_code and country_code.upper() != "N/A":
            country = pycountry.countries.get(alpha_2=country_code.upper())
            if country:
                info["flag"] = country.flag
                try:
                    currency = pycountry.currencies.get(numeric=country.numeric)
                    info["currency"] = currency.alpha_3
                except:
                    pass
    except Exception as e:
        print(f"Pycountry lookup error for code {country_code}: {e}")
    return info
