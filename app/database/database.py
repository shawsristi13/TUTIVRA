import sqlite3
from pathlib import Path


# ============================================================
# DATABASE PATH
# ============================================================

# Database will be created in the TUTIVRA project root.
DATABASE_PATH = (
    Path(__file__).resolve().parents[2]
    / "tutivra.db"
)


# ============================================================
# CONNECTION
# ============================================================

def get_connection():
    """Create and return a SQLite database connection."""

    return sqlite3.connect(
        DATABASE_PATH
    )


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():
    """Create all required database tables."""

    connection = get_connection()

    cursor = connection.cursor()

    # --------------------------------------------------------
    # STUDENTS TABLE
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            level TEXT NOT NULL DEFAULT 'beginner'
        )
    """)

    # --------------------------------------------------------
    # TOPIC PROGRESS TABLE
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topic_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            student_id INTEGER NOT NULL,

            topic TEXT NOT NULL,

            mastery REAL NOT NULL DEFAULT 0.0,

            attempts INTEGER NOT NULL DEFAULT 0,

            correct_answers INTEGER
            NOT NULL DEFAULT 0,

            misconceptions TEXT
            NOT NULL DEFAULT '',

            UNIQUE(student_id, topic),

            FOREIGN KEY(student_id)
            REFERENCES students(id)
        )
    """)

    # --------------------------------------------------------
    # CONCEPT PROGRESS TABLE
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS concept_progress (

            id INTEGER
            PRIMARY KEY AUTOINCREMENT,

            student_id INTEGER NOT NULL,

            topic TEXT NOT NULL,

            concept TEXT NOT NULL,

            mastery REAL
            NOT NULL DEFAULT 0.0,

            attempts INTEGER
            NOT NULL DEFAULT 0,

            correct_answers INTEGER
            NOT NULL DEFAULT 0,

            misconceptions TEXT
            NOT NULL DEFAULT '',

            status TEXT
            NOT NULL DEFAULT 'not_started',

            UNIQUE(
                student_id,
                topic,
                concept
            ),

            FOREIGN KEY(student_id)
            REFERENCES students(id)
        )
    """)

    connection.commit()

    connection.close()


# ============================================================
# STUDENT FUNCTIONS
# ============================================================

def get_or_create_student(
    name: str,
    level: str = "beginner",
):
    """Get an existing student or create a new one."""

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, name, level

        FROM students

        WHERE name = ?
        """,
        (name,),
    )

    student = cursor.fetchone()

    # --------------------------------------------------------
    # EXISTING STUDENT
    # --------------------------------------------------------

    if student:

        connection.close()

        return student

    # --------------------------------------------------------
    # CREATE NEW STUDENT
    # --------------------------------------------------------

    cursor.execute(
        """
        INSERT INTO students (
            name,
            level
        )

        VALUES (?, ?)
        """,
        (
            name,
            level,
        ),
    )

    connection.commit()

    student_id = cursor.lastrowid

    connection.close()

    return (
        student_id,
        name,
        level,
    )


# ============================================================
# TOPIC PROGRESS FUNCTIONS
# ============================================================

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
        (
            student_id,
            topic,
        ),
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

    # Convert misconception list into text.
    misconception_text = "\n".join(
        misconceptions
    )

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

        ON CONFLICT(
            student_id,
            topic
        )

        DO UPDATE SET

            mastery =
                excluded.mastery,

            attempts =
                excluded.attempts,

            correct_answers =
                excluded.correct_answers,

            misconceptions =
                excluded.misconceptions
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


# ============================================================
# CONCEPT PROGRESS FUNCTIONS
# ============================================================

def load_concept_progress(
    student_id: int,
    topic: str,
    concept: str,
):
    """
    Load saved progress for one specific concept.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT

            mastery,

            attempts,

            correct_answers,

            misconceptions,

            status

        FROM concept_progress

        WHERE student_id = ?

        AND topic = ?

        AND concept = ?
        """,
        (
            student_id,
            topic,
            concept,
        ),
    )

    progress = cursor.fetchone()

    connection.close()

    return progress


def load_all_concept_progress(
    student_id: int,
    topic: str,
):
    """
    Load progress for all concepts
    belonging to a specific topic.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT

            concept,

            mastery,

            attempts,

            correct_answers,

            misconceptions,

            status

        FROM concept_progress

        WHERE student_id = ?

        AND topic = ?

        ORDER BY concept
        """,
        (
            student_id,
            topic,
        ),
    )

    rows = cursor.fetchall()

    connection.close()

    return rows


def save_concept_progress(
    student_id: int,
    topic: str,
    concept: str,
    mastery: float,
    attempts: int,
    correct_answers: int,
    misconceptions: list,
    status: str,
):
    """
    Save or update progress for
    one specific learning concept.
    """

    connection = get_connection()

    cursor = connection.cursor()

    # Convert misconception list into text.
    misconception_text = "\n".join(
        misconceptions
    )

    cursor.execute(
        """
        INSERT INTO concept_progress (

            student_id,

            topic,

            concept,

            mastery,

            attempts,

            correct_answers,

            misconceptions,

            status
        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?)

        ON CONFLICT(
            student_id,
            topic,
            concept
        )

        DO UPDATE SET

            mastery =
                excluded.mastery,

            attempts =
                excluded.attempts,

            correct_answers =
                excluded.correct_answers,

            misconceptions =
                excluded.misconceptions,

            status =
                excluded.status
        """,
        (
            student_id,
            topic,
            concept,
            mastery,
            attempts,
            correct_answers,
            misconception_text,
            status,
        ),
    )

    connection.commit()

    connection.close()