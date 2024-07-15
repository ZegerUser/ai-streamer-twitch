import logging
import uuid
import asyncio

from fastsocket import Server, Message

from .constants import *
from .api import API
from .config import ServerConfig, APIConfig
from .utils import setup_logger, get_channel_id_from_name
from .models import CCL

class Service():
    def __init__(self, config: ServerConfig, log_level=logging.DEBUG) -> None:
        self._config = config

        self._logger, _ = setup_logger("Twitch WS", level=log_level)

        self._ws = Server(
            self._config.ws_host,
            self._config.ws_port,
            log_level=log_level
        )

        self._ws.on_message(START_TWITCH_API, self.start_twitch_api)
        self._ws.on_message(STOP_TWITCH_API, self.stop_twitch_api)
        self._ws.on_message(GET_STATUS, self.get_status)
        self._ws.on_message(GET_ID_FROM_USER, self.get_id_from_user)
        self._ws.on_message(SET_CHANNELS, self.set_channels)
        self._ws.on_message(UPDATE_STREAM, self.update_stream)

        self._api = None

    async def start_twitch_api(self, msg: Message, ws):
        self._logger.debug("Got Request to start twitch API")
        
        if self._api is not None:
            self._logger.error("Twitch API Already started!")
            msg = Message(uuid=msg.uuid, code=ERROR_TWITCH, data={"info": "Twitch API Already started!"})
            await ws.send(msg.to_json())
            return

        if "token" not in msg.data.keys() or "user_name" not in msg.data.keys():
            self._logger.error("token or user_name not in data!")
            msg = Message(uuid=msg.uuid, code=ERROR_TWITCH, data={"info": "token or user_name not in data!"})
            await ws.send(msg.to_json())
            return

        try:
            user_id = await get_channel_id_from_name(
                self._config.twitch_id,
                self._config.twitch_secret,
                msg.data["user_name"]
            )
        except Exception as e:
            self._logger.error(e)
            msg = Message(uuid=msg.uuid, code=ERROR_TWITCH, data={"info": "Could not get user id from username", "error": str(e)})
            ws.send(msg.to_json())
            return

        try:
            api = API(APIConfig(
                msg.data["token"],
                user_id,
                msg.data["user_name"],
                self._config
            ))
            await api.start()
            self._api = api

            msg = Message(uuid=msg.uuid, code=START_TWITCH_API, data={})
            await ws.send(msg.to_json())

        except Exception as e:
            self._logger.error(e)
            msg = Message(uuid=msg.uuid, code=ERROR_TWITCH, data={"info": "Could not start twitch API", "error": str(e)})
            await ws.send(msg.to_json())
            return

    async def stop_twitch_api(self, msg: Message, ws):
        self._logger.debug("Requested stop twitch api")

        if self._api is None:
            self._logger.error("twitch API Not Connected")
            msg = Message(uuid=msg.uuid, code=ERROR_TWITCH_API_NOT_CONNECTED, data={})
            await ws.send(msg.to_json())
            return
        
        await self._api.close()
        self._api = None

        msg = Message(uuid=msg.uuid, code=STOP_TWITCH_API, data={})
        await ws.send(msg.to_json())

    async def get_status(self, msg: Message, ws):
        self._logger.debug("Requested status")

        if self._api is None:
            self._logger.error("twitch API Not Connected")
            msg = Message(uuid=msg.uuid, code=ERROR_TWITCH_API_NOT_CONNECTED, data={})
            await ws.send(msg.to_json())
            return

        info = self._api.get_info()
        msg = Message(uuid=msg.uuid, code=GET_STATUS, data=info)
        await ws.send(msg.to_json())

    async def get_id_from_user(self, msg: Message, ws):
        self._logger.debug("Requested id from user")

        if "user_name" not in msg.data.keys():
            self._logger.error("twitch API Not Connected")
            msg = Message(uuid=msg.uuid, code=ERROR_TWITCH, data={"info": "user_name not in data"})
            await ws.send(msg.to_json())
        try:
            user_id = await get_channel_id_from_name(
                self._config.twitch_id,
                self._config.twitch_secret,
                msg.data["user_name"]
            )
            msg = Message(uuid=msg.uuid, code=GET_ID_FROM_USER, data={"user_id": user_id, "user_name": msg.data["user_name"]})
            await ws.send(msg.to_json())

        except Exception as e:
            self._logger.error(e)
            msg = Message(uuid=msg.uuid, code=ERROR_TWITCH, data={"info": "Could not get user id from username", "error": str(e)})

    async def set_channels(self, msg: Message, ws):
        self._logger.debug("Requested set new channels")
        if self._api is None:
            msg = Message(uuid=msg.uuid, code=ERROR_TWITCH_API_NOT_CONNECTED, data={})
            await ws.send(msg.to_json())
            return

        if "channels" not in msg.data.keys():
            msg = Message(uuid=msg.uuid, code=ERROR_TWITCH, data={"info": "channels not in data!"})
            await ws.send(msg.to_json())
            return
        
        await self._api.set_channels(msg.data["channels"])
        msg = Message(uuid=msg.uuid, code=SET_CHANNELS, data={})
        await ws.send(msg.to_json())

    async def update_stream(self, msg: Message, ws):
        self._logger.debug("Requested update stream")
        if self._api is None:
            msg = Message(uuid=msg.uuid, code=ERROR_TWITCH_API_NOT_CONNECTED, data={})
            await ws.send(msg.to_json())
            return

        if "title" not in msg.data.keys() or "tags" not in msg.data.keys() or "ccl" not in msg.data.keys() or "game_id" not in msg.data.keys():
            msg = Message(uuid=msg.uuid, code=ERROR_TWITCH, data={"info": "title, tags, ccl or game_id not in data!"})
            await ws.send(msg.to_json())
            return
        try:
            self._api.update_stream(
                msg.data["title"],
                msg.data["tags"],
                ccl=CCL.from_dict(msg.data["ccl"]),
                game_id=msg.data["game_id"]
            )
        except Exception as e:
            self._logger.error(e)
            msg = Message(uuid=msg.uuid, code=ERROR_TWITCH, data={"info": "could not update stream", "error": str(e)})
            await ws.send(msg.to_json())
        
        msg = Message(uuid=msg.uuid, code=UPDATE_STREAM, data={})
        await ws.send(msg.to_json())

    async def client_updater_loop(self):
        while True:
            if self._api is None:
                new_chats = {}
                new_subs = {}
                new_cheers = {}
            else:
                new_chats = [x.to_dict() for x in self._api.get_chat_messages()]
                new_subs = [x.to_dict() for x in self._api.get_subs()]
                new_cheers = [x.to_dict() for x in  self._api.get_bits()]

            msg = Message(uuid=int(uuid.uuid4()), code=NEW_MESSAGES, data={
                "chat": new_chats,
                "cheers": new_cheers,
                "subs": new_subs
            })
            await self._ws.send_msg(msg)
            await asyncio.sleep(self._config.twitch_update_delay)

    async def start(self):
        await self._ws.start()
        asyncio.create_task(self.client_updater_loop())
    
    async def stop(self):
        await self._ws.stop()
        asyncio.get_running_loop().stop()