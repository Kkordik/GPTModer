from initialize_app import app
from message_handler import handle_message
from pyrogram.handlers import MessageHandler
from pyrogram import filters

# Register the Message Handler
app.add_handler(MessageHandler(handle_message, filters.text))

# Run the Client
app.run()