from pathlib import Path

def export_markdown(title, content):
    """导出 Markdown 格式"""
    return f"# {title}\n\n{content}"

def export_html(title, content):
    """导出 HTML 格式"""
    md_content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
body {{
    font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
    max-width: 800px; margin: 40px auto; padding: 0 20px;
    line-height: 1.8; color: #333;
}}
h1 {{ border-bottom: 2px solid #6366f1; padding-bottom: 10px; }}
h2 {{ color: #4f46e5; }}
pre {{ background: #f5f5f5; padding: 16px; border-radius: 8px; overflow-x: auto; }}
code {{ background: #f0f0f0; padding: 2px 6px; border-radius: 4px; }}
blockquote {{ border-left: 4px solid #6366f1; margin: 0; padding-left: 16px; color: #666; }}
.footer {{ margin-top: 40px; text-align: center; color: #999; font-size: 14px; }}
</style>
</head>
<body>
<h1>{title}</h1>
<div class="content">
{md_content.replace(chr(10), "<br>")}
</div>
<div class="footer">由 AI 写作工作台生成</div>
</body>
</html>"""
    return html

def save_file(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return str(path)
