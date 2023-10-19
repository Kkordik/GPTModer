import datetime
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus, ParseMode
import openai
import aiohttp
from config import telegram_token, telegraph_token, openai_api_key, api_hash, api_id
openai.api_key = openai_api_key


# Pyrogram Client
app = Client(
    "my_bot",
    api_id=api_id,
    api_hash=api_hash,
    bot_token=telegram_token,
    parse_mode=ParseMode.MARKDOWN
)


# Secure Parameters Class
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
        "description": "Get the number of members in a chat.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "setChatDescription",
        "description": "Change the description of a chat.",
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


async def post_telegraph_page(called_function, params, result):
    async with aiohttp.ClientSession() as session:
        response = await session.post(
            'https://api.telegra.ph/createPage',
            json={
                "access_token": telegraph_token,
                "title": f"Processing Request ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})",
                "author_name": "GPTModerBot",
                "author_url": "https://telegram.me/GPTModerBot",
                "content": [f"{called_function}\n\n{params}\n\n{result}"]
            }
        )
        data = await response.json()
        print(data)
        return data["result"]["url"]


async def read_telegraph_page(url):
    async with aiohttp.ClientSession() as session:
        response = await session.get(f'https://api.telegra.ph/getPage/{url.split("/")[-1]}?return_content=true')
        data = await response.json()
        content = data['result']['content'][0]
        called_function, params, result = content.split('\n\n')
        params = eval(params)
        result = eval(result)
        return called_function, params, result


# Telegram API Execution Function
async def telegram_api_execution(message, user_status, called_function, params):
    if called_function in permissions.get(user_status, set()):
        print(f"called function: {called_function}, params: {params}")
        telegram_api_url = f'https://api.telegram.org/bot{telegram_token}/{called_function}'
        secure_params = SecureParameters(called_function, message).get_all()
        params.update(secure_params)

        async with aiohttp.ClientSession() as session:
            async with session.post(telegram_api_url, json=params) as resp:
                return await resp.json()
    else:
        return "You do not have permission to use this function."


# Function to Handle Function Calls
async def handle_function_call(openai_response):
    """
    Handles function calls from GPT-3 based on user status and permissions.
    :param openai_response: The response from GPT-3.
    """
    called_function, params = None, None

    if openai_response['choices'][0]['finish_reason'] == 'function_call':
        called_function = openai_response['choices'][0]['message']['function_call']['name']
        # Convert arguments string of json format to dict type
        params = eval(openai_response['choices'][0]['message']['function_call']['arguments'])
        # Add secure parameters (f.e. chat_id)

    return called_function, params


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
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_input},
        ],
        function_call="auto"
    )
    print(openai_response)
    called_function, params = await handle_function_call(openai_response)

    if called_function:
        tg_response = await telegram_api_execution(message, user_status, called_function, params)
        url = await post_telegraph_page(called_function, params, tg_response)
        answer_text += f'[‎ ]({url})'
        # Sending the Telegram API response to GPT-3
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
    answer_text += openai_response['choices'][0]['message']['content']
    # Sending GPT-3's response back to the user
    await message.reply(text=answer_text, disable_web_page_preview=True)

# Run the Client
app.run()
