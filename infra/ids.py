import random
import string


_ALPHABET = string.ascii_letters + string.digits  # a-z A-Z 0-9


def generate_id(length: int = 8) -> str:
    """
    Generates a short, URL-safe share ID (e.g. "xK9mPq2R").
    Person 2 calls this when handling POST /generate to create the job_id.

    Example:
        from infra import generate_id
        job_id = generate_id()  # "xK9mPq2R"
    """
    return "".join(random.choices(_ALPHABET, k=length))
