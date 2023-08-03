import secrets


class Bind:
    def __init__(self):
        self.to_ = None
        self.origin_ = None
        self._key: str = str(secrets.token_hex(3))


class Group:
    def __init__(self, available, group):
        self.available: bool = available
        self.result = group


class User:
    def __init__(self, available, user):
        self.available: bool = available
        self.result = user
