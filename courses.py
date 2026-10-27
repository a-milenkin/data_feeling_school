"""Курсы школы: данные из src/courses/*.json и шаблон страницы курса.

Чтобы добавить курс, создайте src/courses/<slug>.json по образцу соседних файлов.
Страница появится по адресу /<slug>/. Если у курса своя страница в src/pages,
поставьте "custom_page": true — тогда здесь соберётся только карточка.
"""
import html
import json
from pathlib import Path

CATEGORIES = {
    "ai": "Искусственный интеллект",
    "ml": "Machine Learning и Data Science",
    "business": "Свои продукты и бизнес",
}
MIN_REVIEWS_FOR_RATING = 10
STEPIK_NOTE = "Обучение проходит на Stepik"
ASK_URL = "https://t.me/Aleron_df"

e = html.escape


def load_courses(folder):
    courses = {}
    for f in sorted(Path(folder).glob("*.json")):
        c = json.loads(f.read_text(encoding="utf-8"))
        c.setdefault("slug", f.stem)
        c.setdefault("card_title", c["title"])
        c.setdefault("label", c["card_title"])
        c.setdefault("color", "lav")
        courses[c["slug"]] = c
    return dict(sorted(courses.items(), key=lambda kv: kv[1].get("order", 99)))


def num(n):
    return f"{n:,}".replace(",", " ")


def rating(c):
    if c.get("rating") and c.get("reviews", 0) >= MIN_REVIEWS_FOR_RATING:
        return f'{c["rating"]:.2f}'.rstrip("0").rstrip(".").replace(".", ",")
    return ""


def is_soon(c):
    return c.get("status") == "soon"


def featured_card(c):
    points = "".join(f"<li>{e(x)}</li>" for x in c.get("highlights", []))
    return (
        f'<a class="card featured-card reveal" href="/{c["slug"]}/">'
        f'<div class="fc-main"><span class="fc-badge">{e(c.get("badge", ""))}</span>'
        f'<h3>{e(c["card_title"])}</h3><p>{e(c["short"])}</p>'
        f'<ul class="fc-points">{points}</ul></div>'
        f'<div class="fc-side"><img class="fc-cover" src="{c["cover"]}" alt="" loading="lazy" width="160" height="160">'
        f'<div class="fc-price">{e(c.get("price", ""))}</div><span class="btn primary">Смотреть интенсив →</span></div>'
        f'</a>'
    )


def course_card(c):
    if c.get("featured"):
        return featured_card(c)
    meta = []
    if c.get("students"):
        meta.append(f'{num(c["students"])} студентов')
    if rating(c):
        meta.append(f"★ {rating(c)}")
    if c.get("price"):
        meta.append(c["price"])
    badge = "Скоро" if is_soon(c) else c.get("badge", "")
    return (
        f'<a class="card {c["color"]} course-card reveal" href="/{c["slug"]}/">'
        f'<div class="cc-top"><img class="cc-cover" src="{c["cover"]}" alt="" loading="lazy" width="64" height="64">'
        f'{f"<span class=cc-badge>{e(badge)}</span>" if badge else ""}</div>'
        f'<h3>{e(c["card_title"])}</h3><p>{e(c["short"])}</p>'
        f'<div class="meta">{"".join(f"<span>{e(m)}</span>" for m in meta)}</div>'
        f'<span class="go">Подробнее →</span></a>'
    )


def course_cards(courses, category=None):
    sel = [c for c in courses.values() if category in (None, c["category"])]
    return "\n".join(course_card(c) for c in sel)


def catalog(courses):
    """Каталог по категориям для страницы /courses/."""
    out = []
    top = [c for c in courses.values() if c.get("featured")]
    if top:
        out.append('<div class="grid-3">' + "\n".join(featured_card(c) for c in top) + "</div>")
    rest = {k: c for k, c in courses.items() if not c.get("featured")}
    for key, name in CATEGORIES.items():
        cards = course_cards(rest, key)
        if cards:
            out.append(f'<h2 class="cat-title">{name}</h2><div class="grid-3">{cards}</div>')
    return "\n".join(out)


