import random
import string


class AuthToken(object):
    def __init__(self, email):
        self.email = email
        self.token = ''.join(
            random.choice(string.ascii_letters + string.hexdigits) for _ in range(20)
        )
