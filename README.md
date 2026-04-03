# Mailer

Django-проект для импорта рассылок из XLSX-файла с последующей отправкой писем.

## Стек

- Python 3.10+
- Django 4.2+
- SQLite
- openpyxl

## Установка
```bash
git clone <repo>
cd mailer
uv sync
```

## Запуск
```bash
python manage.py migrate
python manage.py import_mailings path/to/file.xlsx
```

## Формат файла

Первая строка — заголовки. Обязательные колонки:

| Колонка | Описание |
|---|---|
| `external_id` | Уникальный идентификатор во внешней системе |
| `user_id` | Идентификатор пользователя |
| `email` | Email получателя |
| `subject` | Тема письма |
| `message` | Текст письма |

## Логика повторного импорта

- `status=sent` — пропускается
- `status=failed` — повторная отправка
- запись отсутствует — создаётся и отправляется

## Результат выполнения
```
Importing from file.xlsx…
Processed : 100
Created   : 95
Skipped   : 3
Failed    : 2
```

## Тесты
```bash
python manage.py test apps.mailings.tests
```