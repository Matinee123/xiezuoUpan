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
