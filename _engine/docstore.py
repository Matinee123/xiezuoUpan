import json
import uuid
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
DATA_DIR = HERE / "_data" / "documents"
INDEX_FILE = DATA_DIR / "index.json"

class DocStore:
    def __init__(self):
        self.docs = {}
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._load_index()

    def _load_index(self):
        if INDEX_FILE.exists():
            self.docs = json.loads(INDEX_FILE.read_text(encoding="utf-8"))

    def _save_index(self):
        INDEX_FILE.write_text(json.dumps(self.docs, ensure_ascii=False, indent=2), encoding="utf-8")

    def list(self):
        items = []
        for doc_id, meta in self.docs.items():
            items.append({
                "id": doc_id,
                "title": meta["title"],
                "updated_at": meta["updated_at"],
                "version": meta.get("version", 1)
            })
        items.sort(key=lambda x: x["updated_at"], reverse=True)
        return items

    def get(self, doc_id):
        doc_file = DATA_DIR / f"{doc_id}.json"
        if not doc_file.exists():
            return None
        return json.loads(doc_file.read_text(encoding="utf-8"))

    def create(self, title="未命名文档", content=""):
        doc_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()
        self.docs[doc_id] = {
            "title": title,
            "created_at": now,
            "updated_at": now,
            "version": 1
        }
        self._save_index()
        doc_file = DATA_DIR / f"{doc_id}.json"
        doc_file.write_text(json.dumps({
            "id": doc_id,
            "title": title,
            "content": content,
            "history": [{"version": 1, "content": content, "saved_at": now}]
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        return doc_id

    def save(self, doc_id, title, content):
        if doc_id not in self.docs:
            return None
        now = datetime.now().isoformat()
        meta = self.docs[doc_id]
        meta["title"] = title
        meta["updated_at"] = now
        meta["version"] = meta.get("version", 1) + 1
        self._save_index()
        doc_file = DATA_DIR / f"{doc_id}.json"
        doc = json.loads(doc_file.read_text(encoding="utf-8"))
        doc["title"] = title
        doc["content"] = content
        doc["history"].append({
            "version": meta["version"],
            "content": content,
            "saved_at": now
        })
        doc_file.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
        return doc_id

    def delete(self, doc_id):
        if doc_id not in self.docs:
            return False
        del self.docs[doc_id]
        self._save_index()
        doc_file = DATA_DIR / f"{doc_id}.json"
        if doc_file.exists():
            doc_file.unlink()
        return True

docstore = DocStore()
