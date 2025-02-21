# Copyright (C) @TheSmartBisnu
# Channel: https://t.me/itsSmartDev

import re
import os
import asyncio
from urllib.parse import urlparse
from pyrogram.enums import ParseMode
from pyrogram import Client, filters
from config import API_ID, API_HASH, SESSION_STRING, BOT_TOKEN, ADMIN_IDS, DEFAULT_LIMIT, ADMIN_LIMIT

# Initialize the bot and user clients
bot = Client(
    "bot_session",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=1000,
    parse_mode=ParseMode.HTML
)

user = Client(
    "user_session",
    session_string=SESSION_STRING,
    workers=1000
)

scrape_queue = asyncio.Queue()

def remove_duplicates(messages):
    unique_messages = list(set(messages))
    duplicates_removed = len(messages) - len(unique_messages)
    return unique_messages, duplicates_removed

async def scrape_messages(client, chat_id, limit, start_number=None):
    messages = []
    count = 0
    pattern = r'\d{16}\D*\d{2}\D*\d{2,4}\D*\d{3,4}'
    async for message in user.search_messages(chat_id):
        if count >= limit:
            break
        text = message.text if message.text else message.caption
        if text:
            matched_messages = re.findall(pattern, text)
            if matched_messages:
                formatted_messages = []
                for matched_message in matched_messages:
                    extracted_values = re.findall(r'\d+', matched_message)
                    if len(extracted_values) == 4:
                        card_number, mo, year, cvv = extracted_values
                        year = year[-2:]
                        formatted_messages.append(f"{card_number}|{mo}|{year}|{cvv}")
                messages.extend(formatted_messages)
                count += len(formatted_messages)
    if start_number:
        messages = [msg for msg in messages if msg.startswith(start_number)]
    messages = messages[:limit]
    return messages

@bot.on_message(filters.command(["scr"]))
async def scr_cmd(client, message):
    args = message.text.split()[1:]
    if len(args) < 2 or len(args) > 3:
        await message.reply_text("<b>⚠️ Provide chat username/ID and amount to scrape</b>")
        return
    chat_identifier = args[0]
    limit = int(args[1])
    max_lim = ADMIN_LIMIT if message.from_user.id in ADMIN_IDS else DEFAULT_LIMIT
    if limit > max_lim:
        await message.reply_text(f"<b>Sorry Bro! Amount over Max limit is {max_lim} ❌</b>")
        return
    start_number = args[2] if len(args) == 3 else None
    
    try:
        chat = await user.get_chat(chat_identifier)
        chat_id = chat.id
        chat_title = chat.title
    except Exception as e:
        await message.reply_text(f"<b>Failed to access chat ❌ Error: {e}</b>")
        return
    
    temporary_msg = await message.reply_text("<b>Scraping in progress wait.....</b>")
    scrapped_results = await scrape_messages(user, chat_id, limit, start_number)
    unique_messages, duplicates_removed = remove_duplicates(scrapped_results)
    
    if unique_messages:
        file_name = f"x{len(unique_messages)}_{chat_title.replace(' ', '_')}.txt"
        with open(file_name, 'w') as f:
            f.write("\n".join(unique_messages))
        with open(file_name, 'rb') as f:
            caption = (
                f"<b>CC Scrapped Successful ✅</b>\n"
                f"<b>━━━━━━━━━━━━━━━━</b>\n"
                f"<b>Source:</b> <code>{chat_title}</code>\n"
                f"<b>Amount:</b> <code>{len(unique_messages)}</code>\n"
                f"<b>Duplicates Removed:</b> <code>{duplicates_removed}</code>\n"
                f"<b>━━━━━━━━━━━━━━━━</b>\n"
                f"<b>Card-Scrapper By: <a href='https://t.me/itsSmartDev'>Smart Dev</a></b>\n"
            )
            await temporary_msg.delete()
            await client.send_document(message.chat.id, f, caption=caption)
        os.remove(file_name)
    else:
        await temporary_msg.delete()
        await client.send_message(message.chat.id, "<b>Sorry Bro ❌ No Credit Card Found</b>")

if __name__ == "__main__":
    user.start()
    bot.run()
