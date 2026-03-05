#!/usr/bin/env python3
"""
Генератор звіту ВЦП (IV квартал)
Використання: python generate_report.py [шлях_до_yaml]
За замовчуванням читає report_data.yaml з поточної папки.
"""

import sys
import yaml
from pathlib import Path
from datetime import datetime

def load_yaml(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)

def is_empty(val):
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

def section_items(items: list, render_fn) -> str:
    """Рендерить список елементів або повертає заглушку."""

    valid = [i for i in (items or []) if isinstance(i, dict) and not all(is_empty(v) for v in i.values())]
    if not valid:
        return '<p class="empty">— відомостей не подано —</p>'
    return "".join(render_fn(i, idx + 1) for idx, i in enumerate(valid))

def card(num: int, body: str) -> str:
    return f'<div class="card"><span class="card-num">{num}</span><div class="card-body">{body}</div></div>'

def row(label: str, value: str) -> str:
    if is_empty(value):
        return ""
    return f'<div class="row"><span class="label">{label}:</span><span class="value">{value}</span></div>'

# ── рендер-функції для кожного типу запису ──────────────────────────────────

def render_submitted_article(item, n):
    return card(n,
        row("Назва", item.get("title")) +
        row("Журнал", item.get("journal")) +
        row("Автори", item.get("authors"))
    )

def render_published_article(item, n):
    return card(n,
        row("Назва", item.get("title")) +
        row("Журнал", item.get("journal")) +
        row("Автори", item.get("authors")) +
        row("Бібліографічний опис (ДСТУ)", item.get("dstu"))
    )

def render_conference(item, n):
    return card(n,
        row("Конференція", item.get("conference_name")) +
        row("Місце проведення", item.get("location")) +
        row("Дата", item.get("date")) +
        row("Назва доповіді", item.get("report_title")) +
        row("Автори", item.get("authors"))
    )

def render_published_abstract(item, n):
    return card(n,
        row("Конференція", item.get("conference_name")) +
        row("Місце проведення", item.get("location")) +
        row("Дата", item.get("date")) +
        row("Назва доповіді", item.get("report_title")) +
        row("Автори", item.get("authors")) +
        row("Бібліографічний опис (ДСТУ)", item.get("dstu"))
    )

def render_patent(item, n):
    status_badge = f'<span class="badge badge-{"green" if item.get("status","").lower() == "опубліковано" else "orange"}">{item.get("status","")}</span>'
    return card(n,
        f'<div class="row"><span class="label">Статус:</span><span class="value">{status_badge}</span></div>' +
        row("Назва", item.get("title")) +
        row("Номер", item.get("number")) +
        row("Журнал", item.get("journal")) +
        row("Автори", item.get("authors")) +
        row("Бібліографічний опис (ДСТУ)", item.get("dstu"))
    )

def render_completed_manual(item, n):
    return card(n,
        row("Назва", item.get("title")) +
        row("Автори", item.get("authors")) +
        row("Курс", item.get("course")) +
        row("Спеціальність", item.get("specialty")) +
        row("Факультет", item.get("faculty")) +
        row("Інститут", item.get("institute")) +
        row("Примітки", item.get("notes"))
    )

def render_inprogress_manual(item, n):
    return card(n,
        row("Назва", item.get("title")) +
        row("Автори", item.get("authors")) +
        row("Очікуваний термін завершення", item.get("expected_completion")) +
        row("Примітки", item.get("notes"))
    )

def render_course(item, n):
    return card(n,
        row("Назва курсу", item.get("course_name")) +
        row("Факультет", item.get("faculty")) +
        row("Інститут", item.get("institute")) +
        row("Спеціальність", item.get("specialty"))
    )

def render_student(item, n):
    level_badge = f'<span class="badge badge-blue">{item.get("degree_level","")}</span>'
    return card(n,
        f'<div class="row"><span class="label">Рівень:</span><span class="value">{level_badge}</span></div>' +
        row("ПІБ студента", item.get("student_name")) +
        row("Тема роботи", item.get("thesis_title"))
    )

def render_consultee(item, n):
    return card(n,
        row("ПІБ студента", item.get("student_name")) +
        row("Роль", item.get("role"))
    )

def render_award(item, n):
    return card(n,
        row("Нагорода / досягнення", item.get("title")) +
        row("Дата", item.get("date")) +
        row("Опис", item.get("description"))
    )

