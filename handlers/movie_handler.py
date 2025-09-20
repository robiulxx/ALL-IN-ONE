import html
import requests
import telebot
from urllib.parse import urlparse

# API endpoint for movie search
MOVIE_API_URL = "https://movie-src.vercel.app/api/src?query={query}"

def search_movie(query):
    """Search for a movie and return download links."""
    try:
        url = MOVIE_API_URL.format(query=requests.utils.quote(query))
        # Changed timeout to 60 seconds
        response = requests.get(url, timeout=60)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

        data = response.json()

        if not data.get("ok"):
            return "❌ API Error: Something went wrong with the movie search service."

        results = data.get("results", [])
        if not results:
            return "❌ No movie found with that title."

        output_list = []
        for movie in results:
            title = movie.get("title", "N/A")
            year = movie.get("year", "N/A")
            movie_type = movie.get("type", "N/A")
            poster = movie.get("poster", None)

            # Create a header for the movie
            movie_header = (
                f"🎬 <b>Title:</b> <code>{html.escape(title)}</code>\n"
                f"📅 <b>Year:</b> <code>{html.escape(year)}</code>\n"
                f"🎥 <b>Type:</b> <code>{html.escape(movie_type)}</code>\n"
            )
            
            # Add poster URL if available
            if poster:
                movie_header += f"🖼️ <b>Poster:</b> <a href='{html.escape(poster)}'>Click Here</a>\n"

            # Add download links with source labels
            links_output = ""
            download_links = movie.get("downloadLink", [])
            if download_links:
                links_output += "📥 <b>Download Links:</b>\n"
                for quality_links in download_links:
                    quality = quality_links.get("quality", "N/A")
                    links = quality_links.get("links", [])
                    links_output += f"  - <b>{html.escape(quality)}:</b>\n"
                    for link in links:
                        # Get the domain name from the URL and format it
                        try:
                            source = urlparse(link).netloc
                            source = source.split('.')[0] if '.' in source else source
                        except:
                            source = "Unknown Source"

                        # Escape special characters in the URL
                        safe_link = html.escape(link).replace("&amp;#038;", "&")
                        links_output += f"    • {html.escape(source)}: <a href='{safe_link}'>Click Here</a>\n"
            else:
                links_output += "🔗 No download links available."

            output_list.append(f"{movie_header}{links_output}")

        return "\n" + "\n" + "\n".join(output_list)

    except requests.exceptions.RequestException as e:
        return f"⚠️ Connection Error: Failed to connect to the movie API. Please try again later. ({str(e)})"
    except Exception as e:
        return f"⚠️ An unexpected error occurred: {str(e)}"

def register(bot, custom_command_handler, command_prefixes_list):
    @custom_command_handler("movie", "ms")
    def handle_movie_search(message):

        command_text = message.text.split(" ", 1)[0].lower()
        actual_command_len = 0
        for prefix in command_prefixes_list:
            if command_text.startswith(f"{prefix}movie") or command_text.startswith(f"{prefix}ms"):
                actual_command_len = len(command_text)
                break
        
        query = message.text[actual_command_len:].strip()

        if not query:
            bot.reply_to(message, "❌ Please provide a movie title to search. Example: `/ms Sultanpur`", parse_mode="Markdown")
            return

        user = message.from_user
        username = f"@{user.username}" if user.username else user.first_name

        sent_msg = bot.reply_to(message, f"🔄 Searching for movies with title <code>{html.escape(query)}</code>...\n\n<i>(It might take a few moments to get the results.)</i>", parse_mode="HTML")

        search_results = search_movie(query)

        footer = f"\n\n👤 𝗥𝗲𝗾𝘂𝗲𝘀𝘁 𝗯𝘆: {username}  |  𝗝𝗼𝗶𝗻: @rszone24"
        final_text = f"<b>🔎 Search results for:</b> <code>{html.escape(query)}</code>\n" + search_results + footer

        if len(final_text) > 4096:
            final_text = final_text[:4000] + "\n\n⚠️ Output trimmed..."

        try:
            bot.edit_message_text(
                chat_id=sent_msg.chat.id,
                message_id=sent_msg.message_id,
                text=final_text.strip(),
                parse_mode="HTML",
                disable_web_page_preview=True
            )
        except Exception as e:
            bot.reply_to(message, f"⚠️ Failed to edit message: {str(e)}")
