def register(bot, custom_command_handler, command_prefixes_list): 
    @custom_command_handler("reveal")
    @custom_command_handler("help")
    def show_help(message):
        user = message.from_user
        username = f"@{user.username}" if user.username else user.first_name

        help_text = (
            "🛠 <b>Available Commands For Our All Services:</b>\n\n"
            "<code>/arise</code> or <code>.arise</code> — Start the bot\n\n"
            "<code>/gen</code> or <code>.gen</code> — Generate random cards with BIN info\n\n"
            "<code>/chk</code> or <code>.chk</code> — Check a single card's status\n\n"
            "<code>/mas</code> or <code>.mas</code> — Check all generated cards at once (reply to a list)\n\n"
            "<code>/fake</code> or <code>.fake</code> — Get fake address\n\n"
            "<code>/country</code> or <code>.country</code> — Check available countries\n\n"
            "<code>/imagine</code> or <code>.imagine</code> — Generate AI images\n\n"
            "<code>/bgremove</code> or <code>.bgremove</code> — Remove image background\n\n"
            "<code>/download</code> or <code>.download</code> — Download videos from YT, FB & Insta\n\n"
            "<code>/gemini</code> or <code>.gemini</code> — Talk to Gemini\n\n"
            "<code>/gpt</code> or <code>.gpt</code> — Talk to GPT\n\n"
            "<code>/say</code> or <code>.say</code> — Text to speech\n\n"
            "<code>/spam</code> or <code>.spam</code> — spam text or imprase ut gf using <code>/spmtxt i love u 1000</code>\n\n"
            "<code>/translate</code> or <code>.translate</code> — Translate texts\n\n"
            "<code>/info</code> or <code>.info</code> — Get Telegram user/bot/group/channel info\n\n"
            "<code>/iban</code> or <code>.iban</code> — generate Iban using 1. germeny - de 2. united kingdom - gb 3. netherlands - nl \n\n"
            "<code>/reveal</code> or <code>.reveal</code> — Show all the commands\n\n"

            "🔸 <b>বিশেষ দ্রষ্টব্য:</b> আপনি !, #, , অথবা অন্য যেকোনো চিহ্ন দিয়েও কমান্ড চালাতে পারবেন।\n"
            f"\n👤 <i>Revealed by:</i> {username}"
        )

        bot.reply_to(message, help_text, parse_mode="HTML")
