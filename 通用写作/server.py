#!/usr/bin/env python3
"""通用写作版 - 入口"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from _engine.server import run_server, APIHandler
from _engine.config import config

def main():
    port = 8080
    print(f"[通用写作] 版本: v1.0.0")
    print(f"[通用写作] 引擎: {config.engine}")
    print(f"[通用写作] 请在浏览器打开 http://localhost:{port}")
    run_server(port)

if __name__ == "__main__":
    main()
