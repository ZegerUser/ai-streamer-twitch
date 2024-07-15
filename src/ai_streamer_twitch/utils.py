import logging
import json
import aiohttp

def setup_logger(name, level=logging.INFO):
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(stream_handler)
    
    return logger, stream_handler

class CircularBuffer():
    def __init__(self, max_elems: int) -> None:
        self._array = []
        self._max_elems = max_elems

    def append(self, elem):
        if len(self._array) == self._max_elems:
            self._array.pop(0)
        self._array.append(elem)
    
    def get_all(self, clear=False):
        out_arr = self._array
        if clear: 
            self._array = []
        return out_arr
    
    def __len__(self):
        return len(self._array)

GRANT_TYPE = 'client_credentials'

async def get_channel_id_from_name(client_id, client_secret, channel_name):
    async with aiohttp.ClientSession() as session:
        # Get access token using app authentication exchange
        token_url = 'https://id.twitch.tv/oauth2/token'
        payload = {
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': GRANT_TYPE,
        }
        async with session.post(token_url, data=payload) as response:
            response_text = await response.text()
            access_token = json.loads(response_text)['access_token']

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Client-Id': client_id,
        }

        # Get channel ID
        user_url = f'https://api.twitch.tv/helix/users?login={channel_name}'
        async with session.get(user_url, headers=headers) as response:
            response_text = await response.text()
            data = json.loads(response_text)
            if response.status == 200:
                return int(data["data"][0]["id"])

async def get_channel_name_from_id(client_id, client_secret, channel_id):
    async with aiohttp.ClientSession() as session:
        # Get access token using app authentication exchange
        token_url = 'https://id.twitch.tv/oauth2/token'
        payload = {
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': GRANT_TYPE,
        }
        async with session.post(token_url, data=payload) as response:
            response_text = await response.text()
            access_token = json.loads(response_text)['access_token']

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Client-Id': client_id,
        }

        # Get channel ID
        url = f'https://api.twitch.tv/helix/channels?broadcaster_id={channel_id}'
        async with session.get(url, headers=headers) as response:
            response_text = await response.text()
            data = json.loads(response_text)
            if response.status == 200:
                return data['data'][0]['broadcaster_name']