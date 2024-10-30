<!-- "Требуется сделать тг бот, который будет:
1. Ставить встречи на определенное время для двух/трех участников
2. Ставить встречи на свободное время между двумя/тремя участниками
3. Добавлять описание встречи
4. Собирать статистику, сколько встреч было на неделе + рисовать диаграммы загруженности
5. Присылать уведомления о встречах, об изменениях встреч, об удалении/добавлении участников" -->

# Описание проекта

## Введение

Цель проекта - разработать Telegram-бота для упрощения процесса планирования встреч между участниками с использованием Google Календаря.

## Функциональные требования

1. **Постановка встречи на определенное время**:
   - Пользователь может создать встречу, указав дату, время и участников.

2. **Постановка встречи в свободное время**:
   - Бот предлагает свободные слоты времени на основе календарей участников.

3. **Добавление описания встречи**:
   - Возможность добавить текстовое описание или заметки к встрече.

4. **Сбор статистики и визуализация**:
   - Подсчет количества встреч за неделю.
   - Генерация диаграмм загруженности.

5. **Уведомления**:
   - Напоминания о предстоящих встречах.
   - Уведомления об изменениях или отменах встреч.

## Сценарии использования

### Сценарий 1: Создание встречи на определенное время

1. Пользователь: `/create_meeting`
2. Бот: "Пожалуйста, укажите дату и время встречи."
3. Пользователь: "15.11.2023 14:00"
4. Бот: "Добавьте описание встречи."
5. Пользователь: "Обсуждение проекта."
6. Бот: "Укажите участников (через @username)."
7. Пользователь: "@participant1 @participant2"
8. Бот: "Встреча создана и приглашения отправлены."

дальше продолжим потом