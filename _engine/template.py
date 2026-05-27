import json
from pathlib import Path

class TemplateEngine:
    def __init__(self, prompts_dir, templates_dir):
        self.prompts_dir = Path(prompts_dir)
        self.templates_dir = Path(templates_dir)

    def list_templates(self):
        templates = []
        if self.templates_dir.exists():
            for f in sorted(self.templates_dir.glob("*.json")):
                try:
                    data = json.loads(f.read_text(encoding="utf-8-sig"))
                    templates.append({
                        "name": data.get("name", f.stem),
                        "file": f.name,
                        "description": data.get("description", "")
                    })
                except json.JSONDecodeError:
                    templates.append({"name": f.stem, "file": f.name, "description": ""})
        return templates

    def list_prompts(self):
        prompts = []
        if self.prompts_dir.exists():
            for f in sorted(self.prompts_dir.glob("*.md")):
                content = f.read_text(encoding="utf-8")
                first_line = content.splitlines()[0] if content else ""
                prompts.append({
                    "name": f.stem,
                    "file": f.name,
                    "preview": first_line.replace("# ", "").strip()
                })
        return prompts

    def get_prompt(self, name):
        prompt_file = self.prompts_dir / f"{name}.md"
        if not prompt_file.exists():
            prompt_file = self.prompts_dir / name
        if not prompt_file.exists():
            return None
        return prompt_file.read_text(encoding="utf-8")

    def get_template(self, name):
        template_file = self.templates_dir / f"{name}.json"
        if not template_file.exists():
            template_file = self.templates_dir / name
        if not template_file.exists():
            return None
        return json.loads(template_file.read_text(encoding="utf-8-sig"))

    def render_prompt(self, prompt_text, variables):
        """将变量替换到提示词模板中"""
        result = prompt_text
        for key, value in variables.items():
            result = result.replace("{{" + key + "}}", value)
        return result
