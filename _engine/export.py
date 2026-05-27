from pathlib import Path
import re

def export_markdown(title, content):
    """导出 Markdown 格式"""
    stripped = content.strip()
    if stripped.startswith('# '):
        # 内容自带标题，跳过第一行用编辑器标题覆盖
        idx = stripped.find('\n')
        body = stripped[idx+1:].strip() if idx > 0 else ''
        return f"# {title}\n\n{body}"
    return f"# {title}\n\n{stripped}"

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
</body>
</html>"""
    return html

def export_wechat_html(title, content, style="business"):
    """导出微信公众号 HTML（全部内联样式，5种风格）"""
    styles = {
        "business": {
            "name": "极简商务风",
            "bg": "#ffffff",
            "text": "#333333",
            "h1": "font-size:22px;font-weight:700;color:#1a1a1a;text-align:center;padding:24px 0 16px;border-bottom:1px solid #eee;margin-bottom:24px;",
            "h2": "font-size:17px;font-weight:600;color:#2d3436;padding:8px 0;margin:24px 0 12px;border-bottom:1px solid #dfe6e9;",
            "p": "font-size:15px;color:#333;line-height:1.85;margin:0 0 16px;letter-spacing:0.5px;",
            "quote": "font-size:14px;color:#636e72;background:#f5f6fa;padding:14px 18px;margin:20px 0;border-left:3px solid #0984e3;border-radius:0 6px 6px 0;line-height:1.75;",
            "code": "font-family:Menlo,Consolas,monospace;font-size:13px;background:#f0f0f0;padding:2px 6px;border-radius:3px;color:#e84393;",
            "list": "font-size:15px;color:#333;line-height:1.85;padding-left:20px;margin:0 0 16px;",
            "hr": "border:none;border-top:1px solid #eee;margin:24px 0;",
            "footer": "font-size:12px;color:#b2bec3;text-align:center;padding:20px 0;border-top:1px solid #eee;margin-top:40px;",
            "accent": "#0984e3"
        },
        "literary": {
            "name": "文艺清新风",
            "bg": "#fefefe",
            "text": "#4a4a4a",
            "h1": "font-size:22px;font-weight:400;color:#2c3e50;text-align:center;padding:20px 0 12px;font-family:Georgia,'Noto Serif SC',serif;letter-spacing:2px;",
            "h2": "font-size:16px;font-weight:400;color:#8b7866;padding:10px 0;margin:20px 0 10px;text-align:center;",
            "p": "font-size:15px;color:#555;line-height:2;margin:0 0 20px;letter-spacing:0.8px;font-family:Georgia,'Noto Serif SC','PingFang SC',serif;",
            "quote": "font-size:15px;color:#8b7866;text-align:center;padding:20px;margin:24px 0;font-style:italic;border-top:1px solid #e8d5c4;border-bottom:1px solid #e8d5c4;",
            "code": "font-family:Georgia,serif;font-size:14px;color:#c0392b;background:#fef9f3;padding:2px 8px;border-radius:3px;",
            "list": "font-size:15px;color:#555;line-height:2;padding-left:20px;",
            "hr": "border:none;border-top:1px dashed #e8d5c4;margin:28px 0;",
            "footer": "font-size:12px;color:#ccc;text-align:center;padding:20px 0;letter-spacing:1px;",
            "accent": "#c8956c"
        },
        "tech": {
            "name": "科技专业风",
            "bg": "#ffffff",
            "text": "#2d3436",
            "h1": "font-size:24px;font-weight:700;color:#0c0c0c;padding:24px 0 16px;line-height:1.3;",
            "h2": "font-size:18px;font-weight:600;color:#0984e3;padding:12px 0 8px;margin:28px 0 14px;border-left:4px solid #0984e3;padding-left:14px;",
            "p": "font-size:15px;color:#2d3436;line-height:1.8;margin:0 0 18px;",
            "quote": "font-size:14px;color:#636e72;background:#f8f9fa;padding:16px 20px;margin:20px 0;border-radius:8px;font-family:Menlo,Consolas,monospace;",
            "code": "font-family:Menlo,Consolas,monospace;font-size:13px;background:#2d3436;color:#55efc4;padding:3px 8px;border-radius:4px;",
            "list": "font-size:15px;color:#2d3436;line-height:1.8;padding-left:20px;",
            "hr": "border:none;border-top:2px solid #dfe6e9;margin:30px 0;",
            "footer": "font-size:12px;color:#b2bec3;text-align:center;padding:16px 0;",
            "accent": "#0984e3"
        },
        "youth": {
            "name": "活力年轻风",
            "bg": "#fefefe",
            "text": "#2d3436",
            "h1": "font-size:23px;font-weight:700;color:#2d3436;padding:20px 0 10px;text-align:center;background:linear-gradient(135deg,#ff6b6b,#feca57);-webkit-background-clip:text;-webkit-text-fill-color:transparent;",
            "h2": "font-size:17px;font-weight:600;background:#fff5f5;padding:10px 14px;margin:24px 0 12px;border-radius:8px;color:#e74c3c;",
            "p": "font-size:15px;color:#444;line-height:1.9;margin:0 0 18px;",
            "quote": "font-size:15px;color:#e74c3c;text-align:center;padding:16px;margin:20px 0;background:#fff5f5;border-radius:12px;font-weight:500;",
            "code": "font-family:Menlo,monospace;font-size:13px;background:#ffeaa7;color:#d63031;padding:3px 8px;border-radius:4px;",
            "list": "font-size:15px;color:#444;line-height:1.9;padding-left:20px;",
            "hr": "border:none;border-top:2px dotted #dfe6e9;margin:26px 0;",
            "footer": "font-size:12px;color:#b2bec3;text-align:center;padding:20px 0;",
            "accent": "#ff6b6b"
        },
        "official": {
            "name": "官方正式风",
            "bg": "#ffffff",
            "text": "#333333",
            "h1": "font-size:24px;font-weight:700;color:#cc0000;text-align:center;padding:30px 0 20px;border-bottom:2px solid #cc0000;margin-bottom:28px;letter-spacing:1px;",
            "h2": "font-size:17px;font-weight:600;color:#cc0000;padding:6px 0;margin:24px 0 14px;border-bottom:1px solid #e0e0e0;",
            "p": "font-size:16px;color:#333;line-height:1.9;margin:0 0 18px;text-indent:2em;",
            "quote": "font-size:15px;color:#666;background:#f8f8f8;padding:16px 20px;margin:24px 0;border-left:4px solid #cc0000;line-height:1.8;",
            "code": "font-family:SimSun,serif;font-size:15px;color:#333;background:#f5f5f5;padding:2px 6px;border-radius:2px;",
            "list": "font-size:16px;color:#333;line-height:1.9;padding-left:20px;",
            "hr": "border:none;border-top:1px solid #ddd;margin:28px 0;",
            "footer": "font-size:13px;color:#999;text-align:right;padding:16px 0;",
            "accent": "#cc0000"
        }
    }

    cfg = styles.get(style, styles["business"])

    def format_wechat(text):
        """将 Markdown-like 文本转为微信公众号 HTML"""
        lines = text.split('\n')
        result = []
        buf = []
        flush = lambda: result.append(''.join(buf)) if buf else None

        for line in lines:
            stripped = line.strip()

            if not stripped:
                flush()
                buf = []
                continue

            # 标题
            if stripped.startswith('### '):
                flush(); buf = []
                result.append('<h3 style="font-size:15px;font-weight:600;color:{0};padding:4px 0;margin:18px 0 8px;">{1}</h3>'.format(cfg['accent'], stripped[4:]))
                continue
            if stripped.startswith('## '):
                flush(); buf = []
                result.append('<h2 style="{0}">{1}</h2>'.format(cfg['h2'], stripped[3:]))
                continue
            if stripped.startswith('# '):
                flush(); buf = []
                result.append('<h1 style="{0}">{1}</h1>'.format(cfg['h1'], stripped[2:]))
                continue

            # 引用
            if stripped.startswith('> '):
                flush(); buf = []
                result.append('<blockquote style="{0}">{1}</blockquote>'.format(cfg['quote'], stripped[2:]))
                continue

            # 分隔线
            if stripped == '---' or stripped == '***':
                flush(); buf = []
                result.append('<hr style="{0}">'.format(cfg['hr']))
                continue

            # 有序列表
            if re.match(r'^\d+[\.\)] ', stripped):
                flush(); buf = []
                text = re.sub(r'^\d+[\.\)] ', '', stripped)
                result.append('<p style="{0}"><span style="color:{2};">{1}</span></p>'.format(cfg['list'], text, cfg['accent']))
                continue

            # 无序列表
            if stripped.startswith('- ') or stripped.startswith('* '):
                flush(); buf = []
                text = stripped[2:]
                result.append('<p style="{0}">- {1}</p>'.format(cfg['list'], text))
                continue

            # 普通段落
            buf.append(stripped)

        flush()

        # 合并连续段落
        final = []
        for item in result:
            if item.startswith('<p ') and final and final[-1].startswith('<p '):
                final[-1] = final[-1][:-4] + '<br>' + item[item.index('>')+1:]
            else:
                final.append(item)

        return '\n'.join(final)

    body_html = format_wechat(content)

    html = f"""<section style="max-width:677px;margin:0 auto;padding:16px 12px 30px;background:{cfg['bg']};font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif;">
<h1 style="{cfg['h1']}">{title}</h1>
{body_html}
</section>"""
    return html

def save_file(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return str(path)
