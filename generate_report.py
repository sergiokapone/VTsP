#!/usr/bin/env python3
"""
Генератор звіту ВЦП (IV квартал)
Використання: python generate_report.py [шлях_до_yaml] [шлях_до_html] [шлях_до_шаблону]
За замовчуванням читає report_data.yaml і шукає report_template.html поруч зі скриптом.
"""

import sys
import yaml
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape


def load_yaml(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def is_empty(val) -> bool:
    """Перевіряє чи значення порожнє."""
    if val is None:
        return True
    if isinstance(val, str):
        return val.strip() == ""
    if isinstance(val, list):
        return len(val) == 0 or all(
            all(is_empty(v) for v in (item.values() if isinstance(item, dict) else [item]))
            for item in val
        )
    return False


def valid_items(items):
    """Jinja2-фільтр: повертає лише непорожні елементи списку."""
    if not items:
        return []
    return [
        i for i in items
        if isinstance(i, dict) and not all(is_empty(v) for v in i.values())
    ]


def generate(yaml_path: str, output_path: str = None,
             template_path: str = None) -> str:

    data = load_yaml(yaml_path)

    # Шлях до шаблону — поруч зі скриптом за замовчуванням
    template_file = Path(template_path or Path(__file__).parent / "report_template.html")

    env = Environment(
        loader=FileSystemLoader(str(template_file.parent)),
        autoescape=select_autoescape(["html"]),
    )
    env.filters["valid_items"] = valid_items

    template = env.get_template(template_file.name)

    html = template.render(
        meta       = data.get("meta", {}),
        science    = data.get("science", {}),
        methodical = data.get("methodical", {}),
        other      = data.get("other", {}),
        generated  = datetime.now().strftime("%d.%m.%Y %H:%M"),
    )

    out = Path(output_path or Path(yaml_path).with_suffix(".html"))
    out.write_text(html, encoding="utf-8")
    print(f"✅  Звіт збережено: {out}")
    return str(out)


if __name__ == "__main__":
    yaml_file     = sys.argv[1] if len(sys.argv) > 1 else "report_data.yaml"
    out_file      = sys.argv[2] if len(sys.argv) > 2 else None
    template_file = sys.argv[3] if len(sys.argv) > 3 else None
    generate(yaml_file, out_file, template_file)
