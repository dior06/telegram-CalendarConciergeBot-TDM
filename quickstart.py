import os
import pickle
import datetime
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Если измените этот скоуп, удалите файл token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def authenticate():
    """Авторизация через OAuth 2.0 и создание сервисного объекта."""
    creds = None
    # Файл token.pickle хранит токен пользователя и используется для повторного входа
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # Если нет валидных учетных данных, выполняем авторизацию
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Сохраняем учетные данные для следующего использования
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds

def list_events():
    """Получаем и выводим события из Google Calendar."""
    creds = authenticate()
    service = build('calendar', 'v3', credentials=creds)

    # Получаем текущую дату и дату через 30 дней
    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' означает UTC время
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                          maxResults=10, singleEvents=True,
                                          orderBy='startTime').execute()

    events = events_result.get('items', [])

    if not events:
        print('Нет предстоящих событий.')
    else:
        print('Предстоящие события:')
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(f"{event['summary']} ({start})")

if __name__ == '__main__':
    list_events()
