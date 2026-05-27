# -*- coding: utf-8 -*-
"""
AI 写作工作台 - 启动器
"""

import sys
import os
import threading
from pathlib import Path

HERE = Path(__file__).resolve().parent

def main():
    print()
    print("========================================")
    print("   AI 写作工作台 v1.0.0")
    print("========================================")
    print()

    # 进入项目目录
    os.chdir(str(HERE))
    sys.path.insert(0, str(HERE))

    # 检查依赖
    print("[1/3] 检查依赖库...")
    try:
        import docx
        print("  [OK] python-docx")
    except ImportError:
        print("  [..] python-docx 未安装")
    try:
        import reportlab
        print("  [OK] reportlab")
    except ImportError:
        print("  [..] reportlab 未安装")

    # 检测本地模型
    print()
    print("[1.5/3] 检测本地离线模型...")
    from _engine.local_llm import model_info, start_server
    info = model_info()
    if info["available"]:
        print(f"  [OK] 发现模型: {Path(info['model_path']).name}")
        ok, msg = start_server(info["model_path"])
        print(f"  [{('OK' if ok else '!!')}] {msg}")
        if ok:
            engine_changed = False
    else:
        print("  [..] 未发现离线模型，仅可使用云端引擎")
        print("  下载模型文件(.gguf)放入 _models/ 目录即可离线使用")

    # 检查配置
    print()
    print("[2/3] 检查配置...")
    from _engine.config import config
    print(f"  [OK] 引擎: {config.engine}")
    if not config.has_active_key():
        print("  [!!] API Key 未设置，将打开配置向导")
        need_setup = True
    else:
        need_setup = False

    # 启动服务
    print()
    print("[3/3] 启动服务...")
    from _engine.server import run_server
    port = config.port
    if need_setup:
        url = f"http://localhost:{port}/setup"
    else:
        url = f"http://localhost:{port}"
    threading.Thread(target=lambda: None, daemon=True).start()
    print(f"  [OK] 已启动 -> {url}")
    print("  按 Ctrl+C 停止")
    print()
    try:
        import webbrowser
        threading.Thread(target=webbrowser.open, args=(url,), daemon=True).start()
    except Exception:
        pass
    run_server(port)

if __name__ == "__main__":
    main()
