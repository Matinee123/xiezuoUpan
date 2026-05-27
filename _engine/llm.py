import json
import urllib.request
import urllib.error

class LLMError(Exception):
    pass

def call_llm(messages, config, stream=False, temperature=0.7, max_tokens=4096):
    """调用 AI 模型，返回回复文本"""
    cfg = config.get_active_config()
    if not cfg or not cfg["api_key"]:
        raise LLMError("API Key 未配置，请编辑 .env.local 文件")

    if not cfg["model"]:
        raise LLMError("模型未配置")

    url = cfg["base_url"].rstrip("/") + "/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {cfg['api_key']}"
    }
    payload = {
        "model": cfg["model"],
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": stream
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=120)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise LLMError(f"API 请求失败 (HTTP {e.code}): {body}")
    except urllib.error.URLError as e:
        raise LLMError(f"网络连接失败: {e.reason}")

    body = resp.read().decode("utf-8")
    if not body:
        raise LLMError("API 返回空响应，请检查接口地址是否正确")
    try:
        result = json.loads(body)
    except json.JSONDecodeError:
        raise LLMError(f"API 返回格式异常: {body[:200]}")
    if "choices" not in result or not result["choices"]:
        raise LLMError(f"API 返回异常: {json.dumps(result, ensure_ascii=False)}")

    return result["choices"][0]["message"]["content"]
