from unittest import mock
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
    assert 'Название встречи ?' in args


def test_init_vstr(mocker):
    bot_mock = mocker.patch('src.bot.bot')
    function_call = MagicMock()
    function_call.message.chat.id = 123

    bot.init_vstr(function_call)
    bot_mock.send_message.assert_called_once()
    args, kwargs = bot_mock.send_message.call_args
    assert 'Название встречи ?' in args


def test_nazw_vstr(mocker):
    bot_mock = mocker.patch('src.bot.bot')
    message = MagicMock()
    message.chat.id = 123
    message.text = 'Новая встреча'

    bot.nazw_vstr(message)
    bot_mock.send_message.assert_called_once()
    args, kwargs = bot_mock.send_message.call_args
    assert 'Напишите описание встречи' in args


def test_opsn_vstr(mocker):
    bot_mock = mocker.patch('src.bot.bot')
    message = MagicMock()
    message.chat.id = 123
    message.text = 'Описание для встречи'

    bot.opsn_vstr(message)
    bot_mock.send_message.assert_called_once()
    args, kwargs = bot_mock.send_message.call_args
    assert 'Участники (почта)?\nВведите e-mail адреса участников, разделяя их запятыми или пробелами.' in args


def test_uchastnik_vstr(mocker):
    bot_mock = mocker.patch('src.bot.bot')
    message = MagicMock()
    message.chat.id = 123
    message.text = 'user1@example.com, user2@anotherexample.com'

    bot.uchastnik_vstr(message)
    bot_mock.send_message.assert_called_once()
    args, kwargs = bot_mock.send_message.call_args
    assert 'Продолжительность (число минут)?' in args[1]


def test_vrm_vstr(mocker):
    bot_mock = mocker.patch('src.bot.bot')
    message = MagicMock()
    message.chat.id = 123
    message.text = '30'

    bot.vrm_vstr(message)
    bot_mock.send_message.assert_called_once()
    args, kwargs = bot_mock.send_message.call_args
    assert 'Введите время начала встречи в формате DD-MM HH:MM' in args[1]


def test_vrm_vstr_incorrect(mocker):
    bot_mock = mocker.patch('src.bot.bot')
    message = MagicMock()
    message.chat.id = 123
    message.text = 'abc'

    bot.vrm_vstr(message)
    bot_mock.send_message.assert_called_once()
    args, kwargs = bot_mock.send_message.call_args
    assert 'Так не ясно. Нужно ввести число (количество минут).' in args[1]


def test_show_db_content(mocker):
    bot_mock = mocker.patch('src.bot.bot')
    db_handler_mock = mocker.patch('src.bot.db_handler')

    db_handler_mock.get_table_content.side_effect = [
        [('id1', 'name1', '2024-01-01', '2024-01-02')],
        [('id2', 'name2', '2024-02-01', '2024-02-02')],
        [],
        [('id4', 'name4', '2024-04-01', '2024-04-02')],
    ]

    message = MagicMock()
    message.chat.id = 123

    bot.show_db_content(message)

    assert bot_mock.send_message.call_count == 4

    expected_calls = [
        mocker.call(message.chat.id, "Таблица users:\n('id1', 'name1', '2024-01-01', '2024-01-02')\n"),
        mocker.call(message.chat.id, "Таблица meetings:\n('id2', 'name2', '2024-02-01', '2024-02-02')\n"),
        mocker.call(message.chat.id, 'Данных в таблице meeting_participants нет.\n'),
        mocker.call(message.chat.id, "Таблица statistics:\n('id4', 'name4', '2024-04-01', '2024-04-02')\n"),
    ]

    bot_mock.send_message.assert_has_calls(expected_calls, any_order=False)


def test_meeting_start_time_correct_format(mocker):
    bot_mock = mocker.patch('src.bot.bot')
    google_calendar_mock = mocker.patch('src.bot.google_calendar')

    message = MagicMock()
    message.chat.id = 123
    message.text = '23-12 15:30'
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
