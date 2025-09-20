import os
import telebot
import logging
from flask import Flask
from threading import Thread
import cleanup
import string

# Handlers import
from handlers import (
    b3_handler,
    bgremove_handler,
    bin_handler,
    bomb_handler,
    chk_handler,
    deepseek_handler,
    download_handler,
    enh_handler,
    fakeAddress_handler,
    gen_handler,
    gemini_handler,
    gmeg_handler,
    gpt_handler,
    grok_handler,
    iban_handler,
    imageedit_handler,
    imagine_handler,
    movie_handler,
    pfp_handler,
    reveal_handler,
    say_handler,
    spam_handler,
    start_handler,
    translate_handler,
    userinfo_handler,
    wth_handler,
    yt_handler
)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

COMMAND_PREFIXES = list(string.punctuation)

def custom_command_handler(*command_names):
    """
    A decorator that handles multiple command names for a single function.
    """
    def decorator(handler_func):
        @bot.message_handler(func=lambda message: message.text and any(
            message.text.lower().startswith(f"{prefix}{command_name}")
            for command_name in command_names
            for prefix in COMMAND_PREFIXES
        ))
        def wrapper(message):
            return handler_func(message)
        return wrapper
    return decorator

app = Flask('')

# Custom logging filter to suppress health check spam
class HealthCheckFilter(logging.Filter):
    def filter(self, record):
        # Suppress logs for /api health check requests
        if hasattr(record, 'getMessage'):
            message = record.getMessage()
            if 'HEAD /api' in message and '404' in message:
                return False
        return True

@app.route('/')
def home():
    return "Bot is running!"

def run():
    port = int(os.environ.get("PORT", 5000))
    # Apply the filter to suppress health check spam
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.addFilter(HealthCheckFilter())
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()

def register_handler(handler_module, handler_name):
    try:
        handler_module.register(bot, custom_command_handler, COMMAND_PREFIXES)
        print(f"✅ {handler_name} handler loaded successfully")
    except Exception as e:
        print(f"❌ {handler_name} handler failed to load: {str(e)}")

print("\n🔄 Loading command handlers...")
print("-" * 40)

# Register all handlers
register_handler(b3_handler, "B3")
register_handler(bgremove_handler, "BG Remove")
register_handler(bin_handler, "BIN")
register_handler(bomb_handler, "Bomber")
register_handler(chk_handler, "Check")
register_handler(deepseek_handler, "Deepseek")
register_handler(download_handler, "Download")
register_handler(enh_handler, "enh")
register_handler(fakeAddress_handler, "Fake Address")
register_handler(gen_handler, "Gen")
register_handler(gemini_handler, "Gemini")
register_handler(gmeg_handler, "Gmeg")
register_handler(gpt_handler, "GPT")
register_handler(grok_handler, "grok")
register_handler(iban_handler, "iban")
register_handler(imageedit_handler, "edit")
register_handler(imagine_handler, "Imagine")
register_handler(movie_handler, "movie")
register_handler(pfp_handler, "pfp")
register_handler(reveal_handler, "Reveal")
register_handler(say_handler, "Say")
register_handler(spam_handler, "spam")
register_handler(start_handler, "Start")
register_handler(translate_handler, "Translate")
register_handler(userinfo_handler, "User Info")
register_handler(wth_handler, "weather")
register_handler(yt_handler, "yt")


print("-" * 40)
print("✨ Handler registration completed!\n")

cleanup.cleanup_project()

if __name__ == '__main__':
    print("🤖 Bot is running...")
    bot.infinity_polling()
