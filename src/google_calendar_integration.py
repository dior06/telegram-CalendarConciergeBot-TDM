import os
import logging
from datetime import datetime, timedelta, timezone
 
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
 
SCOPES = ['https://www.googleapis.com/auth/calendar']
 
class GoogleCalendarIntegration:
    def __init__(self):
        self.service = None
        self.authenticate()
 
    def authenticate(self):
        creds = None
 
        if os.path.exists('token.json'):
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
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            return creds
        except Exception as e:
            logging.error(f"Ошибка загрузки токенов: {e}")
            return None
 
    def get_new_credentials(self):

        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        return creds
 
    def save_credentials(self, creds):

        with open('token.json', 'w') as token_file:
            token_file.write(creds.to_json())
 
    def find_common_free_slot(self, attendees, time_min, time_max, duration_minutes=30):
        if not self.service:
            logging.error("Сервис Google Calendar не инициализирован.")
            return None

        body = {
            "timeMin": time_min.isoformat(),
            "timeMax": time_max.isoformat(),
            "timeZone": "UTC",
            "items": [{"id": email} for email in attendees],
        }
 
        try:
            response = self.service.freebusy().query(body=body).execute()
            logging.info(f"[find_common_free_slot] FreeBusy response:\n{response}")
        except HttpError as e:
            logging.error(f"Ошибка freeBusy-запроса: {e}")
            return None
 
        busy_blocks = []
        for email in attendees:
            user_busy = response["calendars"][email]["busy"]
            for block in user_busy:
                start_busy_str = block["start"]
                end_busy_str = block["end"]
                busy_blocks.append((start_busy_str, end_busy_str))
 
        busy_blocks_dt = []
        for (start_str, end_str) in busy_blocks:
            s_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
            e_dt = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
            busy_blocks_dt.append((s_dt, e_dt))
 
        busy_blocks_dt.sort(key=lambda x: x[0])
        logging.debug(f"[find_common_free_slot] Sorted busy blocks: {busy_blocks_dt}")
 
        merged_busy = []
        for block in busy_blocks_dt:
            if not merged_busy:
                merged_busy.append(block)
            else:
                prev_start, prev_end = merged_busy[-1]
                curr_start, curr_end = block
                if curr_start <= prev_end:
                    merged_busy[-1] = (prev_start, max(prev_end, curr_end))
                else:
                    merged_busy.append(block)
 
        logging.debug(f"[find_common_free_slot] Merged busy blocks: {merged_busy}")
 
        current_start = time_min
        for (busy_start, busy_end) in merged_busy:
            if busy_start > current_start:
                free_delta = (busy_start - current_start).total_seconds() / 60
                if free_delta >= duration_minutes:
                    return (current_start, current_start + timedelta(minutes=duration_minutes))
 
            if busy_end > current_start:
                current_start = busy_end
 
        if current_start < time_max:
            tail_delta = (time_max - current_start).total_seconds() / 60
            if tail_delta >= duration_minutes:
                return (current_start, current_start + timedelta(minutes=duration_minutes))
 
        return None
 
    def create_event(self, summary, start_time, end_time,
                     description=None, location=None, attendees=None):

        if not self.service:
            logging.error("Сервис Google Calendar не инициализирован.")
            return None
 
        event_body = {
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
            'attendees': [{'email': email} for email in (attendees or [])],
            'reminders': {
                'useDefault': True,
            },
        }
 
        try:
            created_event = self.service.events().insert(
                calendarId='primary',
                body=event_body
            ).execute()
            logging.info(f"Событие создано: {created_event.get('htmlLink')}")
            return created_event
        except HttpError as error:
            logging.error(f"Произошла ошибка при создании события: {error}")
            return None
