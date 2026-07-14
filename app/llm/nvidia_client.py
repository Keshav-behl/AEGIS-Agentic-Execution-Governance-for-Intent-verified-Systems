from openai import OpenAI

from app import config

_clients: dict[str, OpenAI] = {}


def _get_client(api_key: str) -> OpenAI:
    if api_key not in _clients:
        _clients[api_key] = OpenAI(base_url=config.NVIDIA_BASE_URL, api_key=api_key)
    return _clients[api_key]


def chat(
    messages: list,
    model: str = config.NVIDIA_CHAT_MODEL,
    api_key: str = config.NVIDIA_API_KEY,
    json_mode: bool = False,
) -> str:
    kwargs = {}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = _get_client(api_key).chat.completions.create(
        model=model,
        messages=messages,
        **kwargs,
    )
    return response.choices[0].message.content
