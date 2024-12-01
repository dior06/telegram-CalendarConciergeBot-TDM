import sqlite3
import typing as tp
from datetime import datetime, timedelta


class DataBaseHandler:
    def __init__(self, db_name: str = "calendar_concierge_bot_tdm.db") -> None:
        self.conn = sqlite3.connect(db_name)
        self.create_tables()

    def create_tables(self) -> None:
        cursor = self.conn.cursor()

        # table of users
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            )
        '''
        )

        # table of meetings
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS meetings (
                meeting_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP NOT NULL,
                status TEXT DEFAULT 'scheduled',
            )
        '''
        )

        # table of meeting participants
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS meeting_participants (
                meeting_id INTEGER,
                user_id INTEGER,
                PRIMARY KEY (meeting_id, user_id),
                FOREIGN KEY (meeting_id) REFERENCES meetings(meeting_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id),
            )
        '''
        )

        # table of statistics
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS statistics (
                stat_id INTEGET PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                week_start_date DATE,
                meeting_count INTREGER,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        '''
        )

        self.conn.commit()

    # adding new user to the data base in case if he is not there
    def add_user(self, user_id: int, username: str, first_name: str, last_name: str) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            '''
            INSERT OR IGNORE INTO users (user_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        ''',
            (user_id, username, first_name, last_name),
        )

        self.conn.commit()

    # creating meeting and connecting it with meeting participants
    def create_meeting(
        self, title: str, description: str, start_time: str, end_time: str, participants: tp.List[int]
    ) -> int | None:
        cursor = self.conn.cursor()
        cursor.execute(
            '''
            INSERT INTO meetings (title, desctiption, start_time, end_time)
            VALUES (?, ?, ?, ?)
        ''',
            (title, description, start_time, end_time),
        )

        meeting_id = cursor.lastrowid

        for user_id in participants:
            cursor.execute(
                '''
                INSERT INTO meeting_participants (meeting_id, user_id)
                VALUES (?, ?)
            ''',
                (meeting_id, user_id),
            )

        self.conn.commit()
        return meeting_id

    # getting list of meetings for current user
    def get_user_meetings(self, user_id: int) -> list:
        cursor = self.conn.cursor()
        cursor.execute(
            '''
            SELECT m.title, m.description, m.start_time, m.end_time, m.status
            FROM meetings m
            JOING meeting_participants mp ON m.meeting_id = mp.meeting_id
            WHERE mp.user_id = ?
            ORDER BY m.start_time
        ''',
            (user_id,),
        )

        return cursor.fetchall()

    # updating status for current meeting
    def update_meeting_status(self, meeting_id: int, new_status: str) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            '''
            UPDATE meetings
            SET status = ?
            WHERE meeting_id = ?
        ''',
            (meeting_id, new_status),
        )

        self.conn.commit()

    # collecting and updating statistics
    def collect_statistics(self) -> None:
        cursor = self.conn.cursor()

        today: datetime = datetime.today()
        start_of_the_week: datetime = today - timedelta(days=today.weekday())
        start_of_the_week_str = start_of_the_week.strftime('%Y-%m-%d')

        cursor.execute(
            '''
            SELECT mp.user_id, COUNT(m.meeting_id)
            FROM meetings m
            JOIN meeting_participants mp ON m.meeting_id = mp.meeting_id
            WHERTE DATE(m.start_time) >= ?
            GROUP BY mp.user_id
        ''',
            (start_of_the_week_str,),
        )
        statistics = cursor.fetchall()

        for user_id, meeting_count in statistics:
            cursor.execute(
                '''
                INSERT OR REPLACE INTO statistics (user_id, week_start_date, meeting_count)
                VALUES (?, ?, ?)
            ''',
                (user_id, start_of_the_week, meeting_count),
            )

        self.conn.commit()

    # getting meeting statistics for current user
    def get_user_statistics(self, user_id: int):
        cursor = self.conn.cursor()

        today = datetime.today()
        start_of_the_week = today - timedelta(days=today.weekday())
        start_of_the_week_str = start_of_the_week.strftime('%Y-%m-%d')

        cursor.execute(
            '''
            SELECT meeting_count
            FROM statistics
            WHERE user_id = ? AND week_start_date = ?
        ''',
            (user_id, start_of_the_week_str),
        )

        result = cursor.fetchone()
        return result[0] if result else 0

    def close_database(self) -> None:
        self.conn.close()
