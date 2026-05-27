import subprocess
import os
import time
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
    if not MODELS_DIR.exists():
        return None
    ggufs = sorted(MODELS_DIR.glob("*.gguf"))
    return str(ggufs[0]) if ggufs else None

def is_running():
    """检查本地模型是否在运行"""
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{DEFAULT_PORT}/health", headers={"User-Agent": "LocalLLM"})
        urllib.request.urlopen(req, timeout=2)
        return True
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
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        # Wait for server to be ready
        for _ in range(30):
            time.sleep(0.5)
            if is_running():
                return True, f"本地模型已启动 (端口 {DEFAULT_PORT})"
        return False, "模型启动超时"
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