from gotrue import SyncSupportedStorage
from flask import session

class FlaskSessionStorage(SyncSupportedStorage):
    def __init__(self):
        pass

    def get_item(self, key: str) -> str | None:
        return session.get(key)

    def set_item(self, key: str, value: str) -> None:
        session[key] = value

    def remove_item(self, key: str) -> None:
        session.pop(key, None)