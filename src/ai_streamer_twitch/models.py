import time
import uuid
import twitchio
from twitchio.ext import pubsub

class CCL():
    def __init__(self, drugs=False,gambling=False,profanity=False,sexual=False,violent=False) -> None:
        self._drugs = drugs   
        self._gambling = gambling
        self._profanity = profanity
        self._sexual = sexual
        self._violent = violent

    def get_ccls(self):
        return [{"id": "DrugsIntoxication", "is_enabled": self._drugs},
                {"id": "Gambling", "is_enabled": self._gambling},
                {"id": "ProfanityVulgarity", "is_enabled": self._profanity},
                {"id": "SexualThemes", "is_enabled": self._sexual},
                {"id": "ViolentGraphic", "is_enabled": self._violent}]

    @classmethod
    def from_dict(cls, data: dict):
        obj = cls(
            drugs=data["drugs"],
            gambling=data["gambling"],
            profanity=data["profanity"],
            sexual=data["sexual"],
            violent=data["violent"]
        )
        return obj

    def to_dict(self) -> dict:
        return {
            "drugs": self._drugs,
            "gambling": self._gambling,
            "profanity": self._profanity,
            "sexual": self._sexual,
            "violent": self._violent
        }

class ChatMessage():
    def __init__(self, user_name: str, user_id: int, content: str) -> None:
        self.user_name = user_name
        self.user_id = user_id
        self.content = content
        self.timestamp = time.time()
        self.uuid = str(uuid.uuid4())

    def to_dict(self) -> dict:
        return {
                "user_name": self.user_name,
                "user_id": self.user_id,
                "content": self.content,
                "timestamp": self.timestamp,
                "uuid": self.uuid,
        }

    @classmethod
    def from_dict(cls, data: dict):
        obj = cls(
            user_name=data["user_name"],
            user_id=data["user_id"],
            content=data["content"]
        )
        obj.timestamp = data["timestamp"]
        obj.uuid = data["uuid"]
        return obj

    @classmethod
    def from_twitch_msg(cls, msg: twitchio.Message):
        obj = cls(
            user_name=msg.author.display_name,
            user_id=msg.author.id,
            content=msg.content
        )
        return obj
    
class SubMessage():
    def __init__(self, user_name: str, user_id: int, content: str, months: int, is_gift: bool, is_anon: bool, gift_amount:int = 0) -> None:
        self.is_anon = is_anon
        self.user_name = user_name
        self.user_id = user_id
        self.content = content
        self.months = months
        self.is_gift = is_gift
        self.gift_amount = gift_amount
        self.timestamp = time.time()
        self.uuid = str(uuid.uuid4())
    
    def to_dict(self) -> dict:
        return {
                "user_name": self.user_name,
                "user_id": self.user_id,
                "content": self.content,
                "timestamp": self.timestamp,
                "uuid": self.uuid,
                "is_anon": self.is_anon,
                "months": self.months,
                "is_gift": self.is_gift,
                "gift_amount": self.gift_amount
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        obj = cls(
            is_anon=data["is_anon"],
            user_name=data["user_name"],
            user_id=data["user_id"],
            content=data["content"],
            months=data["months"],
            is_gift=data["is_gift"],
            gift_amount=data["gift_amount"]
        )
        obj.timestamp = data["timestamp"]
        obj.uuid = data["uuid"]
        return obj
    
    @classmethod
    def from_event(cls, event: pubsub.PubSubChannelSubscribe):
        obj = cls(
            is_anon=True if event.user is None else False,
            user_name="Anon" if event.user is None else event.user.name,
            user_id=-1 if event.user is None else event.user.id,
            content=event.message,
            months=event.cumulative_months,
            is_gift=event.is_gift,
            gift_amount=0
        )
        return obj

class CheerMessage():
    def __init__(self, is_anon: bool, user_name: str, user_id: int, content: str, amount: int) -> None:
        self.is_anon = is_anon
        self.user_name = user_name
        self.user_id = user_id
        self.content = content
        self.amount = amount
        self.timestamp = time.time()
        self.uuid = int(uuid.uuid4())
    
    def to_dict(self) -> dict:
        return {
            "is_anon": self.is_anon,
            "user_name": self.user_name,
            "user_id": self.user_id,
            "content": self.content,
            "amount": self.amount,
            "timestamp": self.timestamp,
            "uuid": self.uuid
        }

    @classmethod
    def from_dict(cls, data: dict):
        obj = cls(
            is_anon=data["is_anon"],
            user_name=data["user_name"],
            user_id=data["user_id"],
            content=data["content"],
            amount=data["amount"],
        )
        obj.timestamp = data["timestamp"]
        obj.uuid = data["uuid"]
        return obj
    
    @classmethod
    def from_event(cls, event: pubsub.PubSubBitsMessage):
        obj = cls(
            is_anon=True if event.user is None else False,
            user_name="Anon" if event.user is None else event.user.name,
            user_id=-1 if event.user is None else event.user.id,
            content=event.message,
            amount=event.bits_used
        )
        return obj