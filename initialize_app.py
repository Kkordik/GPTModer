from pyrogram import Client
from pyrogram.enums import ParseMode
from config import telegram_token, api_id, api_hash


def initialize_app():
    # Pyrogram Client
    return Client(
        "my_bot",
        api_id=api_id,
        api_hash=api_hash,
        bot_token=telegram_token,
        parse_mode=ParseMode.MARKDOWN
    ) 

app = initialize_app()