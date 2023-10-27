from config import MAX_FUNCTION_CALLS, OPENAI_API_KEY
from list_gpt_functions import gpt3_functions
from telegraph import TelegraphPage
from telegram_api_execution import telegram_api_execution
import openai
from initialize_app import app
from gpt import GPT
from functioncall import FunctionCall
import re

openai.api_key = OPENAI_API_KEY


async def handle_message(_, message):
    """
    Handles the request message. Sends the request to GPT-3 and executes the Telegram API function calls. 
    After each function call, the response or error is posted on Telegraph. And the Telegraph URL is added to the answer message text.
    Then the answer message is sent back to the user.
    """
    user_input = message.text
    chat_id = message.chat.id
    chat_member = await app.get_chat_member(chat_id, message.from_user.id)
    user_status = chat_member.status
    answer_text = ''
    i = 0
    called_function = "start"

    gpt = GPT(user_input, message)
    await gpt.get_context(get_replies=True)

    while i <= MAX_FUNCTION_CALLS and called_function:
        i += 1
        # Creating the GPT response
        # (to_do) LATER HAVE TO IMPLEMENT EDITING FUNCTIONS BASED ON THE USER STATUS
        openai_response = await gpt.acreate(
            functions=gpt3_functions if i != MAX_FUNCTION_CALLS else [],
            context=gpt.context,
            function_call="auto" if i != MAX_FUNCTION_CALLS else "none"
        )
    

        called_function, params, error_msg = await gpt.handle_function_call(openai_response)

        if called_function:
            # Executing the Telegram API function call if no error occurred while handling the function call and arguments
            if not error_msg:
                function_call = FunctionCall(called_function, params, message)
                result, error_msg = await function_call.execute()
            function_response = error_msg if error_msg else result

            # Posting the Telegram API call and response or error on Telegraph 
            url = await TelegraphPage(called_function, params, function_response).post_telegraph_page()
            print(url)
            # Adding the Telegraph URL to the answer message text
            answer_text += f'[‎ ]({url})'
            # Adding the response or error to the messages list
            gpt.add_to_context([
                openai_response['choices'][0]['message'],
                {"role": "function", "name": called_function, "content": str(function_response)}])
        else:
            # Adding GPT's response to the answer message text
            answer_text += openai_response['choices'][0]['message']['content']

    # Sending GPT-3's response back to the user
    await message.reply(text=answer_text, disable_web_page_preview=True)

