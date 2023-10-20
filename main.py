import datetime
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus, ParseMode
import openai
import aiohttp
import secrets
import json
from config import telegram_token, telegraph_token, openai_api_key, api_hash, api_id
openai.api_key = openai_api_key


class FunctionCallError(Exception):
    pass

# Pyrogram Client
app = Client(
    "my_bot",
    api_id=api_id,
    api_hash=api_hash,
    bot_token=telegram_token,
    parse_mode=ParseMode.MARKDOWN
)


# Secure Parameters Class (chat_id, etc.)
class SecureParameters:
    def __init__(self, called_function, message):
        self.message = message
        self.required_spm = function_required_spm.get(called_function, [])
        self.secure_params = {}

    def get_all(self):
        for method in self.required_spm:
            self.secure_params.update(method(self))
        return self.secure_params

    def get_chat_id(self):
        return {'chat_id': self.message.chat.id}


# Permissions and Secure Params Dict
permissions = {
    ChatMemberStatus.OWNER: {'getChatMemberCount', 'setChatDescription'},
    ChatMemberStatus.ADMINISTRATOR: {'getChatMemberCount', 'setChatDescription'},
    ChatMemberStatus.MEMBER: {'getChatMemberCount'}
}

# Required secure parameters methods
function_required_spm = {
    'getChatMemberCount': [SecureParameters.get_chat_id],
    'setChatDescription': [SecureParameters.get_chat_id],
}

# GPT-3 Functions List
gpt3_functions = [
    {
        "name": "getChatMemberCount",
        "description": "Get the number of members in the chat.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "setChatDescription",
        "description": "Change the description of the chat.",
        "parameters": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "New chat description, 0-255 characters."
                }
            },
            "required": ["description"]
        }
    }
]

# GPT-3 Functions Set
gpt3_functions_set = {function['name'] for function in gpt3_functions}

async def post_telegraph_page(called_function, params, result):
    """
    Posts a page on Telegraph with the called function, parameters and result.
    :param called_function: The called function.
    :param params: The parameters of the function call.
    :param result: The result of the function call.
    :return: The URL of the Telegraph page.
    """
    async with aiohttp.ClientSession() as session:
        response = await session.post(
            'https://api.telegra.ph/createPage',
            json={
                "access_token": telegraph_token,
                "title": f"Request #{secrets.token_hex(8)} ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})",
                "author_name": "GPTModerBot",
                "author_url": "https://telegram.me/GPTModerBot",
                "content": [f"{called_function}\n\n{params}\n\n{result}"]
            }
        )
        data = await response.json()
        print(data)
        return data["result"]["url"]


async def read_telegraph_page(url):
    """
    Reads a Telegraph page and returns the called function, parameters and result.
    :param url: The URL of the Telegraph page.
    :return: The called function, parameters and result. Data type: str, dict, dict.
    """
    async with aiohttp.ClientSession() as session:
        response = await session.get(f'https://api.telegra.ph/getPage/{url.split("/")[-1]}?return_content=true')
        data = await response.json()
        content = data['result']['content'][0]
        called_function, params, result = content.split('\n\n')
        params = json.loads(params)
        result = json.loads(result)
        return called_function, params, result


async def telegram_api_execution(message, user_status, called_function, params):
    """
    Executes the Telegram API function call. Returns the result or error.
    :param message: The pyrogram message object.
    :param user_status: The user status. Data type: pyrogram.enums.ChatMemberStatus.
    :param called_function: The called function. 
    :param params: The parameters of the function call.
    :return: The result or error. Data type: dict, str.
    """
    result, error = None, None
    try:

        # Check if the user has permission to use the function
        if called_function in permissions.get(user_status, set()):

            print(f"called function: {called_function}, params: {params}")
            # Telegram API URL
            telegram_api_url = f'https://api.telegram.org/bot{telegram_token}/{called_function}'
            # Get the secure parameters (chat_id, etc.)
            secure_params = SecureParameters(called_function, message).get_all()
            params.update(secure_params)

            async with aiohttp.ClientSession() as session:
                try:
                    # Send the request to the Telegram API
                    async with session.post(telegram_api_url, json=params) as resp:
                        resp.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
                        result = await resp.json()
                except aiohttp.ClientResponseError as e:
                    error = f"HTTP error occurred: {e}"
                except json.JSONDecodeError as e:
                    error = f"JSON decode error occurred: {e}"
        else:
            error = "The user doesn't have permission to use this function."
    except Exception as e:
        error = str(e)

    return result, error


async def handle_function_call(openai_response):
    """
    Handles function calls from GPT-3 based on user status and permissions.
    :param openai_response: The response from GPT-3.
    :return: Error message, called function, parameters.
    """
    called_function, params, error = None, None, None
    try:
        # Check if the response contains a function call
        if openai_response['choices'][0]['finish_reason'] == 'function_call':
            called_function = openai_response['choices'][0]['message']['function_call']['name']
            # Check if the called function exists
            if called_function not in gpt3_functions_set:
                error = f"Called function {called_function} doesn't exist"
            # Get the arguments of the function call, generated by GPT
            params = json.loads(openai_response['choices'][0]['message']['function_call']['arguments'])
        else:
            error = "No function call found"
    except json.JSONDecodeError:
        error = "Invalid JSON format in arguments"
    except Exception as e:
        error = str(e)
    return called_function, params, error


# Message Handler
@app.on_message(filters.text)
async def handle_message(_, message):
    user_input = message.text
    chat_id = message.chat.id
    chat_member = await app.get_chat_member(chat_id, message.from_user.id)
    user_status = chat_member.status
    answer_text = ''

    # GPT interaction
    openai_response = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo",
        functions=gpt3_functions,
        messages=[
            {"role": "system", "content": "You are a helpful assistant for Telegram groups."},
            {"role": "user", "content": user_input},
        ],
        function_call="auto"
    )
    print(openai_response)

    # Handling function calls
    called_function, params, error = await handle_function_call(openai_response)

    if called_function:
        # Executing the Telegram API function call if no error occurred while handling the function call and arguments
        if error is None:
            result, error = await telegram_api_execution(message, user_status, called_function, params)
        tg_response = error if error else result

        print(tg_response)

        # Posting the Telegram API call and response or error on Telegraph 
        url = await post_telegraph_page(called_function, params, tg_response)
        # Adding the Telegraph URL to the answer message text
        answer_text += f'[‎ ]({url})'
        
        # Sending the function call and response or error to GPT
        openai_response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_input},
                openai_response['choices'][0]['message'],
                {"role": "function", "name": called_function, "content": str(tg_response)},
            ]
        )
        print(openai_response)

    # Adding GPT's response to the answer message text
    answer_text += openai_response['choices'][0]['message']['content']
    # Sending GPT-3's response back to the user
    await message.reply(text=answer_text, disable_web_page_preview=True)

# Run the Client
app.run()
