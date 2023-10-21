import aiohttp
import json
import secrets
import datetime
from config import telegraph_token


async def post_telegraph_page(called_function, params, result):
    """
    Posts a page on Telegraph with the called function, parameters and result.
    :param called_function: The called function.
    :param params: The parameters of the function call.
    :param result: The result of the function call.
    :return: The URL of the Telegraph page.
    """
    if isinstance(params, dict):
        params = json.dumps(params)
    if isinstance(result, dict):
        result = json.dumps(result)
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
        return data["result"]["url"]


async def read_telegraph_page(url):
    """
    Reads a Telegraph page and returns the called function, parameters and result.
    :param url: The URL of the Telegraph page.
    :return: The called function, parameters and result. Data type: str, str (JSON), str.
    """
    async with aiohttp.ClientSession() as session:
        response = await session.get(f'https://api.telegra.ph/getPage/{url.split("/")[-1]}?return_content=true')
        data = await response.json()
        content = data['result']['content'][0]
        called_function, params, result = content.split('\n\n')
        
        try:
            params = json.loads(params)
        except json.JSONDecodeError:
            params = str(params)
        try:
            result = json.loads(result)
        except json.JSONDecodeError:
            result = str(result)
        return called_function, params, result
