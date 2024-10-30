Пример гпт

# Архитектура проекта

## Общая архитектура

Проект состоит из следующих основных компонентов:

- **Telegram Bot**:
  - Отвечает за взаимодействие с пользователем.
  - Использует библиотеку `python-telegram-bot`.

- **Google Calendar API**:
  - Интеграция для создания и управления событиями в календаре.

- **База данных**:
  - Хранение информации о пользователях, встречах, статистике.
  - Используется PostgreSQL.

## Структура базы данных

- **Таблица `users`**:
  - `user_id` (PK)
  - `telegram_id`
  - `username`
  - `google_calendar_token`

- **Таблица `meetings`**:
  - `meeting_id` (PK)
  - `creator_id` (FK to `users`)
  - `date_time`
  - `description`

- **Таблица `participants`**:
  - `meeting_id` (FK to `meetings`)
  - `user_id` (FK to `users`)

(и так далее...)

## Технологический стек

- **Язык программирования**: Python 3.10+
- **Библиотеки**:
  - `python-telegram-bot`
  - `google-api-python-client`
  - `sqlalchemy` для работы с БД
- **База данных**: PostgreSQL
- **Среда выполнения**: Docker (опционально)
