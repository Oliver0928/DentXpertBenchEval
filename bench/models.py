import json
import urllib.request
from typing import Any


def chat_completion(
    messages: list[dict[str, Any]],
    model: str,
    api_key: str | None,
    base_url: str,
    temperature: float,
    max_tokens: int,
    timeout: int,
    extra_body: dict[str, Any] | None = None,
) -> str:
    '''
    构造请求、发送请求、解析响应，返回模型的回答
    '''
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if extra_body:
        payload.update(extra_body)
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = urllib.request.Request(
        url,
        data=body,
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]

