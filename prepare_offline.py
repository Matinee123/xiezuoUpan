#!/usr/bin/env python3
"""
离线分发准备工具
一键下载所有依赖到 U盘，用户拿到后完全无需联网
"""

import os, sys, zipfile, urllib.request, time, shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENV_DIR = HERE / "_env"
MODELS_DIR = HERE / "_models"

# ====== 下载源 ======
PYTHON_URL = "https://www.python.org/ftp/python/3.12.3/python-3.12.3-embed-amd64.zip"
GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py"
LLAMA_URL = "https://github.com/ggml-org/llama.cpp/releases/download/b9370/llama-b9370-bin-win-cpu-x64.zip"
MODEL_URL = "https://modelscope.cn/models/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/master/qwen2.5-1.5b-instruct-q4_k_m.gguf"

def download(url, dest, desc):
    """下载文件并显示进度"""
    if dest.exists():
        size_mb = round(dest.stat().st_size / (1024*1024), 1)
        print(f"  [SKIP] {desc} 已存在 ({size_mb}MB)")
        return True
    print(f"  [DOWNLOAD] {desc}...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Prepare-Offline"})
        resp = urllib.request.urlopen(req, timeout=1800)
        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f:
            while True:
                chunk = resp.read(8192)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = int(downloaded / total * 100)
                    mb = round(downloaded / (1024*1024), 1)
                    total_mb = round(total / (1024*1024), 1)
                    print(f"\r    {mb}/{total_mb}MB ({pct}%)", end="", flush=True)
        print()
        return True
    except Exception as e:
        print(f"\n  [FAIL] {e}")
        if dest.exists():
            dest.unlink()
        return False

def main():
    print()
    print("=" * 60)
    print("  AI 写作工作台 - 离线分发准备工具")
    print("=" * 60)
    print()
    print("此工具将下载所有依赖到 U盘，完成后用户无需联网即可使用。")
    print("需要联网下载约 1.1GB 文件。")
    print()

    ok = 0
    total = 4

    # Step 1: Python
    print(f"[1/{total}] Python 运行环境 (60MB)")
    temp_zip = ENV_DIR / "python.zip"
    if download(PYTHON_URL, temp_zip, "Python embeddable"):
        if not (ENV_DIR / "python.exe").exists():
            print("  解压中...")
            with zipfile.ZipFile(temp_zip, "r") as zf:
                zf.extractall(ENV_DIR)
            temp_zip.unlink()
        ok += 1

    # Step 2: pip
    print(f"\n[2/{total}] pip 包管理器")
    pip_path = ENV_DIR / "get-pip.py"
    if download(GET_PIP_URL, pip_path, "get-pip"):
        python_exe = str(ENV_DIR / "python.exe")
        if os.path.exists(python_exe):
            import subprocess
            subprocess.run([python_exe, str(pip_path)], capture_output=True, timeout=60)
            subprocess.run([python_exe, "-m", "pip", "install", "python-docx", "reportlab"],
                         capture_output=True, timeout=120)
            pip_path.unlink()
        ok += 1

    # Step 3: llama-server
    print(f"\n[3/{total}] llama.cpp 推理引擎 (50MB)")
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    llama_zip = MODELS_DIR / "llama_temp.zip"
    if download(LLAMA_URL, llama_zip, "llama.cpp"):
        if not (MODELS_DIR / "llama-server.exe").exists():
            print("  解压中...")
            with zipfile.ZipFile(llama_zip, "r") as zf:
                zf.extractall(MODELS_DIR)
            llama_zip.unlink()
        ok += 1

    # Step 4: Model
    print(f"\n[4/{total}] Qwen2.5-1.5B 离线大模型 (1GB)")
    model_path = MODELS_DIR / "qwen2.5-1.5b-instruct-q4_k_m.gguf"
    if download(MODEL_URL, model_path, "Qwen2.5-1.5B-Q4_K_M"):
        ok += 1

    print()
    if ok == total:
        print("=" * 60)
        print(f"  ✅ 全部完成！{ok}/{total} 项已就绪")
        print(f"  总大小: ~1.1GB")
        print(f"  U盘已可拔下分发，用户插上即用！")
        print("=" * 60)
    else:
        print(f"  ⚠️ {ok}/{total} 项完成，{total - ok} 项失败。重试即可。")

if __name__ == "__main__":
    main()