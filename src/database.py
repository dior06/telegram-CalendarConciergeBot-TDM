import sqlite3
from sqlite3 import Error
from typing import List, Tuple
import threading

local = threading.local()

class DataBaseHandler:
    def __init__(self, db_file='meetings.db'):
        self.db_file = db_file
        self.create_tables()  

    def create_connection(self):
        if not hasattr(local, 'db_connection'):
            try:
                local.db_connection = sqlite3.connect(self.db_file, check_same_thread=False)  
                local.db_connection.row_factory = sqlite3.Row  
                print(f"Подключение к базе данных установлено: {self.db_file}")
            except Error as e:
                print(f"Ошибка подключения к базе данных: {e}")
                raise
        return local.db_connection

    def create_tables(self):
        create_meetings_table = """
        CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL
        );
        """

        create_users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            first_name TEXT,
            last_name TEXT,
            username TEXT
        );
        """

        create_participants_table = """
        CREATE TABLE IF NOT EXISTS meeting_participants (
            meeting_id INTEGER,
            user_id INTEGER,
            FOREIGN KEY (meeting_id) REFERENCES meetings (id),
            FOREIGN KEY (user_id) REFERENCES users (id),
            PRIMARY KEY (meeting_id, user_id)
        );
        """

        create_statistics_table = """
        CREATE TABLE IF NOT EXISTS statistics (
            user_id INTEGER,
            meetings_created INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
        """

        try:
            conn = self.create_connection()
            cursor = conn.cursor()
            cursor.execute(create_meetings_table)
            cursor.execute(create_users_table)
            cursor.execute(create_participants_table)
            cursor.execute(create_statistics_table)
            conn.commit()
            print("Таблицы успешно созданы или уже существуют.")
        except Error as e:
            print(f"Ошибка при создании таблиц: {e}")

    def add_user(self, user_id: int, first_name: str, last_name: str, username: str):
        try:
            conn = self.create_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO users (user_id, first_name, last_name, username)
                VALUES (?, ?, ?, ?)
            """, (user_id, first_name, last_name, username))
            conn.commit()
        except Error as e:
            print(f"Ошибка при добавлении пользователя: {e}")

    def get_user(self, user_id: int) -> Tuple[int, str, str, str]:
        conn = self.create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        return cursor.fetchone()

    def create_meeting(self, title: str, description: str, start_time: str, end_time: str, participants: List[int]) -> int:
        try:
            conn = self.create_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO meetings (title, description, start_time, end_time)
                VALUES (?, ?, ?, ?)
            """, (title, description, start_time, end_time))
            meeting_id = cursor.lastrowid
            conn.commit()

            for user_id in participants:
                cursor.execute("""
                    INSERT INTO meeting_participants (meeting_id, user_id)
                    VALUES (?, ?)
                """, (meeting_id, user_id))
            conn.commit()
            return meeting_id
        except Error as e:
            print(f"Ошибка при создании встречи: {e}")
            return None

    def get_meeting(self, meeting_id: int) -> Tuple[int, str, str, str, str]:
        conn = self.create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM meetings WHERE id=?", (meeting_id,))
        return cursor.fetchone()

    def get_meetings_for_user(self, user_id: int) -> List[Tuple[int, str, str, str, str]]:
        conn = self.create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.id, m.title, m.description, m.start_time, m.end_time
            FROM meetings m
            JOIN meeting_participants mp ON m.id = mp.meeting_id
            WHERE mp.user_id=?
        """, (user_id,))
        return cursor.fetchall()

    def get_participants_for_meeting(self, meeting_id: int) -> List[Tuple[int, str, str, str]]:
        conn = self.create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.user_id, u.first_name, u.last_name, u.username
            FROM users u
            JOIN meeting_participants mp ON u.user_id = mp.user_id
            WHERE mp.meeting_id=?
        """, (meeting_id,))
        return cursor.fetchall()

    def update_statistics(self, user_id: int):
        conn = self.create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO statistics (user_id, meetings_created)
            VALUES (?, COALESCE((SELECT meetings_created FROM statistics WHERE user_id=?), 0) + 1)
        """, (user_id, user_id))
        conn.commit()

    def get_user_statistics(self, user_id: int) -> int:
        conn = self.create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT meetings_created FROM statistics WHERE user_id=?", (user_id,))
        result = cursor.fetchone()
        return result[0] if result else 0

    def get_table_content(self, table_name: str) -> List[Tuple]:
        conn = self.create_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        return cursor.fetchall()

    def close_connection(self):
        if hasattr(local, 'db_connection'):
            local.db_connection.close()
            print("Подключение к базе данных закрыто.")



if __name__ == "__main__":
    db_handler = DataBaseHandler()

    db_handler.add_user(12345, "Иван", "Иванов", "ivan_ivanov")
    
 
    meeting_id = db_handler.create_meeting(
        title="Совещание",
        description="Обсуждение важных вопросов",
        start_time="2024-12-10 14:00",
        end_time="2024-12-10 15:00",
        participants=[12345]  
    )

    db_handler.update_statistics(12345)

    print(f"Встречи создано: {db_handler.get_user_statistics(12345)}")

    meetings = db_handler.get_meetings_for_user(12345)
    print("Встречи пользователя:", meetings)

    participants = db_handler.get_participants_for_meeting(meeting_id)
    print("Участники встречи:", participants)

    db_handler.close_connection()
