
# 🤖 Multi-Feature Telegram Bot

A powerful Telegram bot with multiple utilities including card generation, translation, AI chat, image processing, and more!

## 🌟 Features Overview

### 💳 Card Generation & Checking
- **Generate Cards**: Create test cards from BIN numbers
- **Single Card Check**: Validate individual cards
- **Mass Check**: Bulk validation of card lists
- **BIN Information**: Get detailed bank and country info

### 🤖 AI & Chat Features
- **Gemini AI**: Chat with Google's Gemini AI
- **GPT Integration**: Alternative AI chat option
- **Auto-Reply**: Enable/disable AI auto-responses

### 🌐 Translation & Communication
- **Multi-Language Translation**: Translate text to any language
- **Text-to-Speech**: Convert text to audio
- **Say Command**: Generate speech from text

### 🎨 Image & Media Processing
- **Background Removal**: Remove backgrounds from images
- **Image Generation**: Create AI-generated images
- **Media Download**: Download content from various platforms

### 📊 Information & User Features
- **User Information**: Get detailed info about Telegram users, bots, groups, and channels
- **Advanced User Lookup**: Multiple methods to fetch user data including usernames and IDs
- **Group Analysis**: Detailed group and channel information retrieval

### 🛠️ Utility Features
- **Multiple Fake Address Generators**: Generate test addresses using FakeXYZ and alternative sources
- **IBAN Generation**: Create valid IBAN numbers for various countries
- **Spam Generation**: Text spam and file generation tools
- **Weather Information**: Real-time weather, forecasts, and air quality data
- **File Management**: Download and process files

### 🎵 Media & Entertainment
- **YouTube Operations**: Search and download YouTube videos/audio
- **AI Art Generation**: Create artwork with style-specific prompts
- **Advanced Media Processing**: Multiple download sources and formats

---

## 📋 Command Reference

### 🔹 Card Generation Commands

#### `/gen` or `.gen` - Generate Cards
**Syntax:**
```
/gen <BIN> .cnt <amount>
/gen <BIN>|<MM>|<YY>|<CVV> .cnt <amount>
```

**Examples:**
```
/gen 526732 .cnt 5
/gen 526732xxxxxx|12|28|000 .cnt 10
/gen 515462xxxxxx .cnt 15
```

**Parameters:**
- `BIN`: 6-16 digit BIN number (Visa: 4xxx, MasterCard: 5xxx)
- `.cnt`: Number of cards to generate (max 30)
- `MM`: Expiry month (optional)
- `YY`: Expiry year (optional)
- `CVV`: Card verification value (optional)

#### `/chk` or `.chk` - Check Single Card
**Syntax:**
```
/chk <card>|<mm>|<yy>|<cvv>
```

**Example:**
```
/chk 5267321234567890|05|28|123
```

#### `/mas` - Mass Check Cards
**Usage:**
1. Generate cards using `/gen`
2. Reply to the generated card list with `/mas`

#### `/bin` - BIN Information
**Syntax:**
```
/bin <6-digit-bin>
```

**Example:**
```
/bin 526732
```

### 🔹 AI Chat Commands

#### `/gemini` - Chat with Gemini AI
**Syntax:**
```
/gemini <your question>
```

**Example:**
```
/gemini What is artificial intelligence?
```

#### `/gemini_on` - Enable Auto-Reply
Enables automatic AI responses to all messages in the chat.

#### `/gemini_off` - Disable Auto-Reply
Disables automatic AI responses.

#### `/gpt` - Chat with GPT
**Syntax:**
```
/gpt <your question>
```

### 🔹 Translation Commands

#### `/translate` - Translate Text
**Syntax:**
```
/translate <language_code> <text>
```

**Examples:**
```
/translate fr Hello World
/translate es How are you?
/translate bn I love programming
```

**Reply Method:**
Reply to any message with `/translate <language_code>` to translate that message.

### 🔹 Media & Image Commands

#### `/say` - Text to Speech
**Syntax:**
```
/say <text>
```

**Example:**
```
/say Hello, this is a test message
```

#### `/bgremove` - Remove Background
Send an image with the caption `/bgremove` to remove its background.

#### `/imagine` - Generate Images
**Syntax:**
```
/imagine <description>
```

**Example:**
```
/imagine A beautiful sunset over mountains
```


#### `/download` - Download Media
**Syntax:**
```
/download <URL>
```

### 🔹 Information & User Commands

#### `/usr` - User Information
**Syntax:**
```
/usr @username
/usr (reply to a message)
```
Get detailed information about a Telegram user.

#### `/bot` - Bot Information  
**Syntax:**
```
/bot @botusername
```
Get information about a Telegram bot.

#### `/grp` - Group Information
**Syntax:**
```
/grp @groupusername
/grp (use in group without parameters)
```
Get information about a Telegram group.

#### `/cnnl` - Channel Information
**Syntax:**
```
/cnnl @channelusername
```
Get information about a Telegram channel.

#### `/info` - General Info Command
Get information about users, bots, groups or channels.

### 🔹 Utility Commands

#### `/fake` - Generate Fake Address
**Syntax:**
```
/fake <country_code>
```
Generate fake address for testing purposes using the FakeXYZ library.

#### `/country` - List Supported Countries
Shows available country codes for fake address generation.

#### `/fake3` - Alternative Fake Address Generator
**Syntax:**
```
/fake3 <country_code>
```
Alternative fake address generator with different data source.

