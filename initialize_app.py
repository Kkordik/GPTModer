from pyrogram import Client
from pyrogram.enums import ParseMode
from config import TELEGRAM_TOKEN, API_ID, API_HASH


def initialize_app():
    # Pyrogram Client
    return Client(
        "my_bot",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=TELEGRAM_TOKEN,
        parse_mode=ParseMode.MARKDOWN
    ) 

app = initialize_app()