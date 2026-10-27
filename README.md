# Data Feeling School — сайт школы

Статический сайт [datafeelingschool.ru](https://datafeelingschool.ru): главная («Обо мне»), каталог курсов, страница на каждый курс и блог со статьями, привязанными к курсам. Без зависимостей, нужен только Python 3.

## Страницы
| URL | Файл |
|---|---|
| `/` — обо мне | `src/pages/index.html` |
| `/courses/` — все курсы | `src/pages/courses.html` |
| `/pet-project/` — курс по пет-проектам | `src/pages/pet-project.html` |
| `/n8n/` — курс по n8n (прежний лендинг) | `src/pages/n8n.html` |
| `/blog/`, `/blog/<slug>/` | `src/blog/*.md` |

## Локально
```bash
python3 build.py --serve   # http://localhost:8000
```
Сборка кладёт готовый сайт в `dist/` (в git не попадает).

## Как добавить статью
Создайте `src/blog/my-slug.md`:
```
---
title: Заголовок
description: Одно предложение для превью и поисковиков
date: 2026-11-01
course: pet-project     # pet-project | n8n | none
draft: true             # необязательно: скрыть статью
source: https://t.me/datafeeling/1994   # необязательно: пост-оригинал (несколько — через запятую)
---
Текст в Markdown (## заголовки, списки, > цитаты, ![](/assets/img/x.jpg), [ссылки](...))
```
Под статьёй автоматически появится блок курса, а на странице курса — подборка «Статьи по теме».

## Как добавить курс
1. Скопируйте `src/pages/pet-project.html` в `src/pages/<slug>.html`, поменяйте `path:` и тексты.
2. Добавьте курс в словарь `COURSES` в `build.py` и карточку в `courses.html`.

## Дизайн
Цвета и радиусы — переменные в начале `assets/css/style.css` (акцент: `--accent`).

## Деплой на Beget
Файлы сайта лежат в `~/datafeelingschool.ru/public_html/`.
- **Автоматически:** workflow `.github/workflows/deploy.yml` собирает сайт и заливает `dist/` по FTP при пуше в `main`. Добавьте в GitHub → Settings → Secrets: `FTP_SERVER`, `FTP_USERNAME`, `FTP_PASSWORD`, `FTP_DIR` (например `datafeelingschool.ru/public_html/`). Данные FTP — в панели Beget → «FTP».
- **Вручную:** `python3 build.py`, затем загрузите содержимое `dist/` в `public_html` (FTP или файловый менеджер Beget).

⚠️ На сервере уже есть папки `images/` и `videos/` старого лендинга. **Не удаляйте их:** `/n8n/` ссылается на `/videos/*.mp4` (видео в репозиторий не кладём). Картинки `images/` лежат в `src/static/images/`.
