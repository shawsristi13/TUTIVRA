# ============================================================
# TUTIVRA - ADAPTIVE AI LEARNING TUTOR
# Streamlit Dashboard
# ============================================================

import sys
import os
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

from app.rag.rag_service import (
    ingest_document,
    ask_from_material,
    load_knowledge_base,
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
# SESSION STATE
# ============================================================

DEFAULT_STATE = {
    "student": None,
    "topic": None,
    "learning_session": None,
    "question_data": None,
    "last_result": None,
    "lesson": None,
    "started": False,

    # RAG
    "rag_ready": False,
    "rag_filename": "",
    "rag_pages": 0,
    "rag_chunks": 0,
}


for key, value in DEFAULT_STATE.items():

    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def create_learning_session(student, topic):
    """
    Create an adaptive learning session.
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
    Generate the first adaptive question.
    """

    summary = student.get_summary(topic)

    adaptation = get_adaptation_decision(
        mastery=summary["mastery"],
        attempts=summary["attempts"],
        correct_answers=summary["correct_answers"],
        misconception_detected=False,
    )

    material_context = ""

    if st.session_state.get(
        "rag_ready",
        False,
    ):

        material_context = get_material_context(
            query=f"{topic} core concepts",
            top_k=5,
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
        material_context=material_context,
    )

    if not isinstance(result, dict):
        return None

    question = result.get(
        "question",
        "",
    )

    expected_answer = result.get(
        "expected_answer",
        "",
    )

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


def normalize_next_question(
    next_question,
    adaptation,
):
    """
    Convert the adaptive session question
    into dashboard format.
    """

    if not next_question:
        return None

    if not isinstance(
        next_question,
        dict,
    ):
        return None

    question = next_question.get(
        "question",
        "",
    )

    if not question:
        return None

    return {
        "question": question,

        "expected_answer": next_question.get(
            "expected_answer",
            "",
        ),

        "difficulty": (
            adaptation.get(
                "difficulty",
                "adaptive",
            )
            if adaptation
            else "adaptive"
        ),

        "strategy": (
            adaptation.get(
                "strategy",
                "",
            )
            if adaptation
            else ""
        ),

        "question_type": (
            adaptation.get(
                "question_type",
                "adaptive",
            )
            if adaptation
            else "adaptive"
        ),

        "reason": (
            adaptation.get(
                "reason",
                "",
            )
            if adaptation
            else ""
        ),
    }


def reset_learning_state():
    """
    Reset active learning session.
    Database progress is NOT deleted.
    """

    st.session_state.learning_session = None
    st.session_state.question_data = None
    st.session_state.last_result = None
    st.session_state.lesson = None
    st.session_state.started = False

    st.session_state.student = None
    st.session_state.topic = None


def process_pdf(uploaded_file):
    """
    Save and process uploaded PDF using RAG.
    """

    upload_dir = PROJECT_ROOT / "rag_uploads"

    upload_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    pdf_path = upload_dir / uploaded_file.name

    with open(
        pdf_path,
        "wb",
    ) as file:

        file.write(
            uploaded_file.getbuffer()
        )

    result = ingest_document(
        str(pdf_path)
    )

    st.session_state.rag_ready = True

    st.session_state.rag_filename = (
        result["filename"]
    )

    st.session_state.rag_pages = (
        result["pages"]
    )

    st.session_state.rag_chunks = (
        result["chunks"]
    )

    return result
def get_material_context(
    query: str,
    top_k: int = 5,
) -> str:
    """
    Retrieve relevant content from the uploaded
    study material.
    """

    try:

        retriever = load_knowledge_base()

        results = retriever.retrieve(
            query=query,
            top_k=top_k,
        )

        if not results:
            return ""

        context_parts = []

        for result in results:

            document = result.get(
                "document",
                {},
            )

            text = document.get(
                "text",
                "",
            )

            page = document.get(
                "page",
                "unknown",
            )

            if text.strip():

                context_parts.append(
                    f"[Page {page}]\n{text}"
                )

        return "\n\n".join(
            context_parts
        )

    except Exception:
        return ""

# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 48px;
        font-weight: 750;
        margin-bottom: 0;
    }

    .subtitle {
        font-size: 20px;
        opacity: 0.7;
        margin-bottom: 30px;
    }

    .question-box {
        padding: 25px;
        border-radius: 12px;
        border: 1px solid rgba(128,128,128,0.25);
        margin: 15px 0;
    }

    .section-title {
        font-size: 28px;
        font-weight: 650;
        margin-top: 15px;
    }

    .setup-box {
        padding: 25px;
        border-radius: 15px;
        border: 1px solid rgba(128,128,128,0.25);
        margin-top: 15px;
        margin-bottom: 20px;
    }

    .material-box {
        padding: 20px;
        border-radius: 12px;
        border: 1px solid rgba(128,128,128,0.25);
        margin: 15px 0;
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
# START SCREEN
# ============================================================

if not st.session_state.started:

    # --------------------------------------------------------
    # WELCOME
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">'
        "Welcome to Tutivra"
        "</div>",
        unsafe_allow_html=True,
    )

    st.write(
        """
        Tutivra is an adaptive AI learning tutor that
        understands your performance and adjusts your
        learning experience accordingly.
        """
    )

    st.divider()


    # ========================================================
    # STUDENT INFORMATION
    # ========================================================

    st.markdown(
        '<div class="section-title">'
        "Student Information"
        "</div>",
        unsafe_allow_html=True,
    )

    entered_name = st.text_input(
        "Your name",
        placeholder="Enter your name",
        key="setup_student_name",
    )


    # ========================================================
    # STUDY SETUP
    # ========================================================

    st.markdown(
        '<div class="section-title">'
        "What do you want to learn?"
        "</div>",
        unsafe_allow_html=True,
    )

    st.write(
        """
        You can enter a topic, upload your study material,
        or use both together.
        """
    )


    # --------------------------------------------------------
    # TOPIC
    # --------------------------------------------------------

    entered_topic = st.text_input(
        "Topic",
        placeholder=(
            "Example: Binary Search, DBMS, Operating Systems..."
        ),
        key="setup_topic",
    )


    st.write("**OR upload your study material**")


    # --------------------------------------------------------
    # PDF UPLOAD
    # --------------------------------------------------------

    uploaded_file = st.file_uploader(
        "Upload study material",
        type=["pdf"],
        key="setup_pdf",
        help="Upload lecture notes, textbooks, syllabus material, etc.",
    )


    # --------------------------------------------------------
    # MATERIAL PREVIEW
    # --------------------------------------------------------

    if uploaded_file is not None:

        st.info(
            f"Selected material: **{uploaded_file.name}**"
        )


    st.divider()


    # ========================================================
    # WHAT TUTIVRA PROVIDES
    # ========================================================

    st.markdown(
        '<div class="section-title">'
        "Your Learning Experience"
        "</div>",
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)


    with col1:

        st.info(
            """
            ### 🧠 Personalized

            Lessons are generated according
            to your learning level.
            """
        )


    with col2:

        st.info(
            """
            ### 🎯 Adaptive

            Question difficulty changes
            according to your performance.
            """
        )


    with col3:

        st.info(
            """
            ### 📖 Material Based

            Ask questions directly from
            your uploaded study material.
            """
        )


    st.divider()


    # ========================================================
    # START LEARNING
    # ========================================================

    if st.button(
        "🚀 Start Learning",
        type="primary",
        use_container_width=True,
        key="start_learning",
    ):

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if not entered_name.strip():

            st.error(
                "Please enter your name."
            )

            st.stop()


        if (
            not entered_topic.strip()
            and uploaded_file is None
        ):

            st.error(
                "Please enter a topic or upload a PDF."
            )

            st.stop()


        # ----------------------------------------------------
        # DETERMINE TOPIC
        # ----------------------------------------------------

        if entered_topic.strip():

            topic = entered_topic.strip()

        else:

            # If only PDF was uploaded,
            # use the filename as the topic.
            topic = Path(
                uploaded_file.name
            ).stem


        # ----------------------------------------------------
        # LOAD STUDENT
        # ----------------------------------------------------

        with st.spinner(
            "Loading your learning profile..."
        ):

            try:

                student = load_student(
                    entered_name,
                    topic,
                )

            except Exception as error:

                st.error(
                    "Tutivra could not load your "
                    "learning profile."
                )

                st.exception(error)

                st.stop()


        # ----------------------------------------------------
        # PROCESS PDF
        # ----------------------------------------------------

        if uploaded_file is not None:

            with st.spinner(
                "Tutivra is processing your study material..."
            ):

                try:

                    result = process_pdf(
                        uploaded_file
                    )

                    st.success(
                        "Study material processed successfully."
                    )

                    st.caption(
                        f"{result['pages']} pages • "
                        f"{result['chunks']} chunks"
                    )

                except Exception as error:

                    st.error(
                        "Tutivra could not process the PDF."
                    )

                    st.exception(error)

                    st.stop()


        # ----------------------------------------------------
        # CREATE LEARNING SESSION
        # ----------------------------------------------------

        st.session_state.student = student

        st.session_state.topic = topic

        st.session_state.learning_session = (
            create_learning_session(
                student,
                topic,
            )
        )

        st.session_state.question_data = None
        st.session_state.last_result = None
        st.session_state.lesson = None
        st.session_state.started = True

        st.rerun()


    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("📚 Tutivra")

    st.write(
        f"**Student:** "
        f"{st.session_state.student.name}"
    )

    st.write(
        f"**Topic:** "
        f"{st.session_state.topic}"
    )

    st.divider()


    # --------------------------------------------------------
    # PROGRESS
    # --------------------------------------------------------

    student = st.session_state.student

    current_topic = st.session_state.topic

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
        f"**Attempts:** "
        f"{summary['attempts']}"
    )

    st.write(
        f"**Correct:** "
        f"{summary['correct_answers']}"
    )


    # --------------------------------------------------------
    # MISCONCEPTIONS
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # STUDY MATERIAL STATUS
    # --------------------------------------------------------

    if st.session_state.rag_ready:

        st.divider()

        st.subheader(
            "📖 Study Material"
        )

        st.success(
            "Material ready"
        )

        st.caption(
            st.session_state.rag_filename
        )

        st.caption(
            f"{st.session_state.rag_pages} pages • "
            f"{st.session_state.rag_chunks} chunks"
        )


    # --------------------------------------------------------
    # NEW SESSION
    # --------------------------------------------------------

    st.divider()

    if st.button(
        "🔄 New Learning Session",
        use_container_width=True,
    ):

        reset_learning_state()

        st.rerun()


