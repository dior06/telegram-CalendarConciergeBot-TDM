import src.bot as bot
from unittest.mock import MagicMock


def test_greeting():
    message = MagicMock()
    message.from_user.first_name = "Иван"
    message.from_user.last_name = "Васильевич"

    expected_message = "Салам Алейкум, <b>Иван Васильевич</b>, что бы вы хотели сделать?"
    assert bot.greeting(message) == expected_message

    message.from_user.last_name = None
    expected_message = "Салам Алейкум, <b>Иван</b>, что бы вы хотели сделать?"
    assert bot.greeting(message) == expected_message


def test_start_bot(mocker):
    bot_mock = mocker.patch('src.bot.bot')
    message = MagicMock()
    message.chat.id = 123
    bot.start_bot(message)

    bot_mock.send_message.assert_called_once()
    args, kwargs = bot_mock.send_message.call_args
    assert message.chat.id in args
    assert 'Салам Алейкум' in args[1]


def test_responce_callback_creation(mocker):
    bot_mock = mocker.patch('src.bot.bot')
    function_call = MagicMock()
    function_call.message.chat.id = 123
    function_call.data = '1'

    bot.response(function_call)
    bot_mock.send_message.assert_called_once()
    args, kwargs = bot_mock.send_message.call_args
    assert 'Введите название встречи' in args


def test_meeting_creation(mocker):
    bot_mock = mocker.patch('src.bot.bot')
    function_call = MagicMock()
    function_call.message.chat.id = 123

    bot.meeting_creation(function_call)
    bot_mock.send_message.assert_called_once()
    args, kwargs = bot_mock.send_message.call_args
    assert 'Введите название встречи' in args


def test_meeting_title(mocker):
    bot_mock = mocker.patch('src.bot.bot')
    message = MagicMock()
    message.chat.id = 123
    message.text = 'Новая встреча'

    bot.meeting_title(message)
    bot_mock.send_message.assert_called_once()
    args, kwargs = bot_mock.send_message.call_args
    assert 'Описание встречи по-братски напиши' in args


def test_meeting_description(mocker):
    bot_mock = mocker.patch('src.bot.bot')
    message = MagicMock()
    message.chat.id = 123
    message.text = 'Описание для встречи'

    bot.meeting_description(message)
    bot_mock.send_message.assert_called_once()
    args, kwargs = bot_mock.send_message.call_args
    assert 'Участники?' in args


def test_meeting_members(mocker):
    bot_mock = mocker.patch('src.bot.bot')
    message = MagicMock()
    message.chat.id = 123
    message.text = 'user1, user2'

    bot.meeting_members(message)
    bot_mock.send_message.assert_called_once()
    args, kwargs = bot_mock.send_message.call_args
    assert 'Продолжительность' in args[1]


def test_meeting_time_correct(mocker):
    bot_mock = mocker.patch('src.bot.bot')
    message = MagicMock()
    message.chat.id = 123
    message.text = '30'

    bot.meeting_time(message)
    bot_mock.send_message.assert_called_once()
    args, kwargs = bot_mock.send_message.call_args
    assert 'Введите время начала встречи' in args[1]


def test_meeting_time_incorrect(mocker):
    bot_mock = mocker.patch('src.bot.bot')
    message = MagicMock()
    message.chat.id = 123
    message.text = 'abc'

    bot.meeting_time(message)
    bot_mock.send_message.assert_called_once()
    args, kwargs = bot_mock.send_message.call_args
    assert 'Нужно ввести число' in args[1]


def test_show_db_content(mocker):
    bot_mock = mocker.patch('src.bot.bot')
    db_handler_mock = mocker.patch('src.bot.db_handler')
    db_handler_mock.get_table_content.return_value = [('id', 'name', '2024-01-01', '2024-01-02')]

    message = MagicMock()
    message.chat.id = 123

    bot.show_db_content(message)
    bot_mock.send_message.assert_called_once()
    args, kwargs = bot_mock.send_message.call_args
    assert 'Содержимое таблицы' in args[1]


def test_meeting_start_time_correct_format(mocker):
    bot_mock = mocker.patch('src.bot.bot')
    google_calendar_mock = mocker.patch('src.bot.google_calendar')

    message = MagicMock()
    message.chat.id = 123
    message.text = '2024-12-07 15:30:00'
    message.from_user.id = 1

    user_data = {
        123: {
            'answer1': 'Тестовая встреча',
            'answer2': 'Описание встречи',
            'answer3': 'user1, user2',
            'answer4': 60,
            'answer5': message.text,
        }
    }

    google_calendar_mock.create_event.return_value = {'htmlLink': 'http://example.com/event'}

    bot.meeting_start_time(message)
    bot_mock.send_message.assert_called_once()
    args, kwargs = bot_mock.send_message.call_args
    assert 'Встреча' in args[1]
    assert 'http://example.com/event' in args[1]
