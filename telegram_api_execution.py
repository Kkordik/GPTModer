import aiohttp
import json
from config import TELEGRAM_TOKEN
from secure_parameters import SecureParameters
from permissions import permissions


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

            
            # Telegram API URL
            telegram_api_url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/{called_function}'
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
                    error = f"HTTP error occurred: {e.status}"
                except json.JSONDecodeError as e:
                    error = f"JSON decode error occurred: {e}"
        else:
            error = "The user doesn't have permission to use this function."
    except Exception as e:
        error = str(e)

    return result, error