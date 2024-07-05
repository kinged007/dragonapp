import string
import secrets

def create_random_key(length: int = 5) -> str:
    chars = string.ascii_uppercase + string.digits + string.ascii_lowercase
    return "".join(secrets.choice(chars) for _ in range(length))
