from typing import List
from collections import deque
import ast
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from telegraph import TelegraphPage
import openai
from config import GPT_SYS_MESSAGE
from initialize_app import app
from list_gpt_functions import gpt3_functions_set


class GPT:
    def __init__(self, user_input: str, message: Message = None, replies_context_history: list = None,
                context: list = None, model: str = "gpt-3.5-turbo"):
        self.message = message
        self.user_input = user_input
        self.replies_context_history = replies_context_history or []
        self.context = context or []
        self.model = model


    async def acreate(self, functions: list, context: list, function_call: str = "auto",  model: str = "gpt-3.5-turbo") -> dict:
        """
        Creates a GPT chat response. 
        :param functions: The list of functions to use in the GPT interaction.
        :param context: The context for the GPT interaction. The last message in the context is the user input.
        :param function_call: The function call type. Can be 'auto', 'none'.
        :param model: The model to use for the GPT interaction.
        :return: openai_response (dict).
        """

        self.model = model or self.model
        self.context = context or self.context
        
        openai_response = await openai.ChatCompletion.acreate(
            model=self.model,
            messages=self.context,
            functions=functions,
            function_call=function_call
        )

        return openai_response

    
    async def get_context(self, get_replies=False, message: Message=None):
        """
        Gets the context for the GPT interaction.
        :param get_replies: If True, gets the context from the message reply history.
        :param message: The message to get the context from.
        :return: The context in format [{'role': 'user', 'content': 'message text'}, ...]
        Last message in the context is the user input.
        """
        if self.context:
            return self.context
        
        self.message = message or self.message
        if not self.message:
            get_replies=False
        
        if get_replies:
            self.context = [
                {"role": "system", "content": GPT_SYS_MESSAGE},
                *await self.get_replies_context_history(self.message),
                {"role": "user", "content": self.user_input}
            ]  
        else:
            self.context = [{"role": "user", "content": self.user_input}]
        return self.context
    
    def add_to_context(self, new_messages: list):
        """
        Adds new messages to the context.
        :param new_messages: The new messages to add to the context.
        """
        self.context.extend(new_messages)

    async def get_replies_context_history(self, message: Message=None):
        """
        Gets the context history of the message.
        :return: The context history in format [{'role': 'user', 'content': 'message text'}, ...]
        """
        if self.replies_context_history:
            return self.replies_context_history
        
        self.message = message or self.message
        if not self.message:
            return []
        
        # Using deque() to add the messages to the context history in the order, that they were sent
        replies_context_deque = deque()
        current_message = self.message

        while current_message.reply_to_message_id:
            # Get the message that the current message is replying to
            current_message = await app.get_messages(current_message.chat.id, current_message.reply_to_message_id)

            # Get the telegraph URLs from the message, where the function call and response or error are posted
            telegraph_urls = self.extract_message_telegraph_urls(current_message)

            # Add the message text that the current message is replying to to the context history
            sender_role = "assistant" if current_message.from_user.is_self else "user"
            replies_context_deque.appendleft({"role": sender_role, "content": current_message.text})

            # Add the function call and response or error from the telegraph URLs to the context history
            for url in reversed(telegraph_urls):
                called_function, params, result = await TelegraphPage(url=url).read_telegraph_page()
                replies_context_deque.appendleft({"role": "function", "name": called_function, "content": str(result)})
                replies_context_deque.appendleft({"role": "assistant", "content": None,"function_call": {"name": called_function,"arguments": str(params)}})

        self.replies_context_history = list(replies_context_deque)
        return self.replies_context_history

    def extract_message_telegraph_urls(self, message: Message=None, only_bot_messages: bool=True):
        """
        Extracts the telegraph URLs from the message.
        :param message: The message to extract the telegraph URLs from.
        :param only_bot_messages: If True, only extracts the telegraph URLs from the bot messages.
        :return: The telegraph URLs in format ['https://telegra.ph/...', ...]
        """
        if not (only_bot_messages and message.from_user.is_self):
            return []
        
        self.message = message or self.message
        if not self.message:
            return []
        
        telegraph_urls = []
        if self.message.entities:
            for entity in self.message.entities:
                if entity.type == MessageEntityType.TEXT_LINK and entity.url.startswith('https://telegra.ph'):
                    telegraph_urls.append(entity.url)
        return telegraph_urls
    
    @staticmethod
    async def handle_function_call(openai_response: dict):
        """
        Handles the function call and arguments from GPT response. In case of an error, 'params' will be a string, otherwise a dict.
        :param openai_response: The response from GPT-3. Data type: dict.
        :return: is_function_call, called_function, params, error_msg. Data type: bool, str, dict/str, str.
        """
        called_function, params, error_msg = None, None, ''

        try:
            # Check if the response contains a function call
            if openai_response['choices'][0]['finish_reason'] == 'function_call':
                
                called_function = openai_response['choices'][0]['message']['function_call']['name']
                # Check if the called function exists

                if called_function not in gpt3_functions_set:
                    error_msg += f"Called function {called_function} doesn't exist. "
                try:
                    # Get the arguments of the function call, generated by GPT
                    params = ast.literal_eval(openai_response['choices'][0]['message']['function_call']['arguments'])
                except Exception as e:
                    error_msg += f"Invalid JSON format in arguments. "
                    params = str(openai_response['choices'][0]['message']['function_call']['arguments'])
        except Exception as e:
            error_msg += str(e) + ' '
        return called_function, params, error_msg
