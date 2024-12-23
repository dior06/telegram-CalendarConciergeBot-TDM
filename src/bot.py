from sqlite3 import DataError
import telebot
from telebot import types
from database import DataBaseHandler
from datetime import datetime, timedelta, timezone
import re

from google_calendar_integration import GoogleCalendarIntegration

db_handler = DataBaseHandler()
google_calendar = GoogleCalendarIntegration()


bot = telebot.TeleBot('BOT')

useransw = {}

def greeting(message) -> str:
    username: str = message.from_user.first_name
    if message.from_user.last_name:
        username += ' ' + message.from_user.last_name

    hello: str = f"Салам Алейкум, <b>{username}</b>, что бы вы хотели сделать?"
    return hello


@bot.message_handler(commands=['start'])
def start_bot(message) -> None:
    greet: str = greeting(message)
    keyboard = types.InlineKeyboardMarkup()
    start_btn = types.InlineKeyboardButton(text='Создать встречу (вручную)', callback_data='1')
    keyboard.add(start_btn)

    ch_inf = types.InlineKeyboardButton(text='Изменить данные встречи', callback_data='2')
    keyboard.add(ch_inf)
    ch_time = types.InlineKeyboardButton(text='Изменить дату встречи', callback_data='3')
    keyboard.add(ch_time)
    statistic = types.InlineKeyboardButton(text='Посмотреть статистику встреч', callback_data='4')
    keyboard.add(statistic)

    bot.send_message(message.chat.id, greet, parse_mode='html', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def response(function_call) -> None:
    if function_call.message:
        if function_call.data == '1':
            init_vstr(function_call)
        elif function_call.data == '2':
            bot.send_message(function_call.message.chat.id, 'مغلق  ! Эта функция еще не готова.')
        elif function_call.data == '3':
            bot.send_message(function_call.message.chat.id, '關閉! Эта функция еще не готова.')
        elif function_call.data == '4':
            bot.send_message(function_call.message.chat.id, 'སྒོ་བརྒྱབ། ! Эта функция не готова.')


def init_vstr(function_call) -> None:
    msg_id = function_call.message.chat.id
    useransw[msg_id] = {}
    bot.send_message(msg_id, 'Название встречи ?')
    bot.register_next_step_handler(function_call.message, nazw_vstr)


def nazw_vstr(message):
    useransw[message.chat.id]['uno'] = message.text
    bot.send_message(message.chat.id, 'Напишите описание встречи')
    bot.register_next_step_handler(message, opsn_vstr)


def opsn_vstr(message):
    useransw[message.chat.id]['duo'] = message.text
    bot.send_message(
        message.chat.id,
        'Участники (почта)?\nВведите e-mail адреса участников, разделяя их запятыми или пробелами.'
    )
    bot.register_next_step_handler(message, uchastnik_vstr)


def uchastnik_vstr(message):
    email_input = message.text
    emails = parse_emails(email_input)
    if not emails:
        bot.send_message(message.chat.id, 'Неверный формат email-адресов. Пожалуйста, попробуйте снова.')
        bot.register_next_step_handler(message, uchastnik_vstr)
        return

    useransw[message.chat.id]['tree'] = emails
    bot.send_message(message.chat.id, 'Продолжительность (число минут)?')
    bot.register_next_step_handler(message, vrm_vstr)


def parse_emails(text: str):
    raw_emails = re.split('[,\\s]+', text.strip())
    email_pattern = re.compile(r"[^@]+@[^@]+\.[^@]+")
    valid_emails = [email for email in raw_emails if email_pattern.match(email)]
    return valid_emails if valid_emails else None


def vrm_vstr(message):
    chat_id = message.chat.id
    user_input = message.text

    if not user_input:
        prompt_error(chat_id)
        return

    duration = parse_duration(user_input)
    if duration is not None:
        useransw[chat_id]['quadro'] = duration
        prompt_next_step(chat_id, 'Введите время начала встречи в формате DD-MM HH:MM', meeting_start_time)
    else:
        prompt_error(chat_id)


def parse_duration(text: str):
    if not text.strip().isdigit():
        return None
    return int(text.strip())


def prompt_error(chat_id):
    bot.send_message(chat_id, 'Так не ясно. Нужно ввести число (количество минут).')
    bot.register_next_step_handler_by_chat_id(chat_id, vrm_vstr)


def prompt_next_step(chat_id, prompt_text, next_handler):
    bot.send_message(chat_id, prompt_text)
    bot.register_next_step_handler_by_chat_id(chat_id, next_handler)


def meeting_start_time(message):
    chat_id = message.chat.id
    useransw[chat_id]['cinque'] = message.text
    answers = useransw[chat_id]

    name = answers.get('uno')
    descr = answers.get('duo')
    guests = answers.get('tree')
    dur = answers.get('quadro')
    start_time_input = answers.get('cinque')

    try:
        start_time = datetime.strptime(start_time_input, '%d-%m %H:%M')
        start_time = start_time.replace(year=datetime.now().year)
    except ValueError:
        bot.send_message(
            message.chat.id,
            'Формат даты неверен. Попробуйте, например: 25-12 14:30 (дд-мм чч:мм).'
        )
        bot.register_next_step_handler(message, meeting_start_time)
        return

    end_time = start_time + timedelta(minutes=dur)

    # Сохраняем в БД
    participants_list = [message.from_user.id]
    meeting_id = db_handler.create_meeting(
        title=name,
        description=descr,
        start_time=start_time.isoformat(),
        end_time=end_time.isoformat(),
        participants=participants_list
    )

    event = google_calendar.create_event(
        summary=name,
        description=descr,
        start_time=start_time,
        end_time=end_time,
        attendees=guests
    )

    if event:
        bot.send_message(
            chat_id,
            f'Встреча "{name}" успешно создана (ID: {meeting_id}).\n'
            f'Ссылка на событие: {event.get("htmlLink")}'
        )
    else:
        bot.send_message(chat_id, 'Не удалось создать событие в календаре.')

    del useransw[chat_id]


@bot.message_handler(commands=['show_db'])
def show_db_content(message):
    for table_name in ['users', 'meetings', 'meeting_participants', 'statistics']:
        content = db_handler.get_table_content(table_name)
        if content:
            formatted_content = "\n".join([str(row) for row in content])
            bot.send_message(message.chat.id, f"Таблица {table_name}:\n{formatted_content}\n")
        else:
            bot.send_message(message.chat.id, f"Данных в таблице {table_name} нет.\n")



@bot.message_handler(commands=['auto_meeting'])
def auto_meeting_handler(message):

    chat_id = message.chat.id
    bot.send_message(chat_id, "Введите e-mail участников (не менее двух), разделяя пробелом или запятой:")
    bot.register_next_step_handler(message, auto_meeting_step_emails)

def auto_meeting_step_emails(message):
    chat_id = message.chat.id
    emails = parse_emails(message.text)
    if not emails or len(emails) < 2:
        bot.send_message(chat_id, "Нужно хотя бы 2 email. Попробуйте ещё раз /auto_meeting.")
        return

    useransw[chat_id] = {}
    useransw[chat_id]['emails'] = emails

    now_utc = datetime.now(timezone.utc)
    useransw[chat_id]['time_min'] = now_utc
    useransw[chat_id]['time_max'] = now_utc + timedelta(days=1)

    bot.send_message(chat_id, "На сколько минут нужно окно для встречи?")
    bot.register_next_step_handler(message, auto_meeting_step_duration)

def auto_meeting_step_duration(message):
    chat_id = message.chat.id
    if chat_id not in useransw:
        return

    try:
        dur = int(message.text.strip())
    except ValueError:
        bot.send_message(chat_id, "Нужно ввести число (минут). Отмена.")
        useransw.pop(chat_id, None)
        return

    emails = useransw[chat_id]['emails']
    time_min = useransw[chat_id]['time_min']
    time_max = useransw[chat_id]['time_max']

    slot = google_calendar.find_common_free_slot(
        attendees=emails,
        time_min=time_min,
        time_max=time_max,
        duration_minutes=dur
    )
    if slot is None:
        bot.send_message(chat_id, "Не нашли общего свободного времени на ближайший день.")
        useransw.pop(chat_id, None)
    else:
        s_dt, e_dt = slot
        useransw[chat_id]['slot'] = (s_dt, e_dt)
        useransw[chat_id]['duration'] = dur
        bot.send_message(
            chat_id,
            f"Свободный слот: {s_dt.strftime('%d-%m %H:%M')} - {e_dt.strftime('%d-%m %H:%M')}.\n"
            f"Создать встречу? (да/нет)"
        )
        bot.register_next_step_handler(message, auto_meeting_confirm)

def auto_meeting_confirm(message):
    chat_id = message.chat.id
    if chat_id not in useransw:
        return

    text = message.text.lower().strip()
    if text == 'да':

        emails = useransw[chat_id]['emails']
        s_dt, e_dt = useransw[chat_id]['slot']
        dur = useransw[chat_id]['duration']

        name = "Автоматическая встреча"
        descr = "Найдена ботом через freeBusy"

        meeting_id = db_handler.create_meeting(
            title=name,
            description=descr,
            start_time=s_dt.isoformat(),
            end_time=e_dt.isoformat(),
            participants=[message.from_user.id]
        )

        event = google_calendar.create_event(
            summary=name,
            description=descr,
            start_time=s_dt,
            end_time=e_dt,
            attendees=emails
        )
        if event:
            bot.send_message(
                chat_id,
                f"Встреча создана (ID {meeting_id}): {event.get('htmlLink')}"
            )
        else:
            bot.send_message(chat_id, "Ошибка при создании встречи.")
    else:
        bot.send_message(chat_id, "Отмена.")

    useransw.pop(chat_id, None)


@bot.message_handler(commands=['show_busy'])
def show_busy_handler(message):
    bot.send_message(message.chat.id, "Введите e-mail пользователя, чью занятость нужно посмотреть:")
    bot.register_next_step_handler(message, show_busy_email_step)

def show_busy_email_step(message):
    email = message.text.strip()

    now_utc = datetime.now(timezone.utc)
    week_later = now_utc + timedelta(days=7)

    body = {
        "timeMin": now_utc.isoformat(),
        "timeMax": week_later.isoformat(),
        "timeZone": "UTC",
        "items": [{"id": email}],
    }

    try:
        response = google_calendar.service.freebusy().query(body=body).execute()

        user_busy = response["calendars"][email]["busy"]
        if not user_busy:
            bot.send_message(message.chat.id, f"На ближайшие 7 дней у {email} нет занятых интервалов.")
            return

        msg = f"Занятость {email} (ближайшие 7 дней):\n"
        for block in user_busy:
            start_str = block['start']
            end_str = block['end']
            msg += f"   c {start_str} по {end_str}\n"

        bot.send_message(message.chat.id, msg)

    except DataError as e:
        bot.send_message(message.chat.id, f"Ошибка при freeBusy-запросе: {e}")

bot.infinity_polling()
