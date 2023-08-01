import secrets
import time

from .user_sql import User


class Bind:
    def __init__(self, user: User):
        self.user: User = user
        self.orgin_user: User = None
        self.params: dict = {}
        self._key: str = str(secrets.token_hex(3))
        self.finished: bool = False
        self.create_time: float = time.time()
