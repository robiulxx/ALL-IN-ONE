def register(bot, custom_command_handler, command_prefixes_list): 
    @custom_command_handler("start")
    @custom_command_handler("arise")
    def start_command(message):
        user = message.from_user
        username = f"@{user.username}" if user.username else user.first_name

        welcome_text = (
            f"👋 <b>Welcome {username}!</b>\n\n"
            "🛠 <b>Available Commands:</b>\n\n"

            "<code>/arise</code> or <code>.arise</code> — Start the bot\n\n"
            "<code>/gen</code> or <code>.gen</code> — Generate random cards with BIN info\n\n"
            "<code>/chk</code> or <code>.chk</code> — Check a single card's status\n\n"
            "<code>/mas</code> or <code>.mas</code> — Check all generated cards at once (reply to a list)\n\n"
            "<code>/fake</code> or <code>.fake</code> — Get fake address\n\n"
            "<code>/country</code> or <code>.country</code> — Check available countries\n\n"
            "<code>/iban</code> or <code>.iban</code> — generate Iban using 1. germeny - de 2. united kingdom - gb 3. netherlands - nl \n\n"
            "<code>/reveal</code> or <code>.reveal</code> — Show all others commands\n\n"

            "🔸 <b>বিশেষ দ্রষ্টব্য:</b> আপনি !, #, ', বা অন্য কোনো চিহ্ন দিয়েও কমান্ড চালাতে পারবেন।\n\n"
            "📢 <b>Stay With Us:</b>\n"
            "<a href='https://t.me/rszone24'>𝗝𝗼𝗶𝗻: RS ZONE</a>"
        )

        bot.send_message(message.chat.id, welcome_text, parse_mode="HTML")
