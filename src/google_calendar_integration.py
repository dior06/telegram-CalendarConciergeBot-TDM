import os
import pickle
import datetime
import logging
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from httplib2 import Credentials

SCOPES = ['https://www.googleapis.com/auth/calendar']

class GoogleCalendarIntegration:
    def __init__(self):
        self.service = None
        self.authenticate()

    def authenticate(self):
        creds = None
        if os.path.exists('src/token.json'):
            creds = self.load_credentials()
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                creds = self.get_new_credentials()

            self.save_credentials(creds)

        self.service = build('calendar', 'v3', credentials=creds)

    def load_credentials(self):
        try:
            creds = Credentials.from_authorized_user_file('src/token.json', SCOPES)
        except Exception as e:
            logging.error(f"Ошибка загрузки токенов: {e}")
            creds = None
        return creds

    def get_new_credentials(self):
        flow = InstalledAppFlow.from_client_secrets_file(
            'src/credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        return creds

    def save_credentials(self, creds):
        with open('src/token.json', 'w') as token:
            token.write(creds.to_json())

    def create_event(self, summary, start_time, end_time, description=None, location=None, attendees=None):
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
            'attendees': [{'email': attendee} for attendee in (attendees or [])],
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
