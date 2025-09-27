import html
import requests
import telebot
import time

# API endpoint for B3 checks
B3_API_URL = "https://b3-checker-production.up.railway.app/check?card={cc}|{mm}|{yy}|{cvv}"

def check_card_b3(card):
    """Check a single card using the B3 API"""
    try:
        parts = card.strip().split('|')
        if len(parts) != 4:
            return "❌ Invalid card format. Use cc|mm|yy|cvv"

        cc, mm, yy, cvv = parts
        
        # New API handles 4-digit years, so no conversion needed
        
        url = B3_API_URL.format(cc=cc, mm=mm, yy=yy, cvv=cvv)
        
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if "error" in data:
            return f"❌ {data['error']}"

        status = data.get("status", "Unknown")
        response_text = data.get("response", "N/A")
        gateway = data.get("gateway", "N/A")
        time_taken = data.get("time_taken", "N/A")
        
        bin_info = data.get("bin_info", {})
        brand = bin_info.get("brand", "N/A")
        card_type = bin_info.get("type", "N/A")
        level = bin_info.get("level", "N/A")
        bank = bin_info.get("bank", "N/A")
        country = bin_info.get("country", "N/A")
        emoji = bin_info.get("emoji", "❓")
        
        # Set emojis based on status
        status_emoji = ""
        if data.get("is_approved", False):
            status = "Live"
            status_emoji = "✅"
        elif "DECLINED" in status.upper():
            status = "Dead"
            status_emoji = "❌"
        else:
            status = "Unknown"
            status_emoji = "⚠️"
        
        # Construct the output string
        output = (
            f"<b>Status:</b> {status_emoji} <code>{html.escape(status)}</code>\n"
            f"<b>Response:</b> <code>{html.escape(response_text)}</code>\n"
            f"<b>Gateway:</b> <code>{html.escape(gateway)}</code>\n"
            f"<b>Time:</b> <code>{html.escape(time_taken)}</code>\n"
            f"•━━━━━ 𝗕𝗶𝗻 𝗜𝗻𝗳𝗼 ━━━━━•\n"
            f"<b>Brand:</b> <code>{html.escape(brand)}</code>\n"
            f"<b>Type:</b> <code>{html.escape(card_type)}</code>\n"
            f"<b>Level:</b> <code>{html.escape(level)}</code>\n"
            f"<b>Bank:</b> <code>{html.escape(bank)}</code>\n"
            f"<b>Country:</b> <code>{html.escape(country)}</code> {emoji}\n"
            f"•━━━━━━━━━━━━━━━━━━•"
        )
        
        return output

    except Exception as e:
        return f"⚠️ Error checking card: {str(e)}"

def register(bot, custom_command_handler, command_prefixes_list):
    @custom_command_handler("b3")
    def handle_b3(message):
        
        command_text = message.text.split(" ", 1)[0].lower()
        
        actual_command = ""
        for prefix in command_prefixes_list:
            if command_text.startswith(f"{prefix}b3"):
                actual_command = f"{prefix}b3"
                break
        
        if len(message.text[len(actual_command):].strip().split()) < 1:
            bot.reply_to(message, "❌ Provide a card to check. Format: `cc|mm|yy|cvv`. Example: `/b3 4000123456789012|12|25|123`", parse_mode="Markdown")
            return

        card = message.text[len(actual_command):].strip().split()[0]
        
        user = message.from_user
        username = f"@{user.username}" if user.username else user.first_name

        sent_msg = bot.reply_to(message, f"🔄 Checking <code>{card}</code> with B3...", parse_mode="HTML")
        
        status = check_card_b3(card)
        
        try:
            bot.edit_message_text(
                chat_id=sent_msg.chat.id,
                message_id=sent_msg.message_id,
                text=f"<code>{card}</code>\n\n{status}\n\n👤 𝗥𝗲𝗾𝘂𝗲𝘀𝘁 𝗯𝘆: {username}  |  𝗝𝗼𝗶𝗻: @rszoneBDx",
                parse_mode="HTML"
            )
        except Exception as e:
            bot.reply_to(message, f"⚠️ Failed to edit message: {str(e)}")

    @custom_command_handler("mb3")
    def handle_mass_b3(message):
        if not message.reply_to_message:
            bot.reply_to(message, f"❌ Please reply to a message containing cards. Example: `{command_prefixes_list[0]}mb3` replied to a message with `cc|mm|yy|cvv` lines.", parse_mode="Markdown")
            return

        lines = message.reply_to_message.text.strip().split('\n')
        cards = [line.strip() for line in lines if '|' in line and line.count('|') == 3]

        if not cards:
            bot.reply_to(message, "❌ No valid cards found in the replied message.")
            return

        if len(cards) > 10:
            bot.reply_to(message, f"⚠️ Limit exceeded: You can check a maximum of 10 cards at once. You provided {len(cards)}.")
            return

        user = message.from_user
        username = f"@{user.username}" if user.username else user.first_name

        sent_msg = bot.reply_to(message, f"🔄 Checking {len(cards)} cards with B3...", parse_mode="HTML")

        results = []
        
        for i, card in enumerate(cards):
            status = check_card_b3(card)
            results.append(f"<code>{card}</code>\n{status}")
            
            # Update message text after each card check
            current_progress = f"🔄 Checking card {i+1} of {len(cards)}...\n"
            reply_text = current_progress + "\n".join(results) + f"\n\n👤 𝗥𝗲𝗾𝘂𝗲𝘀𝘁 𝗯𝘆: {username}  |  𝗝𝗼𝗶𝗻: @rszoneBDx"

            try:
                bot.edit_message_text(
                    chat_id=sent_msg.chat.id,
                    message_id=sent_msg.message_id,
                    text=reply_text.strip(),
                    parse_mode="HTML"
                )
            except Exception as e:
                pass # Ignore edit message errors for now

            # Wait for 17 seconds before checking the next card
            if i < len(cards) - 1:
                time.sleep(17)
        
        final_reply_text = "\n".join(results) + f"\n\n👤 𝗥𝗲𝗾𝘂𝗲𝘀𝘁 𝗯𝘆: {username}  |  𝗝𝗼𝗶𝗻: @rszoneBDx"
        
        if len(final_reply_text) > 4000:
            final_reply_text = final_reply_text[:3900] + "\n\n⚠️ Output trimmed..."
        
        try:
            bot.edit_message_text(
                chat_id=sent_msg.chat.id,
                message_id=sent_msg.message_id,
                text=final_reply_text.strip(),
                parse_mode="HTML"
            )
        except Exception as e:
            bot.reply_to(message, f"⚠️ Failed to edit message: {str(e)}")
