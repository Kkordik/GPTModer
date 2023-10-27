from initialize_app import app
from message_handler import handle_message
from pyrogram.handlers import MessageHandler
from pyrogram import filters


def bot_request_flter(data):
    async def func(flt, _, message):
        replied_is_self = False
        if message.reply_to_message_id:
            replied_msg = await app.get_messages(message.chat.id, message.reply_to_message_id)
            replied_is_self = replied_msg.from_user.is_self
        return flt.data in message.text or replied_is_self

    # "data" kwarg is accessed with "flt.data" above
    return filters.create(func, data=data)

# Register the Message Handler
app.add_handler(MessageHandler(handle_message, bot_request_flter("gptm")))

# Run the Client
app.run()