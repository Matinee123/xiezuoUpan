import subprocess
import os
import time
import json
import urllib.request
import urllib.error
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
MODELS_DIR = HERE / "_models"
SERVER_EXE = MODELS_DIR / "llama-server.exe"
DEFAULT_PORT = 8088

local_process = None

def find_model():
    """在 _models/ 目录下查找 gguf 文件"""
    ggufs = list_models()
    return str(MODELS_DIR / ggufs[0]["file"]) if ggufs else None

def list_models():
    """列出所有可用的 gguf 模型"""
    if not MODELS_DIR.exists():
        return []
    result = []
    for f in sorted(MODELS_DIR.glob("*.gguf")):
        if f.name.startswith("mmproj-"):
            continue
        result.append({
            "file": f.name,
            "name": f.stem,
            "size_mb": round(f.stat().st_size / (1024*1024), 1)
        })
    return result

def is_running():
    """检查本地模型是否在运行且模型已加载"""
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{DEFAULT_PORT}/health", headers={"User-Agent": "LocalLLM"})
        resp = urllib.request.urlopen(req, timeout=3)
        data = resp.read().decode("utf-8", errors="replace")
        return '"ok"' in data or '"status"' in data
    except:
        return False

def start_server(model_path=None):
    """启动 llama-server"""
    global local_process
    if not model_path:
        model_path = find_model()
    if not model_path:
        return False, "未找到模型文件，请将 .gguf 文件放入 _models/ 目录"
    
    if is_running():
        return True, "本地模型已在运行"

    exe = str(SERVER_EXE)
    if not os.path.exists(exe):
        # Try system llama.cpp
        import shutil
        exe = shutil.which("llama-server.exe")
        if not exe:
            exe = shutil.which("llama-server")
        if not exe:
            return False, "未找到 llama-server，请放入 _models/ 目录"
    
    try:
        local_process = subprocess.Popen(
            [exe, "-m", model_path, "--port", str(DEFAULT_PORT), "--host", "127.0.0.1", "-ngl", "0"],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
            cwd=str(MODELS_DIR)
        )
        for _ in range(120):
            time.sleep(0.5)
            if local_process.poll() is not None:
                err = local_process.stderr.read().decode("utf-8", errors="replace").strip()
                return False, f"启动失败(进程退出): {err[:200]}"
            # 发真实请求确认模型能生成内容
            try:
                url = f"http://127.0.0.1:{DEFAULT_PORT}/v1/chat/completions"
                body = json.dumps({
                    "model": Path(model_path).stem,
                    "messages": [{"role":"user","content":"hi"}],
                    "max_tokens": 1
                }).encode()
                req = urllib.request.Request(url, data=body, headers={"Content-Type":"application/json"})
                resp = urllib.request.urlopen(req, timeout=5)
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("choices"):
                    return True, "本地模型已启动"
            except Exception:
                pass
        local_process.terminate()
        err = local_process.stderr.read().decode("utf-8", errors="replace").strip()
        return False, f"启动超时(60秒): {err[:200]}"
    except Exception as e:
        return False, f"启动失败: {e}"

def stop_server():
    """停止 llama-server"""
    global local_process
    if local_process:
        local_process.terminate()
        local_process = None
        return True
    return False

def model_info():
    """获取本地模型信息"""
    model_path = find_model()
    return {
        "available": bool(model_path),
        "model_path": model_path,
        "model_name": Path(model_path).stem if model_path else None,
        "running": is_running(),
        "port": DEFAULT_PORT
    }