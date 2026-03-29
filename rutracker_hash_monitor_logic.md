# Логика мониторинга BTIH-хеша RuTracker (multi-link)

## Цель
Проверять несколько RuTracker-ссылок, сравнивать BTIH-хеши с прошлым запуском и отправлять в чат итог:
- `хеш прежний` (если изменений нет)
- `хеш изменился` + текущий `title` страницы (для каждой изменившейся ссылки)

---

## Файлы

- Основной скрипт:
  - `/home/clawd/.openclaw/workspace/data/rutracker_hash_check.py`
- Bash-обертка (используется cron-задачей):
  - `/home/clawd/.openclaw/workspace/data/rutracker_hash_check.sh`
- Файл со списком ссылок (по одной ссылке на строку):
  - `/home/clawd/.openclaw/workspace/data/rutracker_links.txt`
- Файл с сохраненными хешами:
  - `/home/clawd/.openclaw/workspace/data/rutracker_hash.txt`
- Этот документ:
  - `/home/clawd/.openclaw/workspace/data/rutracker_hash_monitor_logic.md`

---

## Формат `rutracker_links.txt`

- Одна ссылка на строку
- Пустые строки игнорируются
- Строки с `#` считаются комментариями

Пример:

```txt
# RuTracker topics
https://rutracker.org/forum/viewtopic.php?t=6823726
https://rutracker.org/forum/viewtopic.php?t=1234567
```

---

## Как работает `rutracker_hash_check.py`

### Параметры
- `--links-file` — файл со ссылками (основной режим)
- `--url` — одиночная ссылка (legacy-режим)
- `--hash-file` — файл хранения хешей
- `--json` — вывод расширенного JSON

Важно: нужно передавать **либо** `--links-file`, **либо** `--url`.

### Логика
1. Читает ссылки из файла (или берет одну из `--url`).
2. Для каждой ссылки:
   - скачивает HTML,
   - извлекает текущий `title` страницы из тега `<title>...</title>`,
   - находит `magnet:?...`,
   - извлекает `xt=urn:btih:...`,
   - нормализует BTIH к `hex` (40 символов, lower-case).
3. Загружает прошлые хеши из `--hash-file`.
   - Текущий формат хранения: JSON-словарь `{url: hash}`.
   - Есть обратная совместимость с старым single-hash форматом (обычный текст), если отслеживается только одна ссылка.
4. Сравнивает текущие и прошлые значения:
   - `changed` — если по ссылке был хеш и он изменился,
   - `same` — если совпал,
   - `new` — если ссылка новая и в прошлых данных ее не было.
5. Перезаписывает `--hash-file` актуальным JSON-словарем.
6. Возвращает итог:
   - если обнаружены изменения по хотя бы одной старой ссылке →
     - первая строка: `хеш изменился`
     - далее по строке на каждую изменившуюся ссылку: `title: <текущий title страницы>`
   - иначе → `хеш прежний`

При ошибках сети/парсинга выводит `error: ...` и код завершения `2`.

---

## Как работает `rutracker_hash_check.sh`

Обертка фиксирует пути и запускает Python-скрипт:

```bash
python3 "$SCRIPT" --links-file "$LINKS_FILE" --hash-file "$HASH_FILE"
```

Где:
- `LINKS_FILE=/home/clawd/.openclaw/workspace/data/rutracker_links.txt`
- `HASH_FILE=/home/clawd/.openclaw/workspace/data/rutracker_hash.txt`
- `SCRIPT=/home/clawd/.openclaw/workspace/data/rutracker_hash_check.py`

---

## Cron-задача OpenClaw

- `name`: `rutracker-hash-monitor`
- `id`: `759a8191-1f4e-4c3c-a163-30d72bd5df67`
- расписание: каждый день в `19:00`, `Europe/Moscow`
- после запуска отправляет в Telegram результат проверки

---

## Ручные команды

Запуск проверки:

```bash
/home/clawd/.openclaw/workspace/data/rutracker_hash_check.sh
```

Диагностика в JSON:

```bash
python3 /home/clawd/.openclaw/workspace/data/rutracker_hash_check.py \
  --links-file /home/clawd/.openclaw/workspace/data/rutracker_links.txt \
  --hash-file /home/clawd/.openclaw/workspace/data/rutracker_hash.txt \
  --json
```

Проверка cron-задач:

```bash
openclaw cron list --json
```

Ручной запуск cron-задачи:

```bash
openclaw cron run 759a8191-1f4e-4c3c-a163-30d72bd5df67 --expect-final
```

История запусков:

```bash
openclaw cron runs --id 759a8191-1f4e-4c3c-a163-30d72bd5df67 --limit 20
```
