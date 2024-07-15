import toml

class ServerConfig():
    def __init__(self, config_path: str) -> None:
        self._config = toml.load(config_path)

        self.ws_port = self._config["ws"]["port"]
        self.ws_host = self._config["ws"]["host"]

        self.twitch_secret = self._config["twitch"]["secret"]
        self.twitch_id = self._config["twitch"]["id"]
        self.twitch_update_delay = self._config["twitch"]["update_delay"]

        self.twitch_chat_buffer_size = self._config["buffers"]["chat"]
        self.twitch_sub_buffer_size = self._config["buffers"]["sub"]
        self.twitch_cheer_buffer_size = self._config["buffers"]["cheer"]
        
class APIConfig():
    def __init__(self, user_token: str, user_id: int, user_name: str, server_config: ServerConfig) -> None:
        self.user_token = user_token
        self.user_id = user_id
        self.user_name = user_name
        self.server_config = server_config