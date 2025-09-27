import requests
import difflib
import pycountry
from telebot.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery


IBAN_GENERATE_API = "https://drlabapis.onrender.com/api/generateiban?country={code}"
IBAN_COUNTRIES_API = "https://drlabapis.onrender.com/api/iban/country"

COUNTRY_FLAGS = {
    country.alpha_2: "".join(chr(0x1F1E6 + ord(c) - ord('A')) for c in country.alpha_2)
    for country in pycountry.countries
    if hasattr(country, "alpha_2")
}

IBAN_ALIASES = {
    "united kingdom": "gb", "gb": "gb", "uk": "gb",
    "kazakhstan": "kz", "kz": "kz", "kzt": "kz",
}


def register(bot, custom_command_handler, command_prefixes_list):
    user_iban_data = {}

    @custom_command_handler("iban")
    def handle_iban(message: Message):
        command_text = message.text.split(" ", 1)[0].lower()
        actual_command_len = 0
        for prefix in command_prefixes_list:
            if command_text.startswith(f"{prefix}iban"):
                actual_command_len = len(f"{prefix}iban")
                break

        user_input_raw = message.text[actual_command_len:].strip()
        if not user_input_raw:
            bot.reply_to(message, f"❌ Country name/code missing.\n\nTry:\n{prefix}iban DE\n{prefix}iban Germany", parse_mode="HTML")
            return

        user_input = user_input_raw.split()[0].lower()

        try:
            res = requests.get(IBAN_COUNTRIES_API)
            res.raise_for_status()
            countries_data = res.json().get("available_country", {})
        except:
            bot.reply_to(message, "❌ Failed to fetch country data.")
            return

        # Mapping user input
        iban_map = {name.lower(): code.lower() for code, name in countries_data.items()}
        iban_map.update({code.lower(): code.lower() for code in countries_data})
        iban_map.update(IBAN_ALIASES)

        country_code = iban_map.get(user_input)

        # ✅ Suggest close matches if not found
        if not country_code:
            suggestion = difflib.get_close_matches(user_input, list(iban_map.keys()), n=3)
            if suggestion:
                suggestion_text = "\n".join(
                    f"🔹 <code>{iban_map[s]}</code> → {s.title()}" for s in suggestion
                )
                bot.reply_to(
                    message,
                    f"❌ Country not found or unsupported.\n\n<b>👉 কাছাকাছি মিল:</b>\n{suggestion_text}\n\n<b>📌 Try:</b> <code>{command_prefixes_list[0]}iban Germany</code>",
                    parse_mode="HTML"
                )
            else:
                bot.reply_to(message, "❌ Unsupported or invalid country.", parse_mode="HTML")
            return

        # Fetch 10 IBANs
        generated_ibans = []
        for _ in range(10):
            try:
                r = requests.get(IBAN_GENERATE_API.format(code=country_code.upper()))
                r.raise_for_status()
                generated_ibans.append(r.json())
            except:
                bot.send_message(message.chat.id, "❌ IBAN fetch failed.")
                return

        user_iban_data[message.from_user.id] = generated_ibans

        country_name = countries_data.get(country_code.upper(), country_code.upper())
        country_flag = COUNTRY_FLAGS.get(country_code.upper(), "🏳️")

        username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name

        # 🔹 Copyable IBAN list message
        msg_lines = [
            f"<b>Iban ⇾ {country_name} {country_flag}</b>",
            f"<b>Amount ⇾ {len(generated_ibans)}</b>",
            "•──────────────────────•",
            "here are 10 IBANs (each copyable):"
        ]
        msg_lines += [f"<code>{iban['iban']}</code>" for iban in generated_ibans]
        msg_lines += [
            "•──────────────────────•",
            f"<b>𝗥𝗲𝗾𝘂𝗲𝘀𝘁 𝗯𝘆:</b> {username}    |    <b>𝗝𝗼𝗶𝗻:</b> @rszoneBDx"
        ]

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⬇ Show Details", callback_data="iban_show"))

        bot.send_message(message.chat.id, "\n".join(msg_lines), parse_mode="HTML", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("iban_"))
    def handle_toggle(call: CallbackQuery):
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        msg_id = call.message.message_id

        ibans = user_iban_data.get(user_id)
        if not ibans:
            bot.answer_callback_query(call.id, "❌ Expired or missing IBAN data.")
            return

        if call.data == "iban_show":
            detail_lines = []
            for i, iban in enumerate(ibans):
                detail_lines.append(
                    f"<b>IBAN {i+1}:</b>\n"
                    f"  IBAN: <code>{iban.get('iban')}</code>\n"
                    f"  account_Code: <code>{iban.get('account_Code')}</code>\n"
                    f"  bank_code: <code>{iban.get('bank_code')}</code>\n"
                    f"  bank_name: <code>{iban.get('bank_name')}</code>\n"
                    f"  bic: <code>{iban.get('bic')}</code>\n"
                    f"  branch_code: <code>{iban.get('branch_code')}</code>\n"
                )
            full_msg = "\n".join(detail_lines)

            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("⬆ Hide Details", callback_data="iban_hide"))
            bot.edit_message_text(full_msg, chat_id, msg_id, parse_mode="HTML", reply_markup=markup)

        elif call.data == "iban_hide":
            short_msg = "🔐 <b>IBAN details hidden.</b>\n⬇️ Click below to see again."
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("⬇ Show Details", callback_data="iban_show"))
            bot.edit_message_text(short_msg, chat_id, msg_id, parse_mode="HTML", reply_markup=markup)

    
    @custom_command_handler("ibncntry")
    def handle_iban_countries(message: Message):
        try:
            res = requests.get(IBAN_COUNTRIES_API)
            res.raise_for_status()
            countries = res.json().get("available_country", {})

            if not countries:
                bot.send_message(message.chat.id, "⚠️ কোনো দেশ পাওয়া যায়নি।")
                return

            country_lines = []
            for code, name in sorted(countries.items(), key=lambda x: x[1]):
                flag = COUNTRY_FLAGS.get(code, "🏳️")
                country_lines.append(f"• {name} (<code>{code}</code>) {flag}")

            msg = (
                f"<b>🌍 Supported IBAN Countries (Total: {len(countries)})</b>\n"
                + "\n".join(country_lines) +
                "\n\n<b>📌 উদাহরণ:</b> <code>/iban Germany</code> বা <code>/iban DE</code>"
            )

            bot.send_message(message.chat.id, msg, parse_mode="HTML")

        except Exception as e:
            bot.send_message(message.chat.id, f"❌ দেশে তালিকা লোড করতে সমস্যা হয়েছে:\n{str(e)}")
