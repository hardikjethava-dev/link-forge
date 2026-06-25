import secrets
import string
from django.conf import settings

BASE62_ALPHABET = string.digits + string.ascii_lowercase + string.ascii_uppercase

def encode_base62(num: int) -> str:
    """
    Encodes an integer into a Base62 string.
    """
    if num < 0:
        raise ValueError("Cannot encode negative integers.")
    if num == 0:
        return BASE62_ALPHABET[0]
        
    base = len(BASE62_ALPHABET)
    arr = []
    while num:
        num, rem = divmod(num, base)
        arr.append(BASE62_ALPHABET[rem])
    arr.reverse()
    return ''.join(arr)

def decode_base62(s: str) -> int:
    """
    Decodes a Base62 string back into an integer.
    """
    if not s:
        raise ValueError("Cannot decode an empty string.")
        
    base = len(BASE62_ALPHABET)
    num = 0
    for char in s:
        if char not in BASE62_ALPHABET:
            raise ValueError(f"Invalid character '{char}' in Base62 string.")
        num = num * base + BASE62_ALPHABET.index(char)
    return num

def generate_random_code(length: int = None) -> str:
    """
    Generates a cryptographically secure random string of Base62 characters.
    """
    if length is None:
        length = getattr(settings, 'SHORT_CODE_LENGTH', 6)
    return ''.join(secrets.choice(BASE62_ALPHABET) for _ in range(length))

def generate_unique_short_code(model_class, length: int = None) -> str:
    """
    Generates a unique short code, checking against the database to prevent collisions.
    """
    max_attempts = 100
    for _ in range(max_attempts):
        code = generate_random_code(length)
        if not model_class.objects.filter(short_code=code).exists():
            return code
    raise ValueError("Could not generate a unique short code after 100 attempts.")