# ── HTML-шаблон ─────────────────────────────────────────────────────────────

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="uk">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Звіт ВЦП — {quarter}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Source+Serif+4:ital,wght@0,300;0,400;0,600;1,300&display=swap');

  :root {{
    --ink:       #1a1a2e;
    --ink-soft:  #3d3d5c;
    --paper:     #faf8f3;
    --paper2:    #f3f0e8;
    --accent:    #8b5e3c;
    --accent2:   #c4813a;
    --rule:      #d4c9b0;
    --green:     #2d7a4f;
    --orange:    #c4813a;
    --blue:      #2d5a8b;
    --empty:     #a09880;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: 'Source Serif 4', Georgia, serif;
    font-weight: 300;
    background: var(--paper);
    color: var(--ink);
    line-height: 1.7;
  }}

  /* ── HEADER ── */
  header {{
    background: var(--ink);
    color: var(--paper);
    padding: 3rem 2rem 2.5rem;
    text-align: center;
    position: relative;
    overflow: hidden;
  }}
  header::before {{
    content: '';
    position: absolute;
    inset: 0;
    background: repeating-linear-gradient(
      45deg,
      transparent,
      transparent 40px,
      rgba(255,255,255,.02) 40px,
      rgba(255,255,255,.02) 41px
    );
  }}
  .header-kpi {{
    font-family: 'Source Serif 4', serif;
    font-size: .75rem;
    letter-spacing: .25em;
    text-transform: uppercase;
    opacity: .55;
    margin-bottom: .6rem;
  }}
  header h1 {{
    font-family: 'Playfair Display', serif;
    font-size: clamp(1.4rem, 4vw, 2.2rem);
    font-weight: 700;
    line-height: 1.25;
    max-width: 820px;
    margin: 0 auto .9rem;
  }}
  .header-meta {{
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: .5rem 1.5rem;
    font-size: .82rem;
    opacity: .7;
  }}
  .header-meta span::before {{ content: '·'; margin-right: .5rem; opacity: .4; }}
  .header-meta span:first-child::before {{ display: none; }}

  /* ── TOPIC BAND ── */
  .topic-band {{
    background: var(--accent);
    color: #fff;
    text-align: center;
    padding: .75rem 1.5rem;
    font-size: .78rem;
    letter-spacing: .04em;
    line-height: 1.5;
  }}
  .topic-band strong {{ display: block; font-weight: 600; }}

  /* ── LAYOUT ── */
  .container {{ max-width: 900px; margin: 0 auto; padding: 2.5rem 1.5rem 4rem; }}

  /* ── CHAPTER ── */
  .chapter {{
    margin-bottom: 3rem;
    border-top: 2px solid var(--ink);
    padding-top: 1.5rem;
  }}
  .chapter-title {{
    font-family: 'Playfair Display', serif;
    font-size: 1.3rem;
    font-weight: 700;
    color: var(--ink);
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: .75rem;
  }}
  .chapter-icon {{
    width: 32px; height: 32px;
    background: var(--ink);
    color: var(--paper);
    display: flex; align-items: center; justify-content: center;
    font-size: .9rem;
    font-family: 'Playfair Display', serif;
    font-weight: 700;
    flex-shrink: 0;
  }}

  /* ── SECTION ── */
  .section {{ margin-bottom: 2rem; }}
  .section-title {{
    font-size: .72rem;
    letter-spacing: .18em;
    text-transform: uppercase;
    color: var(--accent);
    font-weight: 600;
    font-family: 'Source Serif 4', serif;
    border-bottom: 1px solid var(--rule);
    padding-bottom: .35rem;
    margin-bottom: 1rem;
  }}

  /* ── CARD ── */
  .card {{
    display: flex;
    gap: 1rem;
    background: var(--paper2);
    border-left: 3px solid var(--accent2);
    padding: 1rem 1.2rem;
    margin-bottom: .75rem;
    border-radius: 0 4px 4px 0;
  }}
  .card-num {{
    font-family: 'Playfair Display', serif;
    font-size: 1.5rem;
    color: var(--rule);
    font-weight: 700;
    min-width: 1.8rem;
    line-height: 1;
    padding-top: .1rem;
  }}
  .card-body {{ flex: 1; }}
  .row {{
    display: grid;
    grid-template-columns: 180px 1fr;
    gap: .25rem .75rem;
    margin-bottom: .3rem;
    font-size: .88rem;
  }}
  .label {{
    color: var(--ink-soft);
    font-weight: 600;
    font-size: .78rem;
    letter-spacing: .03em;
    padding-top: .1rem;
  }}
  .value {{ color: var(--ink); }}

  /* ── EMPTY ── */
  .empty {{
    color: var(--empty);
    font-style: italic;
    font-size: .88rem;
    padding: .5rem 0;
  }}

  /* ── BADGES ── */
  .badge {{
    display: inline-block;
    padding: .15em .6em;
    border-radius: 2px;
    font-size: .72rem;
    font-weight: 600;
    letter-spacing: .05em;
    text-transform: uppercase;
  }}
  .badge-green  {{ background: #d4edda; color: var(--green); }}
  .badge-orange {{ background: #fde8cb; color: var(--orange); }}
  .badge-blue   {{ background: #d0e4f5; color: var(--blue); }}

  /* ── FOOTER ── */
  footer {{
    text-align: center;
    padding: 1.5rem;
    font-size: .75rem;
    color: var(--empty);
    border-top: 1px solid var(--rule);
  }}

  @media print {{
    body {{ background: #fff; }}
    header {{ background: #000 !important; -webkit-print-color-adjust: exact; }}
    .topic-band {{ background: #8b5e3c !important; -webkit-print-color-adjust: exact; }}
  }}
  @media (max-width: 600px) {{
    .row {{ grid-template-columns: 1fr; }}
    .label {{ margin-bottom: -.1rem; }}
  }}
</style>
</head>
<body>

<header>
  <div class="header-kpi">Київський політехнічний інститут імені Ігоря Сікорського · ВЦП</div>
  <h1>Анотований звіт<br>{quarter}</h1>
  <div class="header-meta">
    <span>{author}</span>
    <span>{department}</span>
    <span>{faculty}</span>
    <span>Сформовано {generated}</span>
  </div>
</header>

<div class="topic-band">
  <strong>Тема дослідження:</strong>
  {topic}
</div>

<div class="container">

  <!-- ══════════════════════════════════════ НАУКОВА РОБОТА -->
  <div class="chapter">
    <div class="chapter-title">
      <div class="chapter-icon">I</div>
      Наукова робота
    </div>

    <div class="section">
      <div class="section-title">1. Подані статті</div>
      {submitted_articles}
    </div>

    <div class="section">
      <div class="section-title">2. Опубліковані статті</div>
      {published_articles}
    </div>

    <div class="section">
      <div class="section-title">3. Доповіді на конференціях</div>
      {conference_presentations}
    </div>

    <div class="section">
      <div class="section-title">4. Тези доповідей, що вийшли</div>
      {published_abstracts}
    </div>

    <div class="section">
      <div class="section-title">5. Тези доповідей, що подані</div>
      {submitted_abstracts}
    </div>

    <div class="section">
      <div class="section-title">6. Патенти</div>
      {patents}
    </div>
  </div>

  <!-- ══════════════════════════════════════ МЕТОДИЧНА РОБОТА -->
  <div class="chapter">
    <div class="chapter-title">
      <div class="chapter-icon">II</div>
      Методична робота
    </div>

    <div class="section">
      <div class="section-title">1. Завершені методичні посібники</div>
      {completed_manuals}
    </div>

    <div class="section">
      <div class="section-title">2. Методичні посібники у підготовці</div>
      {inprogress_manuals}
    </div>

    <div class="section">
      <div class="section-title">3. Курси, що читаються</div>
      {courses_taught}
    </div>

    <div class="section">
      <div class="section-title">4. Лабораторні заняття / практикуми</div>
      {lab_classes}
    </div>
  </div>

  <!-- ══════════════════════════════════════ ІНШЕ -->
  <div class="chapter">
    <div class="chapter-title">
      <div class="chapter-icon">III</div>
      Інше
    </div>

    <div class="section">
      <div class="section-title">1. Керівництво бакалаврськими / магістерськими роботами</div>
      {supervised_students}
    </div>

    <div class="section">
      <div class="section-title">2. Кураторство / наукове консультування студентів</div>
      {consultee_students}
    </div>

    <div class="section">
      <div class="section-title">3. Нагороди, грамоти та досягнення</div>
      {awards}
    </div>
  </div>

</div>

<footer>
  Звіт згенеровано автоматично · {generated} · КПІ ім. Ігоря Сікорського
</footer>
</body>
</html>
"""

def generate(yaml_path: str, output_path: str = None):
    data = load_yaml(yaml_path)
    meta = data.get("meta", {})
    sci  = data.get("science", {})
    meth = data.get("methodical", {})
    oth  = data.get("other", {})

    now = datetime.now().strftime("%d.%m.%Y %H:%M")

    html = HTML_TEMPLATE.format(
        quarter   = meta.get("report_quarter", "IV квартал 2025"),
        author    = meta.get("author_full_name", ""),
        department= meta.get("department", ""),
        faculty   = meta.get("faculty", ""),
        topic     = meta.get("topic", ""),
        generated = now,

        # НАУКОВА РОБОТА
        submitted_articles      = section_items(sci.get("submitted_articles"),      render_submitted_article),
        published_articles      = section_items(sci.get("published_articles"),      render_published_article),
        conference_presentations= section_items(sci.get("conference_presentations"),render_conference),
        published_abstracts     = section_items(sci.get("published_abstracts"),     render_published_abstract),
        submitted_abstracts     = section_items(sci.get("submitted_abstracts"),     render_conference),
        patents                 = section_items(sci.get("patents"),                 render_patent),

        # МЕТОДИЧНА РОБОТА
        completed_manuals  = section_items(meth.get("completed_manuals"),   render_completed_manual),
        inprogress_manuals = section_items(meth.get("in_progress_manuals"), render_inprogress_manual),
        courses_taught     = section_items(meth.get("courses_taught"),      render_course),
        lab_classes        = section_items(meth.get("lab_classes"),         render_course),

        # ІНШЕ
        supervised_students = section_items(oth.get("supervised_students"), render_student),
        consultee_students  = section_items(oth.get("consultee_students"),  render_consultee),
        awards              = section_items(oth.get("awards"),              render_award),
    )

    out = output_path or Path(yaml_path).with_suffix(".html")
    Path(out).write_text(html, encoding="utf-8")
    print(f"✅  Звіт збережено: {out}")
    return out

if __name__ == "__main__":
    yaml_file = sys.argv[1] if len(sys.argv) > 1 else "report_data.yaml"
    out_file  = sys.argv[2] if len(sys.argv) > 2 else None
    generate(yaml_file, out_file)
