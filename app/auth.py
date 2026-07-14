from app import config


def identify_requester(api_key: str | None) -> str | None:
    if not api_key:
        return None
    return config.AEGIS_API_KEYS.get(api_key)
