from pyrogram import filters
from pyrogram.handlers import MessageHandler
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from collections import deque
from config import gpt_sys_message, max_function_calls, openai_api_key
from list_gpt_functions import gpt3_functions
from handle_function_call import handle_function_call
from telegraph import read_telegraph_page, post_telegraph_page
from telegram_api_execution import telegram_api_execution
import openai
from initialize_app import app

openai.api_key = openai_api_key

async def get_replies_context_history(message: Message):
    """
    Gets the context history of the message.
    :param message: The pyrogram message object.
    :return: The context history in format [{'role': 'user', 'content': 'message text'}, ...]
    """
    replies_context_history = deque()
    current_message = message

    while current_message.reply_to_message_id:
        # Get the message that the current message is replying to
        current_message = await app.get_messages(message.chat.id, current_message.reply_to_message_id)

        # Get the telegraph URLs from the message, where the function call and response or error are posted
        telegraph_urls = []
        if current_message.entities:
            for entity in current_message.entities:
                if entity.type == MessageEntityType.TEXT_LINK and entity.url.startswith('https://telegra.ph'):
                    telegraph_urls.append(entity.url)
        
        # Add the message text, data from the telegraph URLs to the context history
        if telegraph_urls and message.from_user.is_self:
            replies_context_history.appendleft({"role": "assistant", "content": current_message.text})
            for url in reversed(telegraph_urls):
                called_function, params, result = await read_telegraph_page(url)
                replies_context_history.appendleft({"role": "function", "name": called_function, "content": str(result)})
                replies_context_history.appendleft({"role": "assistant", "content": None,"function_call": {"name": called_function,"arguments": str(params)}})
        else:
            replies_context_history.appendleft({"role": "user", "content": current_message.text})

    return list(replies_context_history)


# Message Handler
async def handle_message(_, message):
    print(message)
    user_input = message.text
    chat_id = message.chat.id
    chat_member = await app.get_chat_member(chat_id, message.from_user.id)
    user_status = chat_member.status
    answer_text = ''
    i = 0
    is_function_call = True

    # The messages list contains the messages from reply history and the user input
    messages = [
        {"role": "system", "content": gpt_sys_message},
        *await get_replies_context_history(message),
        {"role": "user", "content": user_input}
        ]  
    print(messages)
    while i <= max_function_calls and is_function_call:

        # GPT interaction
        openai_response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            functions=gpt3_functions if i != max_function_calls else [],
            messages=messages,
            function_call= "auto" if i != max_function_calls else "none"
        )
        print(openai_response)

        # Handling the function call and arguments from GPT response
        is_function_call, called_function, params, error_msg = await handle_function_call(openai_response)

        if is_function_call:
            # Executing the Telegram API function call if no error occurred while handling the function call and arguments
            if not error_msg:
                result, error_msg = await telegram_api_execution(message, user_status, called_function, params)
            tg_response = error_msg if error_msg else result

            # Posting the Telegram API call and response or error on Telegraph 
            url = await post_telegraph_page(called_function, params, tg_response)
            # Adding the Telegraph URL to the answer message text
            answer_text += f'[‎ ]({url})'
            # Adding the response or error to the messages list
            messages.append(openai_response['choices'][0]['message'])
            messages.append({"role": "function", "name": called_function, "content": str(tg_response)})
        else:
            # Adding GPT's response to the answer message text
            answer_text += openai_response['choices'][0]['message']['content']

    # Sending GPT-3's response back to the user
    await message.reply(text=answer_text, disable_web_page_preview=True)

