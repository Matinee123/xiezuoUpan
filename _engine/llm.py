import json
import urllib.request
import urllib.error
import time

class LLMError(Exception):
    pass

def call_llm(messages, config, stream=False, temperature=0.7, max_tokens=4096):
    """调用 AI 模型，返回回复文本。本地引擎有自动重试机制。"""
    cfg = config.get_active_config()
    if not cfg or not cfg["api_key"]:
        raise LLMError("API Key 未配置，请编辑 .env.local 文件")

    if not cfg["model"]:
        raise LLMError("模型未配置")

    is_local = (config.engine == "local")
    max_retries = 3 if is_local else 1

    for attempt in range(max_retries):
        if attempt > 0:
            time.sleep(3)

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
            if is_local and attempt < max_retries - 1:
                continue
            raise LLMError(f"API 请求失败 (HTTP {e.code}): {body}")
        except urllib.error.URLError as e:
            if is_local and attempt < max_retries - 1:
                continue
            raise LLMError(f"网络连接失败: {e.reason}")

        body = resp.read().decode("utf-8", errors="replace")
        if not body:
            if is_local and attempt < max_retries - 1:
                continue
            raise LLMError("API 返回空响应，请检查接口地址是否正确")
        try:
            result = json.loads(body)
        except json.JSONDecodeError:
            if is_local and attempt < max_retries - 1:
                continue
            raise LLMError(f"API 返回格式异常: {body[:200]}")
        if "choices" not in result or not result["choices"]:
            if is_local and attempt < max_retries - 1:
                continue
            raise LLMError(f"API 返回异常: {json.dumps(result, ensure_ascii=False)}")

        content = result["choices"][0]["message"]["content"]
        if not content.strip() and is_local and attempt < max_retries - 1:
            continue

        return content

    raise LLMError("本地模型重试3次后仍返回空内容，请稍后重试")
