import secrets

from .user_sql import User


class Bind:
    def __init__(self):
        self.to_user: User = None
        self.origin_user: User = None
        self._key: str = str(secrets.token_hex(3))
