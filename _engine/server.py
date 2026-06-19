import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from .config import config
from .docstore import docstore
from .llm import call_llm, LLMError
from .export import export_markdown, export_html
from .template import TemplateEngine

HERE = Path(__file__).resolve().parent.parent

class APIHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.template_engine = None
        super().__init__(*args, **kwargs)

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/api/health":
            self._json_response({"status": "ok", "version": "1.0.0", "engine": config.engine})
        elif self.path == "/api/has-key":
            self._json_response({"has_key": config.has_active_key(), "engine": config.engine})
        elif self.path == "/api/config":
            self._json_response({
                "engine": config.engine,
                "engines": ["deepseek", "openai", "ollama", "custom"]
            })
        elif self.path == "/api/documents":
            self._json_response(docstore.list())
        elif self.path.startswith("/api/documents/"):
            doc_id = self.path.split("/")[-1]
            doc = docstore.get(doc_id)
            if doc:
                self._json_response(doc)
            else:
                self._json_response({"error": "文档不存在"}, 404)
        elif self.path == "/api/templates":
            self._json_response(self._get_template_engine().list_templates())
        elif self.path == "/api/prompts":
            self._json_response(self._get_template_engine().list_prompts())
        elif self.path == "/api/version":
            version_file = HERE / "version.json"
            if version_file.exists():
                self._json_response(json.loads(version_file.read_text(encoding="utf-8")))
            else:
                self._json_response({"version": "1.0.0"})
        else:
            super().do_GET()

    def do_POST(self):
        body = self._read_body()
        if self.path == "/api/documents":
            title = body.get("title", "未命名文档")
            content = body.get("content", "")
            doc_id = docstore.create(title, content)
            self._json_response({"id": doc_id, "title": title})
        elif self.path.startswith("/api/documents/") and self.path.endswith("/save"):
            doc_id = self.path.split("/")[-2]
            title = body.get("title", "未命名文档")
            content = body.get("content", "")
            result = docstore.save(doc_id, title, content)
            if result:
                self._json_response({"id": doc_id, "title": title})
            else:
                self._json_response({"error": "文档不存在"}, 404)
        elif self.path.startswith("/api/documents/") and self.path.endswith("/delete"):
            doc_id = self.path.split("/")[-2]
            result = docstore.delete(doc_id)
            self._json_response({"ok": result})
        elif self.path == "/api/chat":
            messages = body.get("messages", [])
            try:
                reply = call_llm(messages, config)
                self._json_response({"reply": reply})
            except LLMError as e:
                self._json_response({"error": str(e)}, 500)
        elif self.path == "/api/generate":
            prompt = body.get("prompt", "")
            template_name = body.get("template", "")
            if not prompt:
                self._json_response({"error": "请输入写作需求"}, 400)
            te = self._get_template_engine()
            system_prompt = ""
            if template_name:
                tmpl = te.get_template(template_name)
                if tmpl and "system_prompt" in tmpl:
                    system_prompt = tmpl["system_prompt"]
            if not system_prompt:
                prompt_text = te.get_prompt("通用写作")
                system_prompt = prompt_text or "你是一个专业的写作助手。请根据用户的需求撰写高质量的文章。"
            messages = [{"role": "system", "content": system_prompt}]
            messages.append({"role": "user", "content": prompt})
            try:
                reply = call_llm(messages, config, temperature=0.7, max_tokens=8192)
                self._json_response({"content": reply})
            except LLMError as e:
                self._json_response({"error": str(e)}, 500)
        elif self.path == "/api/continue":
            content = body.get("content", "")
            if not content:
                self._json_response({"error": "没有可续写的内容"}, 400)
            messages = [
                {"role": "system", "content": "请继续撰写文章，保持原有的风格和语气。"},
                {"role": "user", "content": f"以下是我已经写的内容：\n\n{content}\n\n请继续写下去："}
            ]
            try:
                reply = call_llm(messages, config)
                self._json_response({"content": reply})
            except LLMError as e:
                self._json_response({"error": str(e)}, 500)
        elif self.path == "/api/rewrite":
            content = body.get("content", "")
            style = body.get("style", "更通顺")
            if not content:
                self._json_response({"error": "没有可改写的内容"}, 400)
            messages = [
                {"role": "system", "content": f"你是一个文字编辑。请改写下面的内容，要求：{style}。只返回改写后的结果。"},
                {"role": "user", "content": content}
            ]
            try:
                reply = call_llm(messages, config)
                self._json_response({"content": reply})
            except LLMError as e:
                self._json_response({"error": str(e)}, 500)
        elif self.path == "/api/export":
            doc_id = body.get("doc_id", "")
            fmt = body.get("format", "markdown")
            doc = docstore.get(doc_id) if doc_id else body
            if not doc:
                self._json_response({"error": "内容为空"}, 400)
            title = doc.get("title", "未命名")
            content = doc.get("content", "")
            if fmt == "markdown":
                result = export_markdown(title, content)
                self._json_response({"format": "md", "content": result})
            elif fmt == "html":
                result = export_html(title, content)
                self._json_response({"format": "html", "content": result})
            else:
                self._json_response({"error": f"不支持的格式: {fmt}"}, 400)
        elif self.path == "/api/switch-engine":
            engine = body.get("engine", "")
            if engine in ["deepseek", "openai", "ollama", "custom"]:
                config.engine = engine
                self._json_response({"ok": True, "engine": engine})
            else:
                self._json_response({"error": f"不支持的引擎: {engine}"}, 400)
        else:
            self._json_response({"error": "Not Found"}, 404)

    def _get_template_engine(self):
        if self.template_engine is None:
            version_dir = self._detect_version_dir()
            prompts_dir = version_dir / "prompts" if version_dir else HERE / "通用写作" / "prompts"
            templates_dir = version_dir / "templates" if version_dir else HERE / "通用写作" / "templates"
            self.template_engine = TemplateEngine(prompts_dir, templates_dir)
        return self.template_engine

    def _detect_version_dir(self):
        path = Path(self.path[1:] if self.path.startswith("/") else self.path)
        return None

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def _json_response(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

def run_server(port=None):
    if port is None:
        port = config.port
    server = HTTPServer(("0.0.0.0", port), APIHandler)
    print(f"[server] AI 写作工作台已启动 → http://localhost:{port}")
    print(f"[server] 引擎: {config.engine}")
    print(f"[server] 按 Ctrl+C 停止")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[server] 正在停止...")
        server.server_close()
