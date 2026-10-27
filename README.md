# Data Feeling School — сайт школы

Статический сайт [datafeelingschool.ru](https://datafeelingschool.ru): главная («Обо мне»), каталог курсов, страница на каждый курс и блог со статьями, привязанными к курсам. Без зависимостей, нужен только Python 3.

## Страницы
| URL | Файл |
|---|---|
| `/` — обо мне | `src/pages/index.html` |
| `/courses/` — все курсы | `src/pages/courses.html` |
| `/pet-project/` — курс по пет-проектам | `src/pages/pet-project.html` |
| `/n8n/`, `/claude-code/`, `/llm-product/`, `/lovable/`, `/stylish-site/`, `/kaggle/`, `/clearml/`, `/excel-ai/` | `src/courses/*.json` |
| `/n8n-landing/` — прежний лендинг n8n | `src/pages/n8n-landing.html` |
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

## Как добавить или обновить курс
Каждый курс — файл `src/courses/<slug>.json`. Страница `/<slug>/`, карточки в каталоге и на главной, ссылки в футере и блок «Курс по теме» под статьями собираются из него автоматически (шаблон — `courses.py`).
1. Скопируйте любой файл из `src/courses/` и поменяйте поля: название, цена, число студентов, программа, авторы, FAQ.
2. Цифры (студенты, рейтинг, цена) берите со Stepik: `https://stepik.org/api/courses/<id>`.
3. Рейтинг показывается, только если отзывов 10 и больше.
4. `"status": "soon"` — курс ещё не стартовал, кнопка ведёт на `url` (например, отдельный лендинг).
5. `"custom_page": true` — у курса своя страница в `src/pages/` (так сделан `/pet-project/`).

Старый лендинг n8n сохранён по адресу `/n8n-landing/` (закрыт от индексации).

## Аналитика переходов
Делается автоматически при сборке (`tracking.py`), руками ничего проставлять не нужно:
- **Stepik:** ко всем ссылкам добавляются `utm_source=datafeelingschool`, `utm_medium=site`, `utm_campaign=<id курса>`, `utm_content=<страница сайта>` (например `pet-project`, `blog-rezhim-manyaka`).
- **Личка в Telegram:** ссылки на `t.me/Aleron_df` открывают чат с готовым текстом: «Привет! Нашёл твой контакт на сайте datafeelingschool.ru» + «У меня вопрос по курсу «…»» на странице курса или «Прочитал статью «…»» в блоге. Свой текст для страницы — поле `tg_context:` в её шапке.

## Обложки статей
Берётся поле `cover:` или первая картинка из текста статьи. Если картинок нет — цветная обложка с эмодзи курса (поле `emoji` в `src/courses/*.json`).

## Фото авторов курсов
Лежат в `assets/img/team/`, взяты из профилей на Stepik (`https://stepik.org/api/users/<id>` → поле `avatar`).

## Дизайн
Цвета и радиусы — переменные в начале `assets/css/style.css` (акцент: `--accent`).

## Деплой на Beget
Домен `datafeelingschool.ru` привязан в панели Beget к сайту `testdraft.store`, файлы лежат в `~/testdraft.store/public_html/`.

1. Запушьте изменения в `main`.
2. Откройте панель Beget → «Терминал» → «Виртуальный хостинг» и выполните:
   ```
   curl -s https://raw.githubusercontent.com/a-milenkin/data_feeling_school/main/deploy.sh | sh
   ```
Скрипт сделает резервную копию в `~/backups` (без видео), скачает код из GitHub, соберёт сайт и скопирует его поверх. Ничего не удаляет.

⚠️ Папки `images/` и `videos/` на сервере не удаляйте: `/n8n/` берёт оттуда видео (в репозиторий они не входят).

Вход по SSH-ключу с компьютера на Beget не держится: веб-терминал панели при подключении перезаписывает `~/.ssh/authorized_keys`. Вариант с GitHub Actions по FTP описан в `.github/workflows/deploy.yml` (нужны секреты `FTP_*`).
