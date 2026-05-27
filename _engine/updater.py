import json
import zipfile
import shutil
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
VERSION_FILE = HERE / "version.json"
BACKUP_DIR = HERE / "_backup"
GITHUB_API = "https://api.github.com/repos/Matinee123/xiezuoUpan/releases/latest"
PROTECTED = [".env.local", "_data", "_backup", "_env", "version.json"]

def get_current_version():
    """读取当前版本号"""
    if not VERSION_FILE.exists():
        return "1.0.0"
    data = json.loads(VERSION_FILE.read_text(encoding="utf-8-sig"))
    return data.get("version", "1.0.0")

def check_update():
    """检查 GitHub 是否有新版本"""
    current = get_current_version()

    try:
        req = urllib.request.Request(GITHUB_API, headers={"User-Agent": "AI-Writing-Workstation"})
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read().decode())
        latest = data.get("tag_name", "").lstrip("v")

        if latest == current:
            return {"has_update": False, "current": current, "latest": latest, "message": "已是最新版本"}

        # Find changelog from release body
        changelog = data.get("body", f"版本 {latest}")
        # Find zip asset
        download_url = None
        for asset in data.get("assets", []):
            if asset.get("name", "").endswith(".zip"):
                download_url = asset.get("browser_download_url")
                break
        # Fallback: use source zip
        if not download_url:
            download_url = data.get("zipball_url", "")

        return {
            "has_update": True,
            "current": current,
            "latest": latest,
            "changelog": changelog,
            "download_url": download_url,
            "release_url": data.get("html_url", "")
        }
    except Exception as e:
        return {"has_update": False, "current": current, "error": str(e), "message": "检查更新失败，请确保有网络连接"}

def backup_protected():
    """备份用户数据"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backed = []
    for name in PROTECTED:
        src = HERE / name
        if src.exists():
            dst = BACKUP_DIR / name
            if src.is_dir():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
            backed.append(name)
    return backed

def apply_update(download_url):
    """下载并应用更新"""
    # Backup first
    backed = backup_protected()

    # Download
    zip_path = HERE / "_upgrade_tmp.zip"
    extract_dir = HERE / "_upgrade_tmp"

    try:
        req = urllib.request.Request(download_url, headers={"User-Agent": "AI-Writing-Workstation"})
        resp = urllib.request.urlopen(req, timeout=300)
        zip_path.write_bytes(resp.read())
    except Exception as e:
        return {"ok": False, "error": f"下载失败: {e}", "stage": "download"}

    # Extract
    extract_dir.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            # GitHub zip is wrapped in a root folder, detect it
            members = zf.namelist()
            prefix = ""
            if members and "/" in members[0]:
                prefix = members[0].split("/")[0] + "/"
            
            for member in members:
                # Strip prefix
                rel = member
                if prefix and member.startswith(prefix):
                    rel = member[len(prefix):]
                if not rel or rel == "/":
                    continue
                
                # Skip protected files
                skip = False
                for p in PROTECTED:
                    if rel == p or rel.startswith(p + "/"):
                        skip = True
                        break
                if skip:
                    continue

                dest = HERE / rel
                if member.endswith("/"):
                    dest.mkdir(parents=True, exist_ok=True)
                else:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(member) as src_f:
                        dest.write_bytes(src_f.read())
    except Exception as e:
        # Rollback
        rollback(backed)
        return {"ok": False, "error": f"解压失败: {e}", "stage": "extract", "rolled_back": True}

    # Update version.json
    try:
        if (extract_dir / "version.json").exists():
            shutil.copy2(extract_dir / "version.json", VERSION_FILE)
    except Exception:
        pass

    # Cleanup
    try:
        zip_path.unlink()
        shutil.rmtree(extract_dir)
    except Exception:
        pass

    return {"ok": True, "message": "升级完成，请重启写作台"}

def rollback(backed=None):
    """从备份恢复"""
    if not BACKUP_DIR.exists():
        return False
    try:
        for name in PROTECTED:
            backup_file = BACKUP_DIR / name
            if backup_file.exists():
                dest = HERE / name
                if dest.is_dir():
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.copytree(backup_file, dest)
                else:
                    shutil.copy2(backup_file, dest)
        return True
    except Exception:
        return False