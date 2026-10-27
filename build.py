#!/usr/bin/env python3
"""Сборщик сайта Data Feeling School. Без зависимостей: только Python 3.

    python3 build.py            # собрать сайт в dist/
    python3 build.py --serve    # собрать и открыть на http://localhost:8000

Страницы:  src/pages/*.html   (шапка с метаданными между строками ---)
Статьи:    src/blog/*.md      (метаданные + Markdown)
Курсы:     src/courses/*.json (страница /<slug>/ по шаблону из courses.py)
Статика:   src/static/        (копируется в dist/ как есть)
Ассеты:    assets/            (css, js, картинки)
"""
import hashlib
import html
import re
import shutil
import sys
from datetime import date, datetime
from pathlib import Path

from courses import (catalog, course_cards, course_jsonld, footer_links, load_courses,
                     render_course_page)
from tracking import track

ROOT = Path(__file__).parent
SRC, DIST = ROOT / "src", ROOT / "dist"
SITE = "https://datafeelingschool.ru"
DEFAULT_IMAGE = SITE + "/assets/img/aleron-stage.jpg"

# Курсы: src/courses/*.json (страницы курсов, карточки, связи со статьями)
COURSES = load_courses(SRC / "courses")


# ---------- вспомогательное ----------
def parse(text):
    """Делит файл на метаданные (между ---) и тело."""
    meta = {}
    if text.startswith("---\n"):
        head, _, text = text[4:].partition("\n---\n")
        for line in head.splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                meta[k.strip()] = v.strip()
    return meta, text


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![*\w])\*([^*\n]+)\*(?!\w)", r"<em>\1</em>", s)
    s = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r'<img src="\2" alt="\1" loading="lazy">', s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    return s


def markdown(text):
    """Мини-Markdown: заголовки, списки, цитаты, код, ссылки, картинки."""
    out, para, lst, code = [], [], None, None

    def flush():
        nonlocal para, lst
        if para:
            out.append("<p>" + inline(" ".join(para)) + "</p>")
            para = []
        if lst:
            tag, items = lst
            out.append(f"<{tag}>" + "".join(f"<li>{inline(i)}</li>" for i in items) + f"</{tag}>")
            lst = None

    for line in text.splitlines():
        if code is not None:
            if line.startswith("```"):
                out.append("<pre><code>" + html.escape("\n".join(code)) + "</code></pre>")
                code = None
            else:
                code.append(line)
            continue
        if line.startswith("```"):
            flush(); code = []; continue
        if not line.strip():
            flush(); continue
        m = re.match(r"(#{2,3}) (.+)", line)
        if m:
            flush(); n = len(m.group(1))
            out.append(f"<h{n}>{inline(m.group(2))}</h{n}>"); continue
        if line.strip() == "---":
            flush(); out.append("<hr>"); continue
        if line.startswith("> "):
            flush(); out.append(f"<blockquote><p>{inline(line[2:])}</p></blockquote>"); continue
        m = re.match(r"(?:[-*]|(\d+)\.) (.+)", line)
        if m:
            tag = "ol" if m.group(1) else "ul"
            if para:
                flush()
            if lst and lst[0] != tag:
                flush()
            lst = lst or (tag, [])
            lst[1].append(m.group(2)); continue
        if lst:
            flush()
        para.append(line.strip())
    flush()
    return "\n".join(out)


def fmt_date(d):
    months = "января февраля марта апреля мая июня июля августа сентября октября ноября декабря".split()
    dt = datetime.strptime(d, "%Y-%m-%d")
    return f"{dt.day} {months[dt.month - 1]} {dt.year}"


def source_links(p):
    """Ссылки на посты-оригиналы в Telegram (поле source: url1, url2)."""
    urls = [u.strip() for u in p.get("source", "").split(",") if u.strip()]
    if not urls:
        return ""
    channel = "@" + urls[0].rstrip("/").split("/")[-2]
    if len(urls) == 1:
        links = f'<a href="{urls[0]}" rel="noopener">читать пост в {channel}</a>'
    else:
        links = ", ".join(f'<a href="{u}" rel="noopener">часть {i}</a>' for i, u in enumerate(urls, 1))
        links = f"оригинал в {channel}: " + links
    return f'<p class="source">✈️ Впервые опубликовано в Telegram — {links}</p>'


