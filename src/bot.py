import telebot 
from telebot import types
import database
from database import DataBaseHandler
from datetime import datetime, timedelta
from google_calendar_integration import GoogleCalendarIntegration
import re  # Для валидации email

# Инициализация базы данных и Google Calendar
db_handler = DataBaseHandler()
google_calendar = GoogleCalendarIntegration()

bot = telebot.TeleBot('7287404688:AAGFVPNVBsg9R6ASpRxp35wiK0la9T7IXhk')

# Словарь для хранения ответов пользователей
useransw = {}  #-------

# Функция для приветствия
def greeting(message) -> str:
    username: str = message.from_user.first_name
    if message.from_user.last_name:
        username += ' ' + message.from_user.last_name

    hello: str = f"Салам Алейкум, <b>{username}</b>, что бы вы хотели сделать?"
    return hello

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start_bot(message) -> None:
    greeting_message: str = greeting(message)

    n = types.InlineKeyboardMarkup()
    strt = types.InlineKeyboardButton(text='Создать встречу', callback_data='1')
    n.add(strt)
    chnf = types.InlineKeyboardButton(text='Изменить данные существующей встречи', callback_data='2')
    n.add(chnf)
    chtm = types.InlineKeyboardButton(text='Изменить дату существующей встречи', callback_data='3')
    n.add(chtm)
    wtchsttcs = types.InlineKeyboardButton(text='Посмотреть статистику встреч', callback_data='4')
    n.add(wtchsttcs)

    bot.send_message(message.chat.id, greeting_message, parse_mode='html', reply_markup=n)

# Обработчик callback'ов
@bot.callback_query_handler(func=lambda call: True)
def response(function_call) -> None:
    if function_call.message:
        if function_call.data == '1':
            init_vstr(function_call)
        elif function_call.data == '2':
            bot.send_message(function_call.message.chat.id, 'مغلق  ! Эта функция еще не готова ')
        elif function_call.data == '3':
            bot.send_message(function_call.message.chat.id, '關閉! Эта функция еще не готова')
        elif function_call.data == '4':
            bot.send_message(function_call.message.chat.id, 'སྒོ་བརྒྱབ། ! эта функция не готова')

def init_vstr(function_call) -> None:
    msg_idnt = function_call.message.chat.id
    useransw[msg_idnt] = {} 
    bot.send_message(msg_idnt, 'Название встречи ?')
    bot.register_next_step_handler(function_call.message, nazw_vstr)

def nazw_vstr(message):
    useransw[message.chat.id]['uno'] = message.text 
    bot.send_message(message.chat.id, 'Напишите описание встречи')
    bot.register_next_step_handler(message, opsn_vstr)

def opsn_vstr(message):
    useransw[message.chat.id]['duo'] = message.text
    bot.send_message(message.chat.id, 'Участники (почта) ?\nВведите email адреса участников, разделяя их запятыми или пробелами.')
    bot.register_next_step_handler(message, uchastnik_vstr)

def uchastnik_vstr(message):
    email_input = message.text
    emails = parse_emails(email_input)
    if not emails:
        bot.send_message(message.chat.id, 'Неверный формат email адресов. Пожалуйста, попробуйте снова.')
        bot.register_next_step_handler(message, uchastnik_vstr)
        return
    useransw[message.chat.id]['tree'] = emails
    bot.send_message(message.chat.id, 'Продолжительность (число минут) ?')
    bot.register_next_step_handler(message, vrm_vstr)

# Функция для парсинга и валидации email адресов
def parse_emails(text):
    # Разделяем по запятым или пробелам
    raw_emails = re.split('[,\\s]+', text.strip())
    # Простая валидация email
    email_pattern = re.compile(r"[^@]+@[^@]+\.[^@]+")
    valid_emails = [email for email in raw_emails if email_pattern.match(email)]
    return valid_emails if valid_emails else None

# время продолжительности встречи
def vrm_vstr (message):
    chat_id = message.chat.id
    user_input = message.text

    if not user_input:
        prompt_error(chat_id)
        return

    duration = parse_duration(user_input)
    if duration is not None:
        useransw[chat_id]['quadro'] = duration
        prompt_next_step(chat_id, 'Введите время начала встречи в формате YYYY-MM-DD HH:MM:SS', meeting_start_time)
    else:
        prompt_error(chat_id)

def parse_duration(text):
    if not text.strip().isdigit():
        return None
    else:
        return int(text.strip())

def prompt_error(chat_id):
    bot.send_message(chat_id, 'Так не ясно. Нужно ввести число')
    bot.register_next_step_handler_by_chat_id(chat_id, vrm_vstr)

def prompt_next_step(chat_id, prompt_text, next_handler):
    bot.send_message(chat_id, prompt_text)
    bot.register_next_step_handler_by_chat_id(chat_id, next_handler)

def meeting_start_time(message):
    chat_id = message.chat.id
    useransw[chat_id]['cinque'] = message.text
    answers = useransw[chat_id]
    print(f"Ответы пользователя {chat_id}: {answers}")

    nzvn = answers.get('uno')
    opsn = answers.get('duo')
    uchstnc = answers.get('tree')
    dltlnst = answers.get('quadro')
    start_time_input = answers.get('cinque')
    user_id = message.from_user.id

    try:
        start_time = datetime.strptime(start_time_input, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        bot.send_message(message.chat.id, 'Такая дата не подойдет. Пожалуйста, напишите дату в формате: YYYY-MM-DD HH:MM:SS')
        bot.register_next_step_handler(message, meeting_start_time)
        return

    end_time = start_time + timedelta(minutes=dltlnst)
    participants_list = [user_id]  # Пока что только текущий пользователь

    # Сохраняем встречу в базе данных
    meeting_id = db_handler.create_meeting(
        title=nzvn,
        description=opsn,
        start_time=start_time.isoformat(),
        end_time=end_time.isoformat(),
        participants=participants_list
    )

    # Получаем список email участников из useransw
    attendees_emails = uchstnc  # Это список email адресов

    # Создаем событие в Google Calendar
    event = google_calendar.create_event(
        summary=nzvn,
        description=opsn,
        start_time=start_time,  
        end_time=end_time,      
        attendees=attendees_emails  # Передаем список email адресов
    )

    if event:
        bot.send_message(chat_id, f'Встреча "{nzvn}" успешно создана. Номер встречи: {meeting_id}.\nСсылка на встречу в календаре: {event.get("htmlLink")}')
    else:
        bot.send_message(chat_id, f'Не удалось создать событие в календаре.')

    # Очищаем данные пользователя
    del useransw[chat_id]

# Обработчик команды /show_db
@bot.message_handler(commands=['show_db'])
def show_db_content(message):
    for I in ['users', 'meetings', 'meeting_participants', 'statistics']:
        content = db_handler.get_table_content(I)
        if content:
            formatted_content = "\n".join([str(row) for row in content])
            bot.send_message(message.chat.id, f"База данных :{I}:\n{formatted_content}\n")
        else:
            bot.send_message(message.chat.id, f"Данных в таблице {I} нет.\n")

# Запуск бота
bot.infinity_polling()
