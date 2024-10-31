import telebot
from telebot import types


bot = telebot.TeleBot('7287404688:AAGFVPNVBsg9R6ASpRxp35wiK0la9T7IXhk')


def greeting(message) -> str:
    username: str = message.from_user.first_name
    if message.from_user.last_name:
        username += ' ' + message.from_user.last_name

    greeting_message: str = f"<b>{username}</b>, Привет!\nХочешь расскажу немного о себе?"

    return greeting_message


@bot.message_handler(commands=['start'])
def start_bot(message) -> None:
    greeting_message: str = greeting(message)

    keyboard = types.InlineKeyboardMarkup()
    key_yes = types.InlineKeyboardButton(text='Да', callback_data='yes')
    keyboard.add(key_yes)
    key_no = types.InlineKeyboardButton(text='Нет', callback_data='no')
    keyboard.add(key_no)

    bot.send_message(message.chat.id, greeting_message, parse_mode='html', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def response(function_call) -> None:
    if function_call.message:
        if function_call.data == 'yes':
            description_message: str = (
                'Я телеграм-бот, назначающий встречи в календаре. Более подробно можешь узнать на нашем сайте!'
            )
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(
                types.InlineKeyboardButton(
                    'Перейти на сайт',
                    url='https://github.com/dior06/telegram-CalendarConciergeBot-TDM',
                )
            )
            bot.send_message(function_call.message.chat.id, description_message, reply_markup=keyboard)
            bot.answer_callback_query(function_call.id)
        elif function_call.data == 'no':
            bot.send_message(function_call.message.chat.id, ':(')


bot.infinity_polling()
