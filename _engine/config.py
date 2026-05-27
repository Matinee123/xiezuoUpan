import os
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
ENV_FILE = HERE / ".env.local"

class Config:
    def __init__(self):
        self.engine = "deepseek"
        self.deepseek_api_key = ""
        self.deepseek_base_url = "https://api.deepseek.com"
        self.openai_api_key = ""
        self.openai_base_url = "https://api.openai.com/v1"
        self.ollama_base_url = "http://localhost:11434/v1"
        self.ollama_model = "qwen2.5:latest"
        self.custom_api_key = ""
        self.custom_base_url = ""
        self.custom_model = ""
        self.port = 8080
        self.load()

    def load(self):
        if not ENV_FILE.exists():
            self._create_default_env()
            return
        lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip().upper()
            value = value.strip().strip("\"'")
            if key == "ENGINE":
                self.engine = value.lower()
            elif key == "DEEPSEEK_API_KEY":
                self.deepseek_api_key = value
            elif key == "DEEPSEEK_BASE_URL":
                self.deepseek_base_url = value
            elif key == "OPENAI_API_KEY":
                self.openai_api_key = value
            elif key == "OPENAI_BASE_URL":
                self.openai_base_url = value
            elif key == "OLLAMA_BASE_URL":
                self.ollama_base_url = value
            elif key == "OLLAMA_MODEL":
                self.ollama_model = value
            elif key == "CUSTOM_API_KEY":
                self.custom_api_key = value
            elif key == "CUSTOM_BASE_URL":
                self.custom_base_url = value
            elif key == "CUSTOM_MODEL":
                self.custom_model = value
            elif key == "PORT":
                try:
                    self.port = int(value)
                except ValueError:
                    pass

    def _create_default_env(self):
        template = """# AI 写作工作台 - 配置
# 不使用的项目留空即可

# 引擎选择: deepseek / openai / ollama / custom
ENGINE=deepseek

# DeepSeek (默认，中文写作首选)
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com

# OpenAI 兼容 (支持 GPT、Claude 等)
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1

# Ollama 本地模型 (离线使用)
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=qwen2.5:latest

# 自定义 API (任何兼容 OpenAI 接口的服务)
CUSTOM_API_KEY=
CUSTOM_BASE_URL=
CUSTOM_MODEL=

# 服务端口
PORT=8080
"""
        ENV_FILE.write_text(template, encoding="utf-8")
        print(f"[config] 已创建默认配置文件: {ENV_FILE}")

    def get_active_config(self):
        if self.engine == "deepseek":
            return {
                "api_key": self.deepseek_api_key,
                "base_url": self.deepseek_base_url,
                "model": "deepseek-chat"
            }
        elif self.engine == "openai":
            return {
                "api_key": self.openai_api_key,
                "base_url": self.openai_base_url,
                "model": "gpt-4o-mini"
            }
        elif self.engine == "ollama":
            return {
                "api_key": "ollama",
                "base_url": self.ollama_base_url,
                "model": self.ollama_model
            }
        elif self.engine == "custom":
            return {
                "api_key": self.custom_api_key,
                "base_url": self.custom_base_url,
                "model": self.custom_model
            }
        return None

config = Config()
