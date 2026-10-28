"""Отслеживание переходов: UTM-метки на ссылках Stepik и стартовое сообщение в личку Telegram.

Применяется ко всем собранным страницам автоматически (см. build.py).
- Stepik: utm_source=datafeelingschool, utm_medium=site, utm_campaign=<id курса>, utm_content=<страница сайта>.
  Старые utm_* в ссылке заменяются.
- t.me/Aleron_df: добавляется ?text=… — человек открывает чат, где уже набрано, откуда он пришёл.
"""
import re
from urllib.parse import quote, urlencode, urlsplit, parse_qsl, urlunsplit

UTM_SOURCE = "datafeelingschool"
UTM_MEDIUM = "site"
TG_USER = "Aleron_df"
SITE_NAME = "datafeelingschool.ru"

STEPIK_RE = re.compile(r'href="(https?://stepik\.org/[^"]*)"')
TG_RE = re.compile(r'href="https?://t\.me/' + TG_USER + r'(?:\?[^"]*)?"', re.I)


def page_key(path):
    """'/blog/rezhim-manyaka/' -> 'blog-rezhim-manyaka', '/' -> 'home'."""
    return path.strip("/").replace("/", "-").replace(".html", "") or "home"


def stepik_course_id(url):
    m = re.search(r"stepik\.org/(?:course/|a/)?(\d+)", url)
    return m.group(1) if m else "stepik"


def add_utm(url, content):
    parts = urlsplit(url)
    query = [(k, v) for k, v in parse_qsl(parts.query) if not k.startswith("utm_")]
    query += [("utm_source", UTM_SOURCE), ("utm_medium", UTM_MEDIUM),
              ("utm_campaign", stepik_course_id(url)), ("utm_content", content)]
    return urlunsplit(parts._replace(query=urlencode(query)))


def tg_text(context=None):
    base = f"Привет! Нашёл твой контакт на сайте {SITE_NAME}"
    return f"{base}. {context}" if context else f"{base}."


def track(html_text, path, tg_context=None, tg_message=None):
    """tg_message — текст в личку целиком (например, после оплаты), вместо стандартного «Нашёл твой контакт…»."""
    content = page_key(path)
    html_text = STEPIK_RE.sub(lambda m: f'href="{add_utm(m.group(1), content).replace("&", "&amp;")}"', html_text)
    tg_url = f"https://t.me/{TG_USER}?text={quote(tg_message or tg_text(tg_context))}"
    return TG_RE.sub(f'href="{tg_url}"', html_text)
