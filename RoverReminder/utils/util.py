import random
import string

import httpx


async def get_public_ip(host: str = "127.127.127.127") -> str:
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get("https://event.kurobbs.com/event/ip", timeout=4)
            return r.text
    except Exception:
        pass

    try:
        async with httpx.AsyncClient() as client:
            r = await client.get("https://api.ipify.org/?format=json", timeout=4)
            return r.json()["ip"]
    except Exception:
        pass

    try:
        async with httpx.AsyncClient() as client:
            r = await client.get("https://httpbin.org/ip", timeout=4)
            return r.json()["origin"]
    except Exception:
        pass

    return host


def generate_random_string(length: int = 32) -> str:
    characters = string.ascii_letters + string.digits + string.punctuation
    return "".join(random.choice(characters) for _ in range(length))
