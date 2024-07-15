import asyncio
from typing import List, Dict
import logging
from fastsocket import Client, Message, TIMEOUT
import uuid

from .constants import *
from .utils import CircularBuffer, setup_logger
from .models import CCL

class TwitchClient:
    def __init__(self, url: str, buffer_size: int = 100, log_level=logging.INFO):
        self.ws = Client(url, log_level)
        self.token = None
        self.user_name = None
        self.connected = False
        self.chat_messages = CircularBuffer(buffer_size)
        self.cheers = CircularBuffer(buffer_size)
        self.subs = CircularBuffer(buffer_size)

    async def connect(self, user_name: str, token: str, channels: List[str]):
        self._logger, _ = setup_logger("Twitch Client")

        await self.ws.connect()
        
        await self.start_twitch_api(token, user_name)
        await self.set_channels(channels)

        self.connected = True

        self.ws.on_message(NEW_MESSAGES, self.handle_new_messages)
        self.ws.on_message(ERROR_TWITCH, self.handle_error)

    async def disconnect(self):
        if self.connected:
            await self.stop_twitch_api()
            await self.ws.disconnect()
            self.connected = False

    async def start_twitch_api(self, token, user_name) -> bool:
        msg = Message(uuid=int(uuid.uuid4()), code=START_TWITCH_API, data={"token": token, "user_name": user_name})
        res = await self.ws.send_msg(msg, blocking=True)
        if self.is_error(res):
            self._logger.error(f"An error occured: {res.code}")
            return False
        else:
            return True

    async def stop_twitch_api(self) -> bool:
        msg = Message(uuid=int(uuid.uuid4()),  code=STOP_TWITCH_API, data={})
        res = await self.ws.send_msg(msg, blocking=True)
        if self.is_error(res):
            self._logger.error(f"An error occured: {res.code}")
            return False
        else:
            return True

    async def get_status(self) -> bool:
        msg = Message(code=GET_STATUS)
        res = await self.ws.send_msg(msg, blocking=True)
        if self.is_error(res):
            self._logger.error(f"An error occured: {res.code}")
            return False
        else:
            return True

    async def set_channels(self, channels: List[str]) -> bool:
        msg = Message(code=SET_CHANNELS, data={"channels": channels})
        res = await self.ws.send_msg(msg, blocking=True)
        if self.is_error(res):
            self._logger.error(f"An error occured: {res.code}")
            return False
        else:
            return True

    async def update_stream(self, title: str, tags: List[str], ccl: CCL, game_id: str) -> bool:
        msg = Message(code=UPDATE_STREAM, data={
            "title": title,
            "tags": tags,
            "ccl": ccl.to_dict(),
            "game_id": game_id
        })
        res = await self.ws.send_msg(msg, blocking=True)
        if self.is_error(res):
            self._logger.error(f"An error occured: {res.code}")
            return False
        else:
            return True

    @staticmethod
    def is_error(res: Message):
        if res.code == ERROR_TWITCH or res.code == ERROR_TWITCH_API_NOT_CONNECTED or res.code == TIMEOUT:
            return True
        else:
            return False

    async def handle_new_messages(self, msg: Message):
        chat_messages = msg.data.get("chat", [])
        cheers = msg.data.get("cheers", [])
        subs = msg.data.get("subs", [])

        for chat_msg in chat_messages:
            self.chat_messages.append(chat_msg)

        for cheer in cheers:
            self.cheers.append(cheer)

        for sub in subs:
            self.subs.append(sub)
    
    def get_newest_messages(self):
        return {
            "chat": self.chat_messages.get_all(clear=True),
            "cheers": self.cheers.get_all(clear=True),
            "subs": self.subs.get_all(clear=True)
        }

    async def handle_error(self, msg: Message):
        self._logger.error(f"Error: {msg.data.get('info')} - {msg.data.get('error', '')}")
