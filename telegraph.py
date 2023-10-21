import aiohttp
import json
import secrets
import datetime
from config import TELEGRAPH_TOKEN


class TelegraphPage:
    def __init__(self, called_function=None, params=None, result=None, url: str=None):
        self.result = self.to_format(result)
        self.params = self.to_format(params)
        self.called_function = called_function
        self.url = url

    def to_format(self, a):
        if isinstance(a, dict):
            a = json.dumps(a)
        else:
            a = str(a)
        return a

    async def post_telegraph_page(self):
        """
        Posts a page on Telegraph with the called function, parameters and result.
        :param self.called_function: The called function.
        :param self.params: The parameters of the function call. Data type: JSON str/str (in case of errors)
        :param self.result: The result of the function call. Data type: JSON str/str (in case of errors)
        :return: The URL of the Telegraph page.
        """
        if not self.called_function:
            return
        
        async with aiohttp.ClientSession() as session:
            response = await session.post(
                'https://api.telegra.ph/createPage',
                json={
                    "access_token": TELEGRAPH_TOKEN,
                    "title": f"Request #{secrets.token_hex(8)} ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})",
                    "author_name": "GPTModerBot",
                    "author_url": "https://telegram.me/GPTModerBot",
                    "content": [f"{self.called_function}\n\n{self.params}\n\n{self.result}"]
                }
            )
        data = await response.json()
        self.url = data["result"]["url"]
        return self.url


    async def read_telegraph_page(self):
        """
        Reads a Telegraph page and returns the called function, parameters and result.
        :param url: The URL of the Telegraph page.
        :return: The called function, parameters and result. Data type: str, dict/str (in case of errors), dict/str (in case of errors)
        """
        if not self.url:
            return
        
        async with aiohttp.ClientSession() as session:
            response = await session.get(f'https://api.telegra.ph/getPage/{self.url.split("/")[-1]}?return_content=true')
            data = await response.json()
            content = data['result']['content'][0]
            self.called_function, params, result = content.split('\n\n')
            
            try:
                self.params = json.loads(params)
            except json.JSONDecodeError:
                self.params = str(params)
            try:
                self.resul = json.loads(result)
            except json.JSONDecodeError:
                self.result = str(result)
            return self.called_function, self.params, self.result
