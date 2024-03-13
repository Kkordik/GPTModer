## GPTModer

**GPTModer** is a Telegram bot for group managment through GPT. It works by adding telegram api methods and their descriptions to the GPT calls as function calls.

## How to use it
1. It can be called by replying on his message or "gptm" in your message.

2. GPTModer will add all the messages in the reply chain to his context

3. The bot can use any of the methods added to the `list_gpt_functions.py` and make up to 5 function calls in one messsage. Each function call and response is written to the telegraph and the link on it is hidden in the beggining of the message inside of empty char. (It is done to let the bot extract function calls and responses from the message chain and add them to the context)

4. After making function calls (if needed) the bot will write you an aswer and send it replying to the prompt message, adding this way the prompt and the answer to the possible context(reply chain) for all the next queries.

### Visit channel for more details 

https://t.me/gptmoder_tests

### Note: There are mistakes in the code, after opeani have changed their python lib I dont remember, if I have tried to modify the code of not. Please, if you want to use the code, contact me for debugging it together :)
