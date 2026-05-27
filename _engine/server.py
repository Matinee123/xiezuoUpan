import json
import mimetypes
import socket
import urllib.request
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote

from .config import config
from .docstore import docstore
from .llm import call_llm, LLMError
from .export import export_markdown, export_html, export_wechat_html, export_docx, export_pdf
from .template import TemplateEngine
from .updater import check_update, apply_update
from .local_llm import model_info, start_server, stop_server, is_running, list_models, find_model, MODELS_DIR

HERE = Path(__file__).resolve().parent.parent

AVAILABLE_VERSIONS = ["通用写作", "党政写作", "商务写作", "法务写作", "教师写作", "学生写作", "职场写作", "媒体创作"]
VERSION_MAP = {
    "general": "通用写作", "party": "党政写作", "business": "商务写作",
    "legal": "法务写作", "teacher": "教师写作", "student": "学生写作",
    "office": "职场写作", "media": "媒体创作"
}

class APIHandler(SimpleHTTPRequestHandler):
    static_dir = HERE / "通用写作" / "static"
    version_dir = HERE / "通用写作"

    def __init__(self, *args, **kwargs):
        self.template_engine = None
        self._current_version = "通用写作"
        super().__init__(*args, **kwargs)

    def log_message(self, format, *args):
        pass

    def _get_version(self, default="通用写作"):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        raw = qs.get("v", [default])[0]
        if raw in VERSION_MAP:
            return VERSION_MAP[raw]
        if raw in AVAILABLE_VERSIONS:
            return raw
        return default

    def _ensure_version(self, version):
        if version != self._current_version:
            self._current_version = version
            self.version_dir = HERE / version
            self.template_engine = None

    def _serve_static(self):
        path = urlparse(self.path).path.lstrip("/")
        if not path:
            path = "index.html"
        file_path = self.static_dir / path
        if file_path.exists() and file_path.is_file():
            content_type, _ = mimetypes.guess_type(str(file_path))
            if content_type is None:
                content_type = "application/octet-stream"
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(file_path.read_bytes())
        else:
            index_path = self.static_dir / "index.html"
            if index_path.exists():
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(index_path.read_bytes())
            else:
                self._json_response({"error": "Not Found"}, 404)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/health":
            self._json_response({"status": "ok", "version": "1.0.0", "engine": config.engine})
        elif path == "/api/config":
            self._json_response({
                "engine": config.engine,
                "engines": ["deepseek", "greenapi", "ollama", "custom", "local"],
                "deepseek_api_key": config.deepseek_api_key,
                "deepseek_model": config.deepseek_model,
                "greenapi_api_key": config.greenapi_api_key,
                "greenapi_base_url": config.greenapi_base_url,
                "greenapi_model": config.greenapi_model,
                "ollama_model": config.ollama_model,
                "local_model": config.local_model,
                "local_base_url": config.local_base_url,
                "custom_base_url": config.custom_base_url,
                "custom_api_key": config.custom_api_key,
                "custom_model": config.custom_model
            })
        elif path == "/api/documents":
            self._json_response(docstore.list())
        elif path.startswith("/api/documents/"):
            doc_id = path.split("/")[-1]
            doc = docstore.get(doc_id)
            if doc:
                self._json_response(doc)
            else:
                self._json_response({"error": "文档不存在"}, 404)
        elif path == "/api/templates":
            v = self._get_version()
            self._ensure_version(v)
            self._json_response(self._get_template_engine().list_templates())
        elif path.startswith("/api/template/"):
            v = self._get_version()
            self._ensure_version(v)
            name = unquote(path.split("/api/template/")[-1])
            tmpl = self._get_template_engine().get_template(name)
            if tmpl:
                self._json_response(tmpl)
            else:
                self._json_response({"error": "模板不存在"}, 404)
        elif path == "/api/prompts":
            v = self._get_version()
            self._ensure_version(v)
            self._json_response(self._get_template_engine().list_prompts())
        elif path == "/api/has-key":
            self._json_response({"has_key": config.has_active_key(), "engine": config.engine})
        elif path == "/api/local-status":
            self._json_response(model_info())
        elif path == "/api/local-models":
            self._json_response(list_models())
        elif path == "/api/proxy-models":
            base_url = parse_qs(parsed.query).get("url", [None])[0]
            api_key = parse_qs(parsed.query).get("key", [None])[0]
            if not base_url or not api_key:
                self._json_response({"error": "缺少参数"}, 400)
                return
            try:
                url = base_url.rstrip("/") + "/models"
                req = urllib.request.Request(url, headers={"Authorization": "Bearer " + api_key, "User-Agent": "AI-Writing-Workstation"})
                resp = urllib.request.urlopen(req, timeout=10)
                data = json.loads(resp.read().decode())
                models = []
                for m in data.get("data", []):
                    models.append(m.get("id", ""))
                self._json_response({"models": sorted(models)})
            except Exception as e:
                self._json_response({"error": str(e)}, 500)
        elif path == "/api/check-update":
            self._json_response(check_update())
        elif path == "/api/version":
            version_file = HERE / "version.json"
            if version_file.exists():
                self._json_response(json.loads(version_file.read_text(encoding="utf-8-sig")))
            else:
                self._json_response({"version": "1.0.0"})
        elif path == "/api/versions":
            self._json_response([
                {"id":"party","name":"党政写作","icon":"🏛","desc":"通知、请示、报告、讲话稿、会议纪要","theme":"#cc0000"},
                {"id":"business","name":"商务写作","icon":"💼","desc":"商业计划书、合同、投标方案、商务邮件、翻译","theme":"#1a56db"},
                {"id":"legal","name":"法务写作","icon":"⚖","desc":"起诉状、律师函、法律意见书、合同审查","theme":"#2d3748"},
                {"id":"teacher","name":"教师写作","icon":"🍎","desc":"教案、试卷、教学计划、课件大纲","theme":"#059669"},
                {"id":"student","name":"学生写作","icon":"📚","desc":"论文、作业、读书笔记、学习总结","theme":"#3b82f6"},
                {"id":"office","name":"职场写作","icon":"👔","desc":"周报、述职、OKR、工作总结","theme":"#4b5563"},
                {"id":"media","name":"媒体创作","icon":"📱","desc":"公众号、小红书、短视频脚本、新闻稿","theme":"#ea580c"},
                {"id":"general","name":"通用写作","icon":"🌐","desc":"自由创作，适合各类日常写作场景","theme":"#6366f1"}
            ])
        elif path == "/api/download":
            fname = parse_qs(parsed.query).get("f", [None])[0]
            if fname:
                fpath = HERE / "exports" / fname
                if fpath.exists():
                    self.send_response(200)
                    ct = "application/vnd.openxmlformats-officedocument.wordprocessingml.document" if fname.endswith(".docx") else "application/pdf"
                    self.send_header("Content-Type", ct)
                    self.send_header("Content-Disposition", f'attachment; filename="{fname}"')
                    self.send_header("Content-Length", str(fpath.stat().st_size))
                    self.end_headers()
                    self.wfile.write(fpath.read_bytes())
                    return
            self._json_response({"error": "文件不存在"}, 404)
        elif path == "/api/search":
            q = parse_qs(parsed.query).get("q", [""])[0]
            if q:
                results = []
                for doc_id, meta in docstore.docs.items():
                    title = meta.get("title", "")
                    if q.lower() in title.lower():
                        results.append({"id": doc_id, "title": title, "updated_at": meta.get("updated_at", "")})
                self._json_response(results)
            else:
                self._json_response([])
        else:
            self._serve_static()

    def do_POST(self):
        body = self._read_body()
        path = urlparse(self.path).path

        if path == "/api/documents":
            title = body.get("title", "未命名文档")
            content = body.get("content", "")
            doc_id = docstore.create(title, content)
            self._json_response({"id": doc_id, "title": title})
        elif path.startswith("/api/documents/") and path.endswith("/save"):
            doc_id = path.split("/")[-2]
            title = body.get("title", "未命名文档")
            content = body.get("content", "")
            result = docstore.save(doc_id, title, content)
            if result:
                self._json_response({"id": doc_id, "title": title})
            else:
                self._json_response({"error": "文档不存在"}, 404)
        elif path.startswith("/api/documents/") and path.endswith("/delete"):
            doc_id = path.split("/")[-2]
            result = docstore.delete(doc_id)
            self._json_response({"ok": result})
        elif path == "/api/chat":
            messages = body.get("messages", [])
            try:
                reply = call_llm(messages, config)
                self._json_response({"reply": reply})
            except LLMError as e:
                self._json_response({"error": str(e)}, 500)
        elif path == "/api/generate":
            prompt = body.get("prompt", "")
            template_name = body.get("template", "")
            if not prompt:
                self._json_response({"error": "请输入写作需求"}, 400)
            v = body.pop("version", None)
            if v:
                self._ensure_version(v)
            te = self._get_template_engine()
            system_prompt = ""
            if template_name:
                tmpl = te.get_template(template_name)
                if tmpl and "system_prompt" in tmpl:
                    system_prompt = tmpl["system_prompt"]
            if not system_prompt:
                prompt_text = te.get_prompt("通用写作") or te.get_prompt("通知") or te.get_prompt("通用文章") or ""
                system_prompt = prompt_text or "你是一个专业的写作助手。请根据用户的需求撰写高质量的文章。"
            messages = [{"role": "system", "content": system_prompt}]
            messages.append({"role": "user", "content": prompt})
            try:
                reply = call_llm(messages, config, temperature=0.7, max_tokens=8192)
                self._json_response({"content": reply})
            except LLMError as e:
                self._json_response({"error": str(e)}, 500)
        elif path == "/api/continue":
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
        elif path == "/api/rewrite":
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
        elif path == "/api/export":
            title = body.get("title", "未命名")
            content = body.get("content", "")
            fmt = body.get("format", "markdown")
            if fmt == "markdown":
                result = export_markdown(title, content)
                self._json_response({"format": "md", "content": result})
            elif fmt == "html":
                result = export_html(title, content)
                self._json_response({"format": "html", "content": result})
            elif fmt == "wechat":
                result = export_wechat_html(title, content, body.get("style", "business"))
                self._json_response({"format": "wechat", "content": result})
            elif fmt == "docx":
                data, err = export_docx(title, content)
                if err:
                    self._json_response({"error": err}, 400)
                else:
                    import uuid
                    fname = f"exports/doc_{uuid.uuid4().hex[:8]}.docx"
                    fpath = HERE / fname
                    fpath.parent.mkdir(parents=True, exist_ok=True)
                    fpath.write_bytes(data)
                    self._json_response({"format": "docx", "download_url": f"/api/download?f={fpath.name}"})
            elif fmt == "pdf":
                data, err = export_pdf(title, content)
                if err:
                    self._json_response({"error": err}, 400)
                else:
                    import uuid
                    fname = f"exports/doc_{uuid.uuid4().hex[:8]}.pdf"
                    fpath = HERE / fname
                    fpath.parent.mkdir(parents=True, exist_ok=True)
                    fpath.write_bytes(data)
                    self._json_response({"format": "pdf", "download_url": f"/api/download?f={fpath.name}"})
            else:
                self._json_response({"error": f"不支持的格式: {fmt}"}, 400)
        elif path == "/api/switch-engine":
            engine = body.get("engine", "")
            if engine not in ["deepseek", "greenapi", "ollama", "custom", "local"]:
                self._json_response({"error": f"不支持的引擎: {engine}"}, 400)
                return
            if engine == "local" and not is_running():
                mname = body.get("model", "")
                if mname:
                    mp = str(MODELS_DIR / (mname + ".gguf" if not mname.endswith(".gguf") else mname))
                else:
                    mp = str(MODELS_DIR / find_model())
                ok, msg = start_server(mp if mname else None)
                if not ok:
                    self._json_response({"error": f"本地模型启动失败: {msg}", "engine": config.engine}, 500)
                    return
            config.engine = engine
            if engine == "deepseek":
                config.deepseek_api_key = body.get("api_key", config.deepseek_api_key)
                config.deepseek_model = body.get("model", config.deepseek_model)
            elif engine == "greenapi":
                config.greenapi_api_key = body.get("api_key", config.greenapi_api_key)
                config.greenapi_base_url = body.get("base_url", config.greenapi_base_url)
                config.greenapi_model = body.get("model", config.greenapi_model)
            elif engine == "ollama":
                config.ollama_model = body.get("model", config.ollama_model)
            elif engine == "local":
                config.local_model = body.get("model", config.local_model)
                config.local_base_url = body.get("base_url", config.local_base_url)
                if not config.local_model:
                    from .local_llm import find_model
                    from pathlib import Path
                    m = find_model()
                    if m:
                        config.local_model = Path(m).stem
            elif engine == "custom":
                config.custom_base_url = body.get("base_url", config.custom_base_url)
                config.custom_api_key = body.get("api_key", config.custom_api_key)
                config.custom_model = body.get("model", config.custom_model)
            try:
                env_file = HERE / ".env.local"
                env_file.write_text(config.to_env_text(), encoding="utf-8")
            except Exception:
                pass
            self._json_response({"ok": True, "engine": engine})
        elif path == "/api/apply-update":
            download_url = body.get("download_url", "")
            if not download_url:
                self._json_response({"error": "缺少下载地址"}, 400)
                return
            result = apply_update(download_url)
            self._json_response(result)
        else:
            self._json_response({"error": "Not Found"}, 404)

    def _get_template_engine(self):
        if self.template_engine is None:
            prompts_dir = self.version_dir / "prompts"
            templates_dir = self.version_dir / "templates"
            self.template_engine = TemplateEngine(prompts_dir, templates_dir)
        return self.template_engine

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

def run_server(port=None, version_name="通用写作"):
    if port is None:
        port = config.port
    APIHandler.static_dir = HERE / version_name / "static"
    APIHandler.version_dir = HERE / version_name
    HTTPServer.allow_reuse_address = True
    server = HTTPServer(("0.0.0.0", port), APIHandler)
    server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print(f"[server] AI 写作工作台已启动 -> http://localhost:{port}")
    print(f"[server] 引擎: {config.engine}")
    print(f"[server] 按 Ctrl+C 停止")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[server] 正在停止...")
        server.server_close()