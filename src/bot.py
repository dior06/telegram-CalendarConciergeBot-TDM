import telebot
from telebot import types
import database
from database import DataBaseHandler
from datetime import datetime, timedelta
from google_calendar_integration import GoogleCalendarIntegration

# Инициализация базы данных и Google Calendar
db_handler = DataBaseHandler()
google_calendar = GoogleCalendarIntegration()

bot = telebot.TeleBot('7287404688:AAGFVPNVBsg9R6ASpRxp35wiK0la9T7IXhk')

# Словарь для хранения ответов пользователей
users_data = {}

# Функция для приветствия
def greeting(message) -> str:
    username: str = message.from_user.first_name
    if message.from_user.last_name:
        username += ' ' + message.from_user.last_name

    greeting_message: str = f"Салам Алейкум, <b>{username}</b>, что бы вы хотели сделать?"
    return greeting_message

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start_bot(message) -> None:
    greeting_message: str = greeting(message)

    keyboard = types.InlineKeyboardMarkup()
    key_init = types.InlineKeyboardButton(text='Создать встречу', callback_data='1')
    keyboard.add(key_init)
    key_chdata = types.InlineKeyboardButton(text='Изменить данные существующей встречи', callback_data='2')
    keyboard.add(key_chdata)
    key_chtime = types.InlineKeyboardButton(text='Изменить дату существующей встречи', callback_data='3')
    keyboard.add(key_chtime)
    key_stata = types.InlineKeyboardButton(text='Посмотреть статистику встреч', callback_data='4')
    keyboard.add(key_stata)

    bot.send_message(message.chat.id, greeting_message, parse_mode='html', reply_markup=keyboard)

# Обработчик callback'ов
@bot.callback_query_handler(func=lambda call: True)
def response(function_call) -> None:
    if function_call.message:
        if function_call.data == '1':
            meeting_creation(function_call)
        elif function_call.data == '2':
            bot.send_message(function_call.message.chat.id, 'Изменение данных о встрече')
        elif function_call.data == '3':
            bot.send_message(function_call.message.chat.id, 'Изменение даты встречи...')
        elif function_call.data == '4':
            bot.send_message(function_call.message.chat.id, 'Статистика')

def meeting_creation(function_call) -> None:
    chat_id = function_call.message.chat.id
    users_data[chat_id] = {} 
    bot.send_message(chat_id, 'Введите название встречи')
    bot.register_next_step_handler(function_call.message, meeting_title)

def meeting_title(message):
    users_data[message.chat.id]['answer1'] = message.text 
    bot.send_message(message.chat.id, 'Описание встречи по-братски напиши')
    bot.register_next_step_handler(message, meeting_description)

def meeting_description(message):
    chat_id = message.chat.id
    users_data[chat_id]['answer2'] = message.text
    bot.send_message(chat_id, 'Участники?')
    bot.register_next_step_handler(message, meeting_members)

def meeting_members(message):
    users_data[message.chat.id]['answer3'] = message.text
    bot.send_message(message.chat.id, 'Продолжительность (число минут) ?')
    bot.register_next_step_handler(message, meeting_time)

def meeting_time(message):
    try:
        duration_minutes = int(message.text)
        users_data[message.chat.id]['answer4'] = duration_minutes
        bot.send_message(message.chat.id, 'Введите время начала встречи в формате час.минуты.день.месяц.год')
        bot.register_next_step_handler(message, meeting_start_time)
    except ValueError:
        bot.send_message(message.chat.id, 'Нужно ввести число')
        bot.register_next_step_handler(message, meeting_time)

def meeting_start_time(message):
    chat_id = message.chat.id
    users_data[chat_id]['answer5'] = message.text
    answers = users_data[chat_id]
    print(f"Ответы пользователя {chat_id}: {answers}")

    title = answers['answer1']
    description = answers['answer2']
    participants = answers['answer3']
    duration_minutes = answers['answer4']
    start_time_input = answers['answer5']
    user_id = message.from_user.id

    # Переводим строковое время в datetime
    try:
        start_time = datetime.strptime(start_time_input, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        bot.send_message(message.chat.id, 'Неверный формат времени. Пожалуйста, используйте формат: YYYY-MM-DD HH:MM:SS')
        bot.register_next_step_handler(message, meeting_start_time)
        return

    end_time = start_time + timedelta(minutes=duration_minutes)
    participants_list = [user_id]  # Пока что только текущий пользователь

    # Сохраняем встречу в базе данных
    meeting_id = db_handler.create_meeting(
        title=title,
        description=description,
        start_time=start_time.isoformat(),
        end_time=end_time.isoformat(),
        participants=participants_list
    )

    # Здесь нужно определить emails участников для календаря
    attendees_emails = ["example@gmail.com"]  # Замените на реальные почты участников, если есть

    # Создаем событие в Google Calendar
    event = google_calendar.create_event(
        summary=title,
        description=description,
        start_time=start_time,  # Передаем объект datetime
        end_time=end_time,      # Передаем объект datetime
        attendees=attendees_emails
    )

    bot.send_message(chat_id, f'Встреча "{title}" успешно создана с идентификатором {meeting_id}.\nСобытие в календаре: {event.get("htmlLink")}')

    # Очищаем данные пользователя
    del users_data[chat_id]

# Обработчик команды /show_db
@bot.message_handler(commands=['show_db'])
def show_db_content(message):
    try:
        tables = ['users', 'meetings', 'meeting_participants', 'statistics'] 
        response = ""

        for table in tables:
            content = db_handler.get_table_content(table)
            response += f"Содержимое таблицы {table}:\n"
            if content:
                for row in content:
                    response += f"{row}\n"
            else:
                response += "Нет данных.\n"
            response += "\n"

        bot.send_message(message.chat.id, response)
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка при проверке базы данных: {str(e)}")

# Запуск бота
bot.infinity_polling()
