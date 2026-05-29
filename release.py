#!/usr/bin/env python3
"""发布脚本：自动更新版本号 + 生成 zip"""
import subprocess, json, zipfile, os, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# 1. 读取 git tag 获取版本号
try:
    tag = subprocess.check_output(["git","describe","--tags","--abbrev=0"], cwd=str(HERE),
                                   stderr=subprocess.DEVNULL).decode().strip()
except Exception:
    tag = input("请输入版本号 (如 v1.2.3): ").strip()
version = tag.lstrip("v")

# 2. 更新 version.json
ver_file = HERE / "version.json"
with open(ver_file, "r", encoding="utf-8") as f:
    data = json.load(f)
data["version"] = version
data["build"] = int(version.split(".")[-1]) if version.count(".") == 2 else 0
with open(ver_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
    f.write("\n")
print(f"[OK] version.json -> {version}")

# 3. 生成 zip
exclude = ["_env", "_data", "_backup", "__pycache__", ".git", "exports", "_models"]
exclude_files = [".env.local", "xiezuoUpan.zip"]
zip_path = HERE / "xiezuoUpan.zip"
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(str(HERE)):
        dirs[:] = [d for d in dirs if d not in exclude and not d.startswith(".git")]
        for f in files:
            if f.endswith(".pyc") or f in exclude_files:
                continue
            path = os.path.join(root, f)
            rel = os.path.relpath(path, str(HERE))
            zf.write(path, rel)
    count = len(zf.namelist())
size_kb = round(zip_path.stat().st_size / 1024, 1)
print(f"[OK] xiezuoUpan.zip: {count} files, {size_kb} KB")

print(f"\n准备就绪！运行:  git commit -m 'v{version}' && git tag v{version} && git push --tags")