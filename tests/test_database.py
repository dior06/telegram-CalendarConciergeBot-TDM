import unittest
from src.database import DataBaseHandler

class TestDataBaseHandler(unittest.TestCase):
    def __init__(self, methodName="runTest"):
        super().__init__(methodName)
        self.db_handler = DataBaseHandler(db_file=':memory:')
        self.clear_database()

    def clear_database(self):
        conn = self.db_handler.create_connection()
        cursor = conn.cursor()
        cursor.executescript(
            """
            DELETE FROM meeting_participants;
            DELETE FROM statistics;
            DELETE FROM meetings;
            DELETE FROM users;
            """
        )
        conn.commit()

    def test_create_tables(self):
        tables = ["meetings", "users", "meeting_participants", "statistics"]
        for table in tables:
            result = self.db_handler.get_table_content(table)
            self.assertEqual(len(result), 0)

    def test_add_user_and_get_user(self):
        self.db_handler.add_user(1, "John", "Doe", "johndoe")
        user = self.db_handler.get_user(1)
        self.assertIsNotNone(user)
        self.assertEqual(user[2], "John")
        self.assertEqual(user[3], "Doe")
        self.assertEqual(user[-1], "johndoe")

    def test_create_and_get_meeting(self):
        self.db_handler.add_user(1, "John", "Doe", "johndoe")
        meeting_id = self.db_handler.create_meeting(
            title="Team Meeting",
            description="Discuss project",
            start_time="2024-12-25 10:00:00",
            end_time="2024-12-25 11:00:00",
            participants=[1],
        )
        self.assertIsNotNone(meeting_id)
        meeting = self.db_handler.get_meeting(meeting_id)
        self.assertIsNotNone(meeting)
        self.assertEqual(meeting[1], "Team Meeting")

    def test_get_meetings_for_user(self):
        self.db_handler.add_user(1, "John", "Doe", "johndoe")
        self.db_handler.add_user(2, "Jane", "Smith", "janesmith")
        self.db_handler.create_meeting(
            title="Team Meeting",
            description="Discuss project",
            start_time="2024-12-25 10:00:00",
            end_time="2024-12-25 11:00:00",
            participants=[1, 2],
        )
        meetings = self.db_handler.get_meetings_for_user(1)
        self.assertEqual(len(meetings), 1)
        self.assertEqual(meetings[0][1], "Team Meeting")

    def test_get_participants_for_meeting(self):
        self.db_handler.add_user(1, "John", "Doe", "johndoe")
        self.db_handler.add_user(2, "Jane", "Smith", "janesmith")
        meeting_id = self.db_handler.create_meeting(
            title="Team Meeting",
            description="Discuss project",
            start_time="2024-12-25 10:00:00",
            end_time="2024-12-25 11:00:00",
            participants=[1, 2],
        )
        participants = self.db_handler.get_participants_for_meeting(meeting_id)
        self.assertEqual(len(participants), 2)

    def test_update_and_get_statistics(self):
        self.db_handler.add_user(1, "John", "Doe", "johndoe")
        self.db_handler.update_statistics(1)
        self.db_handler.update_statistics(1)
        stats = self.db_handler.get_user_statistics(1)
        self.assertEqual(stats, 2)

    def test_tearDown(self):
        self.db_handler.close_connection()
