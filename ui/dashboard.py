# ============================================================
# TUTIVRA - ADAPTIVE AI LEARNING TUTOR
# Streamlit Dashboard
# ============================================================

import sys
from pathlib import Path


# ============================================================
# PROJECT ROOT / IMPORT FIX
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# IMPORTS
# ============================================================

import streamlit as st

from app.student.student_model import StudentModel
from app.learning.adaptive_session import AdaptiveLearningSession
from app.ai.teaching_engine import create_lesson
from app.ai.question_generator import generate_question
from app.adaptation.difficulty_engine import (
    get_adaptation_decision,
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Tutivra",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# TOPICS
# ============================================================

TOPICS = [
    "Arrays",
    "Linked List",
    "Binary Search",
    "Sorting",
    "Stack",
    "Queue",
    "Recursion",
    "Trees",
    "Graphs",
]


# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================

DEFAULT_STATE = {
    "student": None,
    "topic": None,
    "learning_session": None,
    "question_data": None,
    "last_result": None,
    "lesson": None,
    "started": False,
}


for key, value in DEFAULT_STATE.items():

    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def create_learning_session(student, topic):
    """
    Create an adaptive learning session for the selected topic.
    """

    return AdaptiveLearningSession(
        student=student,
        topic=topic,
        concept=f"Core concepts of {topic}",
        language="English",
    )


def load_student(name, topic):
    """
    Create StudentModel and load saved progress.
    """

    student = StudentModel(
        name=name.strip(),
        level="beginner",
    )

    student.load_from_database(topic)

    return student


def generate_first_question(student, topic):
    """
    Generate the first adaptive question based on
    the student's current state.
    """

    summary = student.get_summary(topic)

    adaptation = get_adaptation_decision(
        mastery=summary["mastery"],
        attempts=summary["attempts"],
        correct_answers=summary["correct_answers"],
        misconception_detected=False,
    )

    result = generate_question(
        topic=topic,
        concept=f"Core concepts of {topic}",
        student_level=student.level,
        mastery=summary["mastery"],
        misconceptions=summary["misconceptions"],
        difficulty=adaptation["difficulty"],
        strategy=adaptation["strategy"],
        question_type=adaptation["question_type"],
    )

    if not isinstance(result, dict):
        return None

    question = result.get("question", "")
    expected_answer = result.get("expected_answer", "")

    if not question:
        return None

    return {
        "question": question,
        "expected_answer": expected_answer,
        "difficulty": adaptation["difficulty"],
        "strategy": adaptation["strategy"],
        "question_type": adaptation["question_type"],
        "reason": adaptation["reason"],
    }


def normalize_next_question(next_question, adaptation):
    """
    Convert the question-generator result returned by the
    adaptive session into the format used by the dashboard.
    """

    if not next_question:
        return None

    if not isinstance(next_question, dict):
        return None

    question = next_question.get("question", "")

    if not question:
        return None

    return {
        "question": question,
        "expected_answer": next_question.get(
            "expected_answer",
            "",
        ),
        "difficulty": (
            adaptation.get("difficulty", "adaptive")
            if adaptation
            else "adaptive"
        ),
        "strategy": (
            adaptation.get("strategy", "")
            if adaptation
            else ""
        ),
        "question_type": (
            adaptation.get("question_type", "adaptive")
            if adaptation
            else "adaptive"
        ),
        "reason": (
            adaptation.get("reason", "")
            if adaptation
            else ""
        ),
    }


def reset_learning_state():
    """
    Reset only the active learning session.
    Saved database progress is NOT deleted.
    """

    st.session_state.learning_session = None
    st.session_state.question_data = None
    st.session_state.last_result = None
    st.session_state.lesson = None
    st.session_state.started = False


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 0;
    }

    .subtitle {
        font-size: 18px;
        opacity: 0.7;
        margin-bottom: 25px;
    }

    .question-box {
        padding: 25px;
        border-radius: 12px;
        border: 1px solid rgba(128,128,128,0.25);
        margin: 15px 0;
    }

    .section-title {
        font-size: 25px;
        font-weight: 650;
        margin-top: 15px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🎓 Tutivra</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    "Adaptive AI Learning Tutor"
    "</div>",
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("⚙️ Learning Setup")

    entered_name = st.text_input(
        "Student name",
        value=(
            st.session_state.student.name
            if st.session_state.student
            else ""
        ),
        placeholder="Enter your name",
    )

    selected_topic = st.selectbox(
        "Choose topic",
        TOPICS,
        index=(
            TOPICS.index(st.session_state.topic)
            if st.session_state.topic in TOPICS
            else 0
        ),
    )

    st.divider()

    if st.session_state.student:

        student = st.session_state.student

        current_topic = selected_topic

        summary = student.get_summary(
            current_topic
        )

        st.subheader("📊 Your Progress")

        st.metric(
            "Mastery",
            f"{summary['mastery']:.1f}%",
        )

        st.progress(
            min(
                max(
                    summary["mastery"] / 100,
                    0.0,
                ),
                1.0,
            )
        )

        st.write(
            f"**Attempts:** {summary['attempts']}"
        )

        st.write(
            f"**Correct:** "
            f"{summary['correct_answers']}"
        )

        if summary["misconceptions"]:

            st.divider()

            st.subheader(
                "⚠️ Areas to Improve"
            )

            for misconception in summary[
                "misconceptions"
            ]:

                st.write(
                    f"• {misconception}"
                )

    st.divider()

    if st.session_state.started:

        if st.button(
            "🔄 New Learning Session",
            use_container_width=True,
        ):

            reset_learning_state()

            st.rerun()


# ============================================================
# TOPIC CHANGE HANDLING
# ============================================================

if (
    st.session_state.started
    and st.session_state.topic != selected_topic
):

    if not entered_name.strip():

        st.error(
            "Please enter your name."
        )

        st.stop()

    student = load_student(
        entered_name,
        selected_topic,
    )

    st.session_state.student = student
    st.session_state.topic = selected_topic

    st.session_state.learning_session = (
        create_learning_session(
            student,
            selected_topic,
        )
    )

    st.session_state.question_data = None
    st.session_state.last_result = None
    st.session_state.lesson = None

    st.rerun()


# ============================================================
# START SCREEN
# ============================================================

if not st.session_state.started:

    st.markdown(
        '<div class="section-title">'
        "Welcome to Tutivra"
        "</div>",
        unsafe_allow_html=True,
    )

    st.write(
        """
        Tutivra is an adaptive AI tutor that changes the
        difficulty of learning based on your performance.
        """
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.info(
            """
            ### 🧠 Adaptive

            Questions become easier or harder based
            on your mastery and misconceptions.
            """
        )

    with col2:

        st.info(
            """
            ### 📈 Progress

            Your mastery, attempts and correct answers
            are saved for future sessions.
            """
        )

    with col3:

        st.info(
            """
            ### 🤖 AI Tutor

            Tutivra evaluates your explanation and
            adjusts the teaching strategy.
            """
        )

    st.divider()

    if st.button(
        "🚀 Start Learning",
        type="primary",
        use_container_width=True,
    ):

        if not entered_name.strip():

            st.error(
                "Please enter your name."
            )

        else:

            with st.spinner(
                "Loading your learning profile..."
            ):

                student = load_student(
                    entered_name,
                    selected_topic,
                )

            st.session_state.student = student
            st.session_state.topic = selected_topic

            st.session_state.learning_session = (
                create_learning_session(
                    student,
                    selected_topic,
                )
            )

            st.session_state.question_data = None
            st.session_state.last_result = None
            st.session_state.lesson = None
            st.session_state.started = True

            st.rerun()

    st.stop()


# ============================================================
# ACTIVE STUDENT
# ============================================================

student = st.session_state.student
topic = st.session_state.topic

summary = student.get_summary(topic)


# ============================================================
# PROGRESS HEADER
# ============================================================

st.markdown(
    f"## 📚 {topic}"
)

progress1, progress2, progress3 = st.columns(3)

with progress1:

    st.metric(
        "Mastery",
        f"{summary['mastery']:.1f}%",
    )

with progress2:

    st.metric(
        "Attempts",
        summary["attempts"],
    )

with progress3:

    st.metric(
        "Correct",
        summary["correct_answers"],
    )


st.progress(
    min(
        max(
            summary["mastery"] / 100,
            0.0,
        ),
        1.0,
    )
)


# ============================================================
# PERSONALIZED LESSON
# ============================================================

st.divider()

with st.expander(
    "🧠 Personalized Lesson",
    expanded=False,
):

    st.write(
        "Tutivra can create a lesson based on your "
        "current level and learning goal."
    )

    if st.button(
        "Generate Personalized Lesson",
        key="generate_lesson",
    ):

        with st.spinner(
            "Tutivra is preparing your lesson..."
        ):

            try:

                lesson = create_lesson(
                    topic=topic,
                    level=student.level,
                    language="English",
                    goal=(
                        f"Understand {topic}, "
                        "solve basic problems, and "
                        "build a strong conceptual foundation."
                    ),
                )

                st.session_state.lesson = lesson

            except Exception as error:

                st.error(
                    "Tutivra could not generate the lesson."
                )

                st.caption(
                    str(error)
                )

    if st.session_state.lesson:

        st.markdown(
            st.session_state.lesson
        )


# ============================================================
# GENERATE FIRST QUESTION
# ============================================================

if st.session_state.question_data is None:

    st.divider()

    st.markdown(
        "## 🎯 Adaptive Practice"
    )

    st.write(
        """
        Tutivra will select the appropriate difficulty
        using your current mastery and learning history.
        """
    )

    if st.button(
        "Generate Question",
        type="primary",
        use_container_width=True,
    ):

        with st.spinner(
            "Tutivra is generating an adaptive question..."
        ):

            try:

                question_data = (
                    generate_first_question(
                        student,
                        topic,
                    )
                )

            except Exception as error:

                question_data = None

                st.error(
                    "Tutivra could not generate a question."
                )

                st.caption(
                    str(error)
                )

        if question_data:

            st.session_state.question_data = (
                question_data
            )

            st.session_state.last_result = None

            st.rerun()

        else:

            st.error(
                "The AI returned an invalid question. "
                "Please try again."
            )

    st.stop()


# ============================================================
# CURRENT QUESTION
# ============================================================

question_data = (
    st.session_state.question_data
)

question = question_data.get(
    "question",
    "",
)

difficulty = question_data.get(
    "difficulty",
    "adaptive",
)

question_type = question_data.get(
    "question_type",
    "adaptive",
)


st.divider()

st.markdown(
    "## ❓ Your Question"
)

q1, q2 = st.columns(2)

with q1:

    st.caption(
        f"Difficulty: **{difficulty}**"
    )

with q2:

    st.caption(
        f"Question type: **{question_type}**"
    )


st.markdown(
    f"""
    <div class="question-box">
    <h3>{question}</h3>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# ANSWER FORM
# ============================================================

with st.form(
    key="answer_form",
    clear_on_submit=False,
):

    student_answer = st.text_area(
        "Your answer",
        height=180,
        placeholder=(
            "Explain your answer in your own words..."
        ),
    )

    submitted = st.form_submit_button(
        "Submit Answer",
        type="primary",
        use_container_width=True,
    )


# ============================================================
# PROCESS ANSWER
# ============================================================

if submitted:

    if not student_answer.strip():

        st.warning(
            "Please write an answer before submitting."
        )

    else:

        with st.spinner(
            "Tutivra is evaluating your answer..."
        ):

            try:

                result = (
                    st.session_state.learning_session
                    .process_answer(
                        question=question,
                        expected_answer=question_data.get(
                            "expected_answer",
                            "",
                        ),
                        student_answer=student_answer,
                    )
                )

                st.session_state.last_result = result

                st.session_state.question_data = None

                st.rerun()

            except Exception as error:

                st.error(
                    "Tutivra encountered an error "
                    "while processing your answer."
                )

                st.exception(error)


# ============================================================
# EVALUATION RESULT
# ============================================================

if st.session_state.last_result:

    result = st.session_state.last_result

    evaluation = result.get(
        "evaluation",
        {},
    )

    student_state = result.get(
        "student_state",
        {},
    )

    adaptation = result.get(
        "adaptation",
        None,
    )

    next_question = result.get(
        "next_question",
        None,
    )


    st.divider()

    st.markdown(
        "## 📊 Evaluation"
    )


    correct = evaluation.get(
        "correct"
    )


    if correct is True:

        st.success(
            "✅ Correct! Good work."
        )

    elif correct is False:

        st.error(
            "❌ Not quite. Let's strengthen this concept."
        )

    else:

        st.warning(
            "⚠️ Tutivra could not reliably evaluate "
            "this answer."
        )


    # --------------------------------------------------------
    # FEEDBACK
    # --------------------------------------------------------

    feedback = evaluation.get(
        "feedback",
        "",
    )

    if feedback:

        st.write(
            f"**Feedback:** {feedback}"
        )


    # --------------------------------------------------------
    # UNDERSTANDING
    # --------------------------------------------------------

    understanding = evaluation.get(
        "understanding_level",
        student.level,
    )

    st.write(
        f"**Understanding level:** "
        f"{understanding}"
    )


    # --------------------------------------------------------
    # MISCONCEPTION
    # --------------------------------------------------------

    if evaluation.get(
        "misconception_detected",
        False,
    ):

        st.warning(
            "⚠️ Tutivra detected a misconception."
        )

        misconception = evaluation.get(
            "misconception",
            "",
        )

        if misconception:

            st.write(
                f"**Detected issue:** "
                f"{misconception}"
            )


    # ========================================================
    # UPDATED PROGRESS
    # ========================================================

    st.markdown(
        "## 📈 Updated Progress"
    )

    old_mastery = summary["mastery"]

    new_mastery = student_state.get(
        "mastery",
        old_mastery,
    )

    delta = new_mastery - old_mastery

    m1, m2, m3 = st.columns(3)

    with m1:

        st.metric(
            "Mastery",
            f"{new_mastery:.1f}%",
            delta=f"{delta:+.1f}%",
        )

    with m2:

        st.metric(
            "Attempts",
            student_state.get(
                "attempts",
                0,
            ),
        )

    with m3:

        st.metric(
            "Correct",
            student_state.get(
                "correct_answers",
                0,
            ),
        )

    st.progress(
        min(
            max(
                new_mastery / 100,
                0.0,
            ),
            1.0,
        )
    )


    # ========================================================
    # ADAPTATION DECISION
    # ========================================================

    if adaptation:

        st.markdown(
            "## 🤖 Tutivra Adapted"
        )

        a1, a2, a3 = st.columns(3)

        with a1:

            st.write(
                "**Next difficulty**"
            )

            st.info(
                adaptation.get(
                    "difficulty",
                    "adaptive",
                )
            )

        with a2:

            st.write(
                "**Strategy**"
            )

            st.info(
                adaptation.get(
                    "strategy",
                    "continue",
                )
            )

        with a3:

            st.write(
                "**Question type**"
            )

            st.info(
                adaptation.get(
                    "question_type",
                    "adaptive",
                )
            )

        reason = adaptation.get(
            "reason",
            "",
        )

        if reason:

            st.caption(
                reason
            )


    # ========================================================
    # NEXT QUESTION
    # ========================================================

    normalized_next = normalize_next_question(
        next_question,
        adaptation,
    )


    if normalized_next:

        st.divider()

        st.markdown(
            "## 🚀 Continue"
        )

        st.write(
            "Tutivra has selected your next question "
            "based on this answer."
        )

        if st.button(
            "➡️ Next Question",
            type="primary",
            use_container_width=True,
        ):

            st.session_state.question_data = (
                normalized_next
            )

            st.session_state.last_result = None

            st.rerun()

    else:

        st.info(
            "Tutivra does not have another question ready yet."
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Tutivra • Adaptive AI Learning Tutor"
)