#!/bin/sh
# Деплой на Beget. Запускается НА СЕРВЕРЕ: панель Beget → «Терминал» → «Виртуальный хостинг».
# Одной строкой (скопировать и вставить в терминал Beget):
#   curl -s https://raw.githubusercontent.com/a-milenkin/data_feeling_school/main/deploy.sh | sh
#
# Что делает: резервная копия текущего сайта в ~/backups (без видео), свежий код из GitHub,
# сборка python3 build.py и копирование dist/ поверх сайта. На сервере ничего не удаляется,
# так что videos/ и images/ остаются.
# Домен datafeelingschool.ru привязан в панели Beget к сайту testdraft.store.
set -e
SITE="$HOME/testdraft.store/public_html"
SRC="$HOME/dfs_src"

mkdir -p "$HOME/backups"
tar --exclude=videos -czf "$HOME/backups/dfs-public_html-$(date +%Y%m%d-%H%M).tgz" -C "$(dirname "$SITE")" public_html
rm -rf "$SRC"
git clone -q --depth 1 https://github.com/a-milenkin/data_feeling_school.git "$SRC"
cd "$SRC" && python3 build.py
cp -r "$SRC/dist/." "$SITE/"
echo "DEPLOY_OK: https://datafeelingschool.ru/"
