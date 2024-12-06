import os
import pickle
import datetime
import logging
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from httplib2 import Credentials

# Если измените этот SCOPES, удалите файл token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']

class GoogleCalendarIntegration:
    def __init__(self):
        self.service = None
        self.authenticate()

    def authenticate(self):
        """Авторизация и получение токенов доступа."""
        creds = None
        # Проверяем, есть ли файл с токеном
        if os.path.exists('token.json'):
            creds = self.load_credentials()
        
        # Если нет токенов или они недействительны, проводим авторизацию
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                creds = self.get_new_credentials()

            self.save_credentials(creds)

        # Строим сервис
        self.service = build('calendar', 'v3', credentials=creds)

    def load_credentials(self):
        """Загрузка токенов из файла."""
        try:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        except Exception as e:
            logging.error(f"Ошибка загрузки токенов: {e}")
            creds = None
        return creds

    def get_new_credentials(self):
        """Запрос на получение новых учетных данных."""
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        return creds

    def save_credentials(self, creds):
        """Сохранение токенов в файл."""
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    def create_event(self, summary, start_time, end_time, description=None, location=None, attendees=None):
        """Создание события в календаре Google."""
        if not self.service:
            logging.error("Сервис Google Calendar не инициализирован.")
            return
        
        event = {
            'summary': summary,
            'location': location,
            'description': description,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'UTC',
            },
            'attendees': [{'email': attendee} for attendee in (attendees or [])],  # добавляем участников
            'reminders': {
                'useDefault': True,
            },
        }

        try:
            event = self.service.events().insert(calendarId='primary', body=event).execute()
            logging.info(f"Событие создано: {event.get('htmlLink')}")
            return event
        except HttpError as error:
            logging.error(f"Произошла ошибка при создании события: {error}")
            return None


if __name__ == '__main__':
    # Пример создания события
    google_calendar = GoogleCalendarIntegration()

    # Убедитесь, что указываете правильный формат времени
    start_time = datetime.datetime(2024, 12, 7, 10, 0, 0)
    end_time = datetime.datetime(2024, 12, 7, 11, 0, 0)

    # Пример создания события
    event = google_calendar.create_event(
        summary='Важная встреча',
        start_time=start_time,
        end_time=end_time,
        description='Описание события',
        location='Место проведения'
    )

    if event:
        print(f"Событие успешно создано: {event.get('htmlLink')}")
