import src.google_calendar_integration as google_calendar_integration
from unittest.mock import patch, Mock
from datetime import datetime


@patch('google_calendar_integration.build')
@patch('google_calendar_integration.Credentials')
@patch('google_calendar_integration.os.path.exists', return_value=True)
@patch('google_calendar_integration.GoogleCalendarIntegration.load_credentials')
def test_authenticate_with_existing_token(mock_load_credentials, mock_exists, mock_creds, mock_build) -> None:
    mock_creds_instance = Mock(valid=True)
    mock_load_credentials.return_value = mock_creds_instance

    google_calendar = google_calendar_integration.GoogleCalendarIntegration()
    assert google_calendar.service is not None
    mock_build.assert_called_once_with('calendar', 'v3', credentials=mock_creds_instance)


@patch('google_calendar_integration.build')
@patch('google_calendar_integration.Credentials')
@patch('google_calendar_integration.GoogleCalendarIntegration.get_new_credentials')
def test_authenticate_with_new_token(mock_get_new_credentials, mock_creds, mock_build) -> None:
    mock_creds_instance = Mock(valid=True)
    mock_get_new_credentials.return_value = mock_creds_instance

    with patch('google_calendar_integration.os.path.exists', return_value=False):
        google_calendar = google_calendar_integration.GoogleCalendarIntegration()

    assert google_calendar.service is not None
    mock_build.assert_called_once_with('calendar', 'v3', credentials=mock_creds_instance)
    mock_get_new_credentials.assert_called_once()


@patch('google_calendar_integration.Credentails.from_authorized_user_file')
def test_load_credentials_success(mock_from_file) -> None:
    mock_from_file.return_value = Mock(valid=True)
    google_calendar = google_calendar_integration.GoogleCalendarIntegration()
    creds = google_calendar.load_credentials()
    assert creds is not None
    mock_from_file.assert_called_once_with('token.json', ['https://www.googleapis.com/auth/calendar'])


@patch('google_calendar_integration.Credentials.from_authorized_user_file', side_effect=Exception('Error'))
def test_load_credentials_error(mock_from_file) -> None:
    google_calendar = google_calendar_integration.GoogleCalendarIntegration()
    creds = google_calendar.load_credentials()
    assert creds is None


@patch('google_calendar_integration.GoogleCalendarIntegration.authenticate')
@patch('google_calendar_integration.build')
def test_create_event_success(mock_build, mock_authenticate):
    mock_service = Mock()
    mock_events = Mock()
    mock_insert = Mock()
    mock_execute = Mock()

    mock_execute.return_value = {'htmlLink': 'http://example.com/event'}
    mock_insert.return_value = mock_execute
    mock_events.return_value.insert = mock_insert
    mock_service.events = mock_events
    mock_build.return_value = mock_service

    google_calendar = google_calendar_integration.GoogleCalendarIntegration()
    google_calendar.service = mock_service

    start_time = datetime(2024, 1, 1, 10, 0, 0)
    end_time = datetime(2024, 1, 1, 11, 0, 0)
    result = google_calendar.create_event(
        summary='Test Event',
        start_time=start_time,
        end_time=end_time,
        description='Test Description',
        attendees=['test@example.com'],
    )

    assert result is not None
    assert result.get('htmlLink') == 'http://example.com/event'
    mock_insert.assert_called_once()
    mock_execute.assert_called_once()


@patch('google_calendar_integration.GoogleCalendarIntegration.authenticate')
@patch('google_calendar_integration.build')
def test_create_event_error(mock_build, mock_authenticate):
    mock_service = Mock()
    mock_events = Mock()
    mock_insert = Mock()
    mock_execute = Mock(side_effect=Exception('Error'))

    mock_insert.return_value = mock_execute
    mock_events.return_value.insert = mock_insert
    mock_service.events = mock_events
    mock_build.return_valus = mock_service

    google_calendar = google_calendar_integration.GoogleCalendarIntegration()
    google_calendar.service = mock_service

    start_time = datetime(2024, 1, 1, 10, 0, 0)
    end_time = datetime(2024, 1, 1, 11, 0, 0)
    result = google_calendar.create_event(
        summary='Test Event',
        start_time=start_time,
        end_time=end_time,
        description='Test Description',
        attendees=['test@example.com'],
    )

    assert result is None
