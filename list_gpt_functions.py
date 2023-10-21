# GPT-3 Functions List
gpt3_functions = [
    {
        "name": "getChatMemberCount",
        "description": "Get the number of members in the chat",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "setChatDescription",
        "description": "Change the description of the chat",
        "parameters": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "New chat description, 0-255 characters"
                }
            },
            "required": ["description"]
        }
    }
]

# GPT-3 Functions Set
gpt3_functions_set = {function['name'] for function in gpt3_functions}