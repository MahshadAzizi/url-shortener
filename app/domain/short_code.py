import secrets
import string

ALPHABET = string.ascii_letters + string.digits
DEFAULT_SHORT_CODE_LENGTH = 8


def generate_short_code(
        length: int = DEFAULT_SHORT_CODE_LENGTH,
) -> str:
    return "".join(
        secrets.choice(ALPHABET)
        for _ in range(length)
    )