# ---------- сборка ----------
def load_posts():
    posts = []
    for f in sorted((SRC / "blog").glob("*.md")):
        meta, body = parse(f.read_text(encoding="utf-8"))
        if meta.get("draft") == "true":
            continue
        meta["slug"] = f.stem
        meta["body"] = body
        meta.setdefault("course", "none")
        # обложка: поле cover или первая картинка из текста статьи
        first = re.search(r"!\[[^\]]*\]\(([^)]+)\)", body)
        meta.setdefault("cover", first.group(1) if first else "")
        posts.append(meta)
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


def post_card(p):
    course = p["course"]
    label = COURSES.get(course, {}).get("label", "Заметки")
    mins = max(1, round(len(p["body"].split()) / 180))
    c = COURSES.get(course, {})
    if p["cover"]:
        cover = f'<img class="pc-cover" src="{p["cover"]}" alt="" loading="lazy">'
    else:
        palette = ["lav", "mint", "peach", "sky", "lemon", "rose"]
        color = palette[sum(map(ord, p["slug"])) % len(palette)]
        cover = (f'<div class="pc-cover ph {color}"><span class="pc-emoji">{c.get("emoji", "✍️")}</span>'
                 f'<span class="pc-label">{html.escape(label)}</span></div>')
    return (
        f'<a class="post-card reveal" data-course="{course}" href="/blog/{p["slug"]}/">{cover}'
        f'<span class="pill {course}">{label}</span><h3>{html.escape(p["title"])}</h3>'
        f'<p>{html.escape(p["description"])}</p>'
        f'<span class="foot">{fmt_date(p["date"])} · {mins} мин чтения</span></a>'
    )


def fill(tpl, ctx):
    for k, v in ctx.items():
        tpl = tpl.replace("{{" + k + "}}", v)
    return tpl


def meta_slug(path):
    return path.strip("/").split("/")[0]