def footer_links(courses):
    return "\n".join(f'<a href="/{c["slug"]}/">{e(c["card_title"])}</a>' for c in courses.values())


def avatar(a):
    if a.get("photo"):
        return f'<img class="avatar" src="{a["photo"]}" alt="{e(a["name"])}" loading="lazy">'
    initials = "".join(w[0] for w in a["name"].split()[:2])
    return f'<span class="avatar initials">{e(initials)}</span>'


def cta_button(c, cls="btn primary"):
    label = c.get("cta") or ("Узнать о старте" if is_soon(c) else "Записаться на курс")
    return f'<a class="{cls}" href="{c["url"]}" rel="noopener">{e(label)}</a>'


def render_course_page(c, related_html):
    """HTML страницы курса (контент внутри <main>)."""
    stats = []
    if c.get("students"):
        stats.append((num(c["students"]), "студентов на Stepik"))
    if rating(c):
        stats.append((rating(c), f'рейтинг курса ({num(c["reviews"])} отзывов)'))
    if c.get("lessons"):
        stats.append((str(c["lessons"]), "уроков" + (f' и {c["tests"]} заданий' if c.get("tests") else "")))
    if c.get("hours"):
        h = c["hours"]
        stats.append((f"{h} ч".replace(".", ",") if not isinstance(h, str) else h, "на прохождение"))
    stats_html = "".join(f'<div class="stat reveal"><b>{e(v)}</b><span>{e(t)}</span></div>' for v, t in stats[:4])

    colors = ["peach", "mint", "sky", "lemon", "rose", "lav"]
    for_whom = "".join(
        f'<div class="card {colors[i % len(colors)]} reveal"><h3>{e(x["title"])}</h3><p>{e(x["text"])}</p></div>'
        for i, x in enumerate(c.get("for_whom", [])))
    outcomes = "".join(f"<li>{e(x)}</li>" for x in c.get("outcomes", []))
    program = "".join(
        f'<div class="step reveal"><h3>{e(m["title"])}</h3><p>{e(m.get("text", ""))}</p></div>'
        for m in c.get("program", []))
    reqs = "".join(f"<li>{e(x)}</li>" for x in c.get("requirements", []))
    authors = "".join(
        f'<div class="author reveal">{avatar(a)}<div><b>{e(a["name"])}</b><p>{e(a.get("bio", ""))}</p></div></div>'
        for a in c.get("authors", []))
    faq = "".join(f'<details><summary>{e(q["q"])}</summary><p>{e(q["a"])}</p></details>' for q in c.get("faq", []))
    tags = "".join(f"<li>{e(t)}</li>" for t in c.get("tags", []))

    hero_badges = []
    if rating(c):
        hero_badges.append(f'<div class="badge b2"><b>★ {rating(c)}</b>{num(c["reviews"])} отзывов на Stepik</div>')
    if c.get("students"):
        hero_badges.append(f'<div class="badge b1"><b>{num(c["students"])}</b>студентов</div>')
    elif is_soon(c):
        hero_badges.append('<div class="badge b1"><b>Скоро</b>старт курса</div>')

    notes = ""
    if c.get("note"):
        notes += f'<p class="disclaimer">{e(c["note"])}</p>'
    if c.get("not_included"):
        notes += f'<p class="disclaimer"><b>Чего не будет.</b> {e(c["not_included"])}</p>'

    if c.get("tariffs"):
        price_block = '<div class="grid-2">' + "".join(
            f'<div class="price-card single"><div><span class="eyebrow" style="color:#b9a7ff">{e(t["name"])}</span>'
            f'<div class="price">{e(t["price"])}</div><ul class="ticks">{"".join(f"<li>{e(i)}</li>" for i in t["items"])}</ul>'
            f'{cta_button(c)}</div></div>' for t in c["tariffs"]) + "</div>"
    else:
        includes = [f'{c["lessons"]} уроков' + (f' и {c["tests"]} заданий' if c.get("tests") else "")] if c.get("lessons") else []
        includes += ["Доступ к материалам на Stepik", "Сертификат Stepik"] if c.get("certificate") else ["Доступ к материалам на Stepik"]
        if c.get("community"):
            includes.append("Сообщество курса в Telegram")
        price_block = (
            f'<div class="price-card"><div><span class="eyebrow" style="color:#b9a7ff">Стоимость</span>'
            f'<h2>{e(c["card_title"])}</h2><ul class="ticks">{"".join(f"<li>{e(i)}</li>" for i in includes)}</ul></div>'
            f'<div class="price-box"><div class="price">{e(c["price"])}</div>'
            f'<p class="small muted" style="margin:8px 0 20px">{STEPIK_NOTE}</p>{cta_button(c)}'
            f'<p class="small muted" style="margin:14px 0 0">Цена актуальна на момент публикации, точная — на Stepik</p></div></div>'
        )

    related = ""
    if related_html:
        related = (f'<section class="section soft"><div class="container"><div class="section-head">'
                   f'<span class="eyebrow">Блог</span><h2>Статьи по теме</h2></div>'
                   f'<div class="post-grid">{related_html}</div></div></section>')

    community = ""
    if c.get("community"):
        community = f'<a class="btn ghost" href="{c["community"]}" rel="noopener">Канал курса в Telegram</a>'

    return f"""
<section class="hero">
  <div class="container grid">
    <div>
      <ul class="tags">{tags}</ul>
      <h1 class="h1-course">{e(c["title"])}</h1>
      <p class="lead">{e(c["lead"])}</p>
      <div class="btn-row">{cta_button(c)}<a class="btn ghost" href="{ASK_URL}" rel="noopener">Задать вопрос</a></div>
      <p class="small muted" style="margin-top:18px">{e(c.get("price", ""))} · {e(c.get("badge", ""))}</p>
    </div>
    <div class="hero-photo course-hero {c["color"]}">
      <img src="{c["cover"]}" alt="{e(c["card_title"])}">
      {"".join(hero_badges)}
    </div>
  </div>
</section>

{f'<section class="section" style="padding-top:0"><div class="container"><div class="stats">{stats_html}</div></div></section>' if stats_html else ""}

<section class="section soft">
  <div class="container">
    <div class="section-head"><span class="eyebrow">Для кого</span><h2>Кому подойдёт курс</h2></div>
    <div class="grid-3">{for_whom}</div>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="grid-2" style="gap:48px;align-items:start">
      <div><span class="eyebrow">Результат</span><h2>Чему вы научитесь</h2><ul class="ticks reveal">{outcomes}</ul></div>
      <div><span class="eyebrow">Перед стартом</span><h2>Что нужно</h2><ul class="ticks reveal">{reqs}</ul>{notes}</div>
    </div>
  </div>
</section>

<section class="section dark">
  <div class="container">
    <div class="section-head"><span class="eyebrow" style="color:#b9a7ff">Программа</span><h2>Из чего состоит курс</h2></div>
    <div class="steps dark-steps">{program}</div>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="section-head"><span class="eyebrow">Авторы</span><h2>Кто ведёт курс</h2></div>
    <div class="authors">{authors}</div>
  </div>
</section>

<section class="section soft" id="price">
  <div class="container">{price_block}</div>
</section>

{f'<section class="section"><div class="container" style="max-width:820px"><div class="section-head"><span class="eyebrow">FAQ</span><h2>Частые вопросы</h2></div>{faq}</div></section>' if faq else ""}

{related}

<section class="section">
  <div class="container">
    <div class="cta">
      <div><h2>{"Узнайте о старте первыми" if is_soon(c) else "Готовы начать?"}</h2><p>{e(c["short"])}</p></div>
      <div class="btn-row" style="margin:0">{cta_button(c)}{community}</div>
    </div>
  </div>
</section>
"""


def course_jsonld(c, site):
    data = {
        "@context": "https://schema.org", "@type": "Course",
        "name": c["title"], "description": c["short"], "url": f"{site}/{c['slug']}/",
        "provider": {"@type": "Organization", "name": "Data Feeling School", "sameAs": site},
    }
    if rating(c):
        data["aggregateRating"] = {"@type": "AggregateRating", "ratingValue": c["rating"], "reviewCount": c["reviews"]}
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + "</script>"
