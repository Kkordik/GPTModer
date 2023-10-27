from pyrogram.types import Message
from secure_parameters import SecureParameters
import aiohttp
import json
from config import TELEGRAM_TOKEN
from list_gpt_functions import gpt3_functions_set



class FunctionCall:
    def __init__(self, called_function: str, params: dict = None, message: Message = None):
        self.called_function = called_function
        self.params = params
        self.message = message
        self.result = None
        self.error = ''

    async def execute(self) -> tuple:
        """
        Executes the function call. Returns the result and error.
        Each method requires its own values to be provided while initializing the FunctionCall class.
        Not to get raised error pass all the required values.
        :return: The result and error. Data type: dict, str.
        """

        for method in function_call_methods.keys():
            if self.called_function in function_call_methods[method]:
                self.result, self.error = await method(self)
                break
        return self.result, self.error

    async def telegram_api_execution(self):
        """
        Executes the Telegram API function call. Returns the result or error.
        :param message: The pyrogram message object.
        :param user_status: The user status. Data type: pyrogram.enums.ChatMemberStatus.
        :param called_function: The called function. 
        :param params: The parameters of the function call.
        :return: The result or error. Data type: dict, str.
        """

        if not self.called_function or isinstance(self.params, type(None)) or isinstance(self.params, type(None)):
            raise ValueError(f"telegram_api_execution: The called function, params and message must be provided while initializing the FunctionCall class. Got self.called_function = {self.called_function}, self.params = {self.params}, self.message = {self.message}")

        try:
            
            # Telegram API URL
            telegram_api_url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/{self.called_function}'
            # Get the secure parameters (chat_id, etc.)
            secure_params = SecureParameters(self.called_function, self.message).get_all()
            self.params.update(secure_params)
            
            async with aiohttp.ClientSession() as session:
                try:
                    # Send the request to the Telegram API
                    async with session.post(telegram_api_url, json=self.params) as resp:
                        resp.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
                        self.result = await resp.json()
                except aiohttp.ClientResponseError as e:
                    self.error += f"HTTP error occurred: {e.status}. "
                except json.JSONDecodeError as e:
                    self.error += f"JSON decode error occurred: {e}. "
        
        except Exception as e:
            self.error += str(e) + ' '

        return self.result, self.error
    


function_call_methods = {FunctionCall.telegram_api_execution: gpt3_functions_set}