def write(path, content):
    target = DIST / path.strip("/") / "index.html" if not path.endswith(".html") else DIST / path.strip("/")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def build():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    layout = (SRC / "layout.html").read_text(encoding="utf-8")
    # версия css/js меняется при правках — браузеры не держат старые стили из кэша
    version = hashlib.md5(b"".join((ROOT / f).read_bytes() for f in ("assets/css/style.css", "assets/js/main.js"))).hexdigest()[:8]
    layout = layout.replace("{{asset_version}}", version)
    header = (SRC / "partials/header.html").read_text(encoding="utf-8")
    footer = fill((SRC / "partials/footer.html").read_text(encoding="utf-8"),
                  {"year": str(date.today().year), "footer_courses": footer_links(COURSES)})
    posts = load_posts()
    urls = []

    def render_related(body):
        def repl(m):
            course, limit = m.group(1), int(m.group(2) or 3)
            sel = [p for p in posts if p["course"] == course][:limit]
            return "\n".join(post_card(p) for p in sel) or '<p class="muted">Статьи скоро появятся.</p>'
        body = re.sub(r"\{\{posts:([\w-]+)(?::(\d+))?\}\}", repl, body)
        body = body.replace("{{catalog}}", catalog(COURSES))
        body = re.sub(r"\{\{course_cards(?::(\w+))?\}\}", lambda m: course_cards(COURSES, m.group(1)), body)
        return re.sub(r"\{\{latest(?::(\d+))?\}\}",
                      lambda m: "\n".join(post_card(p) for p in posts[: int(m.group(1) or 3)]), body)

    def page(meta, body, path):
        url = SITE + path
        ctx = {
            "title": html.escape(meta.get("title", "Data Feeling School")),
            "description": html.escape(meta.get("description", "")),
            "url": url, "image": meta.get("image", DEFAULT_IMAGE),
            "og_type": meta.get("og_type", "website"),
            "head_extra": meta.get("head_extra", ""),
            "header": header, "footer": footer, "content": render_related(body),
        }
        return track(fill(layout, ctx), path, meta.get("tg_context") or course_question(path))

    def course_question(path):
        """Стартовое сообщение в личку со страницы курса."""
        c = COURSES.get(meta_slug(path))
        return f'У меня вопрос по курсу «{c["card_title"]}».' if c else None

    # страницы
    for f in sorted((SRC / "pages").glob("*.html")):
        meta, body = parse(f.read_text(encoding="utf-8"))
        path = meta.get("path") or ("/" if f.stem == "index" else f"/{f.stem}/")
        if meta.get("layout") == "none":
            write(path, track(body, path, meta.get("tg_context")))
        elif f.stem == "404":
            (DIST / "404.html").write_text(page(meta, body, "/404.html"), encoding="utf-8")
            continue
        else:
            write(path, page(meta, body, path))
        urls.append((path, meta.get("lastmod", date.today().isoformat())))

    # страницы курсов из src/courses/*.json
    for c in COURSES.values():
        if c.get("custom_page"):
            continue
        rel = "\n".join(post_card(p) for p in [p for p in posts if p["course"] == c["slug"]][:3])
        meta = {"title": f'{c["title"]} — курс Data Feeling School', "description": c["short"],
                "head_extra": course_jsonld(c, SITE)}
        path = f'/{c["slug"]}/'
        write(path, page(meta, render_course_page(c, rel), path))
        urls.append((path, date.today().isoformat()))

    # блог: индекс + статьи
    blog_meta, blog_body = parse((SRC / "blog" / "_index.html").read_text(encoding="utf-8")) \
        if (SRC / "blog" / "_index.html").exists() else ({}, "")
    cards = "\n".join(post_card(p) for p in posts)
    used = [c for c in COURSES.values() if any(p["course"] == c["slug"] for p in posts)]
    filters = "\n".join(f'<button class="chip" data-filter="{c["slug"]}">{c["label"]}</button>' for c in used)
    blog_body = blog_body.replace("{{all_posts}}", cards).replace("{{blog_filters}}", filters)
    write("/blog/", page(blog_meta, blog_body, "/blog/"))
    urls.append(("/blog/", date.today().isoformat()))

    for p in posts:
        c = COURSES.get(p["course"])
        box = ""
        if c:
            box = (f'<div class="course-box"><div><span class="pill {p["course"]}">Курс по теме</span>'
                   f'<h3>{c["card_title"]}</h3><p>{c["short"]}</p></div>'
                   f'<a class="btn primary" href="/{c["slug"]}/">Узнать больше</a></div>')
        related = [x for x in posts if x["slug"] != p["slug"] and x["course"] == p["course"]][:3]
        more = ""
        if related:
            more = ('<section class="section soft"><div class="container"><h2>Читайте также</h2>'
                    '<div class="post-grid">' + "\n".join(post_card(x) for x in related) + "</div></div></section>")
        body = (
            f'<article class="article"><a class="small muted" href="/blog/">← Все статьи</a>'
            f'<h1>{html.escape(p["title"])}</h1>'
            f'<div class="byline"><span>Алерон Миленькин</span><span>·</span><span>{fmt_date(p["date"])}</span></div>'
            f'<div class="prose">{markdown(p["body"])}</div>{source_links(p)}{box}</article>{more}'
        )
        meta = {"title": p["title"] + " — Data Feeling School", "description": p["description"], "og_type": "article",
                "tg_context": f'Прочитал статью «{p["title"]}».'}
        if p["cover"].startswith("/"):
            meta["image"] = SITE + p["cover"]
        write(f"/blog/{p['slug']}/", page(meta, body, f"/blog/{p['slug']}/"))
        urls.append((f"/blog/{p['slug']}/", p["date"]))

    # статика, ассеты, служебные файлы
    shutil.copytree(ROOT / "assets", DIST / "assets")
    if (SRC / "static").exists():
        shutil.copytree(SRC / "static", DIST, dirs_exist_ok=True)
    sm = "".join(f"<url><loc>{SITE}{u}</loc><lastmod>{d}</lastmod></url>" for u, d in urls)
    (DIST / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + sm + "</urlset>",
        encoding="utf-8")
    print(f"Готово: {len(urls)} страниц, {len(posts)} статей → {DIST}")


if __name__ == "__main__":
    build()
    if "--serve" in sys.argv:
        import functools, http.server
        h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DIST))
        print("http://localhost:8000")
        http.server.ThreadingHTTPServer(("", 8000), h).serve_forever()
