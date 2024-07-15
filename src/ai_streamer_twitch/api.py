import asyncio
import uuid
import logging

import twitchio
from twitchio.ext import pubsub

from .config import APIConfig
from .utils import setup_logger, CircularBuffer
from .models import ChatMessage, CCL, CheerMessage, SubMessage

class API():
    def __init__(self, config: APIConfig, log_level=logging.DEBUG) -> None:
        self._config = config

        self._logger, self._stream_hndl = setup_logger("TwitchAPI", log_level)

        self._twitch_client = None
        self._pubsub = None
        self._user = None

        self._chat_buffer = CircularBuffer(self._config.server_config.twitch_chat_buffer_size)
        self._sub_buffer = CircularBuffer(self._config.server_config.twitch_sub_buffer_size)
        self._cheer_buffer = CircularBuffer(self._config.server_config.twitch_cheer_buffer_size)

        self.started_raid = False

    async def close(self):
        self._logger.info("Closing Twitch API")
        await self._twitch_client.close()
        self._logger.info("Closed Twitch API")
        self._logger.removeHandler(self._stream_hndl)

    async def start(self):
        self._logger.info("Starting Twitch API")
        client = twitchio.Client(self._config.user_token)
        pubsub_api = pubsub.PubSubPool(client)
        user = client.create_user(self._config.user_id, self._config.user_name)

        @client.event()
        async def event_message(msg: twitchio.Message):
            cm = ChatMessage.from_twitch_msg(msg)
            self._chat_buffer.append(cm)
            self._logger.debug(f"Got Chat Message: {cm.to_dict()}")

        @client.event()
        async def event_pubsub_subscriptions(event: pubsub.PubSubChannelSubscribe):
            cm = SubMessage.from_event(event)
            self._sub_buffer.append(cm)
            self._logger.debug(f"Got Chat Message: {cm.to_dict()}")

        @client.event()
        async def event_pubsub_bits(event: pubsub.PubSubBitsMessage):
            cm = CheerMessage.from_event(event)
            self._cheer_buffer.append(cm)
            self._logger.debug(f"Got Chat Message: {cm.to_dict()}")
        
        pubsub_topics = [
            pubsub.bits(self._config.user_token)[self._config.user_id],
            pubsub.channel_subscriptions(self._config.user_token)[self._config.user_id]
        ]
        await pubsub_api.subscribe_topics(pubsub_topics)
        await client.connect()

        self._twitch_client = client
        self._pubsub = pubsub_api
        self._user = user

        self._logger.info("Started Twitch API")
    
    def get_chat_messages(self, clear=True) -> list[ChatMessage]:
        return self._chat_buffer.get_all(clear=clear)
    
    def get_bits(self, clear=True) -> list[CheerMessage]:
        return self._cheer_buffer.get_all(clear=clear)
    
    def get_subs(self, clear=True) -> list[SubMessage]:
        return self._sub_buffer.get_all(clear=clear) 

    async def set_channels(self, channels):
        await self._twitch_client.join_channels(channels)
    
    async def update_stream(self, title: str, tags:list[str], ccl:CCL = CCL(), game_id:int=509658):
        await self._user.modify_stream(
            self._config.user_token,
            game_id=game_id,
            content_classification_labels=ccl.get_ccls(),
            title=title,
            tags=tags
        )
    
    async def start_raid(self, channel_id: int):
        self._user.start_raid(self._config.user_token, channel_id)
    
    async def stop_raid(self):
        self._user.cancel_raid(self._config.user_token)
    
    def get_conncted_channels(self):
        return self._twitch_client.connected_channels

    def get_info(self):
        return {
            "connected_channels": self._twitch_client.connected_channels
        }