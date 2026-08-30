import sqlite3
from pathlib import Path


# Database will be created in the TUTIVRA project root.
DATABASE_PATH = Path(__file__).resolve().parents[2] / "tutivra.db"


def get_connection():
    """Create and return a SQLite database connection."""

    return sqlite3.connect(DATABASE_PATH)


def initialize_database():
    """Create the required database tables."""

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            level TEXT NOT NULL DEFAULT 'beginner'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topic_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            topic TEXT NOT NULL,
            mastery REAL NOT NULL DEFAULT 0.0,
            attempts INTEGER NOT NULL DEFAULT 0,
            correct_answers INTEGER NOT NULL DEFAULT 0,
            misconceptions TEXT NOT NULL DEFAULT '',
            UNIQUE(student_id, topic),
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    """)

    connection.commit()
    connection.close()


def get_or_create_student(
    name: str,
    level: str = "beginner",
):
    """Get an existing student or create a new one."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT id, name, level FROM students WHERE name = ?",
        (name,),
    )

    student = cursor.fetchone()

    if student:
        connection.close()
        return student

    cursor.execute(
        """
        INSERT INTO students (name, level)
        VALUES (?, ?)
        """,
        (name, level),
    )

    connection.commit()

    student_id = cursor.lastrowid

    connection.close()

    return (
        student_id,
        name,
        level,
    )


def load_topic_progress(
    student_id: int,
    topic: str,
):
    """Load saved progress for a specific topic."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            mastery,
            attempts,
            correct_answers,
            misconceptions
        FROM topic_progress
        WHERE student_id = ?
        AND topic = ?
        """,
        (student_id, topic),
    )

    progress = cursor.fetchone()

    connection.close()

    return progress


def save_topic_progress(
    student_id: int,
    topic: str,
    mastery: float,
    attempts: int,
    correct_answers: int,
    misconceptions: list,
):
    """Save or update progress for a topic."""

    connection = get_connection()
    cursor = connection.cursor()

    misconception_text = "\n".join(misconceptions)

    cursor.execute(
        """
        INSERT INTO topic_progress (
            student_id,
            topic,
            mastery,
            attempts,
            correct_answers,
            misconceptions
        )
        VALUES (?, ?, ?, ?, ?, ?)

        ON CONFLICT(student_id, topic)
        DO UPDATE SET
            mastery = excluded.mastery,
            attempts = excluded.attempts,
            correct_answers = excluded.correct_answers,
            misconceptions = excluded.misconceptions
        """,
        (
            student_id,
            topic,
            mastery,
            attempts,
            correct_answers,
            misconception_text,
        ),
    )

    connection.commit()
    connection.close()