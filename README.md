# rutracker_monitor

Мониторинг изменения BTIH-хеша (magnet) на страницах RuTracker.

## Что делает
- Берет список ссылок из `rutracker_links.txt`
- Для каждой ссылки извлекает magnet BTIH-хеш
- Сравнивает с предыдущим сохраненным значением из `rutracker_hash.txt`
- Печатает результат:
  - `хеш прежний`
  - `хеш изменился` (+ `title: ...` для изменившихся страниц)

## Файлы
- `rutracker_hash_check.py` — основной скрипт
- `rutracker_hash_check.sh` — запуск с фиксированными путями
- `rutracker_links.txt` — список ссылок (по одной на строку)
- `rutracker_hash.txt` — сохраненные хеши (JSON `url -> hash`)
- `rutracker_hash_monitor_logic.md` — подробная логика

## Требования
- Python 3.9+
- Пакет `requests`

Установка:

```bash
pip install requests
```

## Использование

### 1) Запуск через bash-обертку
```bash
./rutracker_hash_check.sh
```

### 2) Прямой запуск Python-скрипта
```bash
python3 rutracker_hash_check.py \
  --links-file ./rutracker_links.txt \
  --hash-file ./rutracker_hash.txt
```

### 3) Диагностика в JSON
```bash
python3 rutracker_hash_check.py \
  --links-file ./rutracker_links.txt \
  --hash-file ./rutracker_hash.txt \
  --json
```

## Формат `rutracker_links.txt`
```txt
# комментарии начинаются с #
https://rutracker.org/forum/viewtopic.php?t=6823726
https://rutracker.org/forum/viewtopic.php?t=6810475
```

## Примечания
- При первом запуске создается/обновляется `rutracker_hash.txt`.
- Если ссылка новая, она добавляется в хранилище хешей.
- При ошибке сети/парсинга скрипт вернет `error: ...` и код `2`.