# ============================================================
# ACTIVE STUDENT
# ============================================================

student = st.session_state.student

topic = st.session_state.topic

summary = student.get_summary(
    topic
)


# ============================================================
# MAIN TOPIC HEADER
# ============================================================

st.markdown(
    f"## 📚 {topic}"
)

st.caption(
    f"Learning with Tutivra • "
    f"{student.level.capitalize()} level"
)


# ============================================================
# PROGRESS HEADER
# ============================================================

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
# STUDY MATERIAL
# ============================================================

st.divider()

st.markdown(
    "## 📖 Study Material"
)

if st.session_state.rag_ready:

    st.success(
        f"Currently learning from: "
        f"{st.session_state.rag_filename}"
    )

    material_col1, material_col2 = st.columns(2)

    with material_col1:

        st.metric(
            "Pages",
            st.session_state.rag_pages,
        )

    with material_col2:

        st.metric(
            "Text Chunks",
            st.session_state.rag_chunks,
        )


else:

    st.info(
        """
        No study material has been uploaded.

        You can still use Tutivra's AI-generated
        lessons and adaptive practice.
        """
    )


# ============================================================
# ASK FROM STUDY MATERIAL
# ============================================================

if st.session_state.rag_ready:

    st.markdown(
        "### 💬 Ask Tutivra"
    )

    st.write(
        "Ask questions based specifically on your uploaded material."
    )

    rag_question = st.text_area(
        "Your question",
        placeholder=(
            "Example: Explain binary search according "
            "to the uploaded material."
        ),
        key="rag_question",
    )

    if st.button(
        "Ask Tutivra",
        type="primary",
        use_container_width=True,
        key="ask_from_material",
    ):

        if not rag_question.strip():

            st.warning(
                "Please enter a question."
            )

        else:

            with st.spinner(
                "Tutivra is searching your study material..."
            ):

                try:

                    answer = ask_from_material(
                        question=rag_question,
                        top_k=3,
                    )

                    st.markdown(
                        "### 🤖 Tutivra's Answer"
                    )

                    st.write(
                        answer
                    )

                except Exception as error:

                    st.error(
                        "Tutivra could not answer "
                        "from the study material."
                    )

                    st.caption(
                        str(error)
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

                material_context = ""

                if st.session_state.get(
                    "rag_ready",
                    False,
                ):

                    material_context = get_material_context(
                        query=f"{topic} concepts explanation",
                        top_k=5,
                    )


                lesson = create_lesson(
                    topic=topic,
                    level=student.level,
                    language="English",
                    goal=(
                        f"Understand {topic}, "
                        "solve basic problems, and "
                        "build a strong conceptual foundation."
                    ),
                    material_context=material_context,
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
        Tutivra selects the difficulty based on
        your current mastery and learning history.
        """
    )

    if st.button(
        "Generate Question",
        type="primary",
        use_container_width=True,
        key="generate_question",
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

                st.exception(error)


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


    # --------------------------------------------------------
    # CORRECT / INCORRECT
    # --------------------------------------------------------

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

    delta = (
        new_mastery
        - old_mastery
    )


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
    # ADAPTATION
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

    normalized_next = (
        normalize_next_question(
            next_question,
            adaptation,
        )
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
            key="next_question",
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