#### `/country3` - List Countries (Alternative)
Shows available countries for `/fake3` command.

#### `/iban` - Generate IBAN
**Syntax:**
```
/iban <country_code>
```
Generate IBAN numbers for specified countries.

#### `/ibncntry` - List IBAN Countries
Shows supported countries for IBAN generation.

#### `/spam` - Text Spam
**Syntax:**
```
/spam <text>
```
Generate normal text spam messages.

#### `/spmtxt` - Spam Text File
Generate text files for spamming purposes.

#### `/gart` - AI Art Generation
**Syntax:**
```
/gart <prompt> | <style>
```
Generate AI artwork with specific style prompts.

#### `/wth` - Weather Information
**Syntax:**
```
/wth <city>
```
Get weather information, forecasts, and air quality for any city.

#### `/yt` - YouTube Operations
**Syntax:**
```
/yt <search term or URL>
```
Search YouTube videos and download them as audio or video.

#### `/start` or `/arise` - Welcome Message
Shows welcome message and basic command overview.

#### `/reveal` - Show All Commands
Displays comprehensive command list.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- Telegram Bot Token (from @BotFather)
- Required API keys for various services

### Installation on Replit

1. **Fork this Repl** or create a new Python Repl
2. **Install Dependencies**: Dependencies will be automatically installed from `requirements.txt`
3. **Set Environment Variables**: Use Replit Secrets to configure:
   - `BOT_TOKEN`: Your Telegram bot token
   - `GEMINI_API_KEY`: Google Gemini API key (optional)
   - `OPENAI_API_KEY`: OpenAI API key (optional)
4. **Run the Bot**: Click the Run button or use `python main.py`

### Configuration

Add these secrets in your Replit environment:

```
BOT_TOKEN=your_telegram_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

---

## 📁 Project Structure

```
├── handlers/                     # Command handlers
│   ├── gen_handler.py            # Card generation
│   ├── chk_handler.py            # Card checking and mass validation
│   ├── bin_handler.py            # BIN information lookup
│   ├── translate_handler.py      # Multi-language translation
│   ├── gemini_handler.py         # Google Gemini AI chat
│   ├── gpt_handler.py            # GPT AI integration
│   ├── say_handler.py            # Text-to-speech conversion
│   ├── bgremove_handler.py       # Background removal from images
│   ├── imagine_handler.py        # AI image generation
│   ├── gart_handler.py           # AI artwork generation
│   ├── userinfo_handler.py       # User/bot/group/channel info
│   ├── fakeAddress_handler.py    # Fake address generation (FakeXYZ)
│   ├── fakeAddress2_handler.py   # Alternative fake addresses
│   ├── fakeAddress3_handler.py   # Third fake address source
│   ├── iban_handler.py           # IBAN generation
│   ├── spam_handler.py           # Spam generation tools
│   ├── wth_handler.py            # Weather information
│   ├── yt_handler.py             # YouTube operations
│   ├── download_handler.py       # Media download
│   ├── start_handler.py          # Welcome messages
│   └── reveal_handler.py         # Command list display
├── main.py                       # Main bot file with Flask server
├── cleanup.py                    # Cleanup utilities
├── flag_data.py                 # Country flags data
├── requirements.txt              # Python dependencies (including FakeXYZ)
└── README.md                    # Documentation
```

---

## ⚠️ Important Notes

### Card Generation Limits
- ✅ Only **Visa (4xxx)** and **MasterCard (5xxx)** BINs supported
- ✅ American Express, Discover not supported
- 🔢 Maximum 30 cards per request
- ⚠️ Cards are for **testing purposes only**

### API Rate Limits
- Some features may have rate limits depending on external APIs
- The bot includes fallback mechanisms for reliability

### Privacy & Security
- Chat histories are stored locally for AI continuity
- No sensitive data is permanently stored
- Use responsibly and follow Telegram's ToS

---

## 🛠️ Development

### Adding New Features

1. Create a new handler file in `handlers/`
2. Import and register in `handlers/__init__.py`
3. Add registration call in `main.py`

### Contributing

1. Fork the project
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

## 📞 Support & Links

- **Telegram Channel**: [https://t.me/rszoneBDx](https://t.me/rszoneBDx)
- **Issues**: Report bugs and request features
- **Documentation**: This README file

---

## 🙏 Credits & Acknowledgments

This bot utilizes several external libraries and services:

- **FakeXYZ Library**: Custom Python library for generating realistic fake address data used in the `/fake` commands
- **Google Gemini AI**: Advanced AI chat capabilities
- **OpenAI GPT**: Alternative AI integration
- **pyTelegramBotAPI**: Core Telegram bot framework
- **Various APIs**: Weather, BIN lookup, and media download services

Special thanks to all the open-source libraries and API providers that make this bot possible.

---

## 📄 License

This project is for educational purposes only. Use responsibly and in accordance with all applicable laws and terms of service.

---

## 🔄 Recent Updates

- ✅ Enhanced card generation with multiple fallback APIs
- ✅ Improved BIN information accuracy
- ✅ Added translation capabilities
- ✅ Integrated AI chat features
- ✅ Background removal functionality
- ✅ Added comprehensive user information commands
- ✅ Multiple fake address generators
- ✅ Weather and YouTube integration
- ✅ IBAN and spam generation tools

---

**Happy Botting! 🤖**

*Built with ❤️ for the Telegram community*
