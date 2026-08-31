from app.student.student_model import StudentModel
from app.learning.adaptive_session import AdaptiveLearningSession
from app.ai.question_generator import generate_question
from app.adaptation.difficulty_engine import get_adaptation_decision


class TutivraApplication:

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

    def __init__(self):
        self.student = None
        self.topic = None
        self.concept = None
        self.session_questions = 0
        self.session_correct = 0
        self.starting_mastery = 0.0

    def run(self):

        self.print_header()

        self.create_student()

        self.choose_topic()

        self.start_session()

    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def print_header(self):

        print("\n" + "=" * 60)
        print("                    TUTIVRA")
        print("             Adaptive AI Learning Tutor")
        print("=" * 60)

    def create_student(self):

        name = input("\nEnter your name: ").strip()

        while not name:
            print("Name cannot be empty.")
            name = input("Enter your name: ").strip()

        self.student = StudentModel(
            name=name,
            level="beginner",
        )

    def choose_topic(self):

        print("\nAvailable Topics:")

        for index, topic in enumerate(
            self.TOPICS,
            start=1,
        ):
            print(f"{index}. {topic}")

        print("\n0. Enter a custom topic")

        while True:

            choice = input("\nChoose a topic: ").strip()

            if choice == "0":

                topic = input(
                    "Enter your topic: "
                ).strip()

                if topic:
                    self.topic = topic
                    break

            elif choice.isdigit():

                number = int(choice)

                if 1 <= number <= len(self.TOPICS):

                    self.topic = self.TOPICS[
                        number - 1
                    ]

                    break

            print("Invalid choice. Try again.")

    # --------------------------------------------------
    # SESSION
    # --------------------------------------------------

    def start_session(self):

        self.student.load_from_database(
            self.topic
        )

        self.starting_mastery = (
            self.student.get_mastery(
                self.topic
            )
        )

        print("\n" + "=" * 60)
        print("              LEARNING SESSION")
        print("=" * 60)

        print(f"\nStudent: {self.student.name}")
        print(f"Topic: {self.topic}")
        print(
            f"Current Mastery: "
            f"{self.starting_mastery:.1f}%"
        )

        print("\nStarting Tutivra...\n")

        self.concept = self.detect_concept()

        self.run_question_loop()

    # --------------------------------------------------
    # CONCEPT
    # --------------------------------------------------

    def detect_concept(self):

        concepts = {
            "Arrays":
                "array fundamentals and operations",

            "Linked List":
                "linked list structure and traversal",

            "Binary Search":
                "how binary search works and why sorted data is required",

            "Sorting":
                "sorting algorithms and their basic principles",

            "Stack":
                "stack operations and LIFO behavior",

            "Queue":
                "queue operations and FIFO behavior",

            "Recursion":
                "recursive functions and base cases",

            "Trees":
                "tree structure and traversal",

            "Graphs":
                "graph representation and traversal",
        }

        return concepts.get(
            self.topic,
            f"fundamentals of {self.topic}",
        )

    # --------------------------------------------------
    # QUESTION LOOP
    # --------------------------------------------------

    def run_question_loop(self):

        MAX_QUESTIONS = 5

        question_data = self.generate_first_question()

        while (
            self.session_questions
            < MAX_QUESTIONS
        ):

            if not question_data:

                print(
                    "\nTutivra could not generate "
                    "the next question."
                )

                break

            print("\n" + "-" * 60)

            question_number = (
                self.session_questions + 1
            )

            print(
                f"QUESTION {question_number}"
            )

            print("-" * 60)

            print(
                f"Difficulty: "
                f"{question_data['difficulty']}"
            )

            print(
                f"Type: "
                f"{question_data['question_type']}"
            )

            print(
                f"\n{question_data['question']}"
            )

            answer = input(
                "\nYour answer: "
            ).strip()

            if not answer:

                print(
                    "\nPlease provide an answer."
                )

                continue

            result = self.process_answer(
                question_data,
                answer,
            )

            if result is None:
                break

            question_data = result

        self.show_session_summary()

    # --------------------------------------------------
    # FIRST QUESTION
    # --------------------------------------------------

    def generate_first_question(self):

        mastery = self.student.get_mastery(
            self.topic
        )

        attempts = self.student.attempts.get(
            self.topic,
            0,
        )

        correct = self.student.correct_answers.get(
            self.topic,
            0,
        )

        misconceptions = (
            self.student.misconceptions.get(
                self.topic,
                [],
            )
        )

        adaptation = get_adaptation_decision(
            mastery=mastery,
            attempts=attempts,
            correct_answers=correct,
            misconception_detected=bool(
                misconceptions
            ),
        )

        question = generate_question(
            topic=self.topic,
            concept=self.concept,
            student_level=self.student.level,
            mastery=mastery,
            misconceptions=misconceptions,
            difficulty=adaptation["difficulty"],
            strategy=adaptation["strategy"],
            question_type=adaptation["question_type"],
        )

        if question.get("error"):
            print(
                "\nQuestion generation error:"
            )
            print(question["error"])
            return None

        return question

    # --------------------------------------------------
    # ANSWER PROCESSING
    # --------------------------------------------------

    def process_answer(
        self,
        question_data,
        answer,
    ):

        session = AdaptiveLearningSession(
            student=self.student,
            topic=self.topic,
            concept=self.concept,
        )

        print("\nProcessing answer...\n")

        result = session.process_answer(
            question=question_data["question"],
            expected_answer=question_data[
                "expected_answer"
            ],
            student_answer=answer,
        )

        evaluation = result["evaluation"]

        if evaluation.get("system_error"):

            print(
                "\nTutivra could not evaluate "
                "this answer."
            )

            print(
                evaluation.get(
                    "feedback",
                    "Please try again.",
                )
            )

            return None

        self.session_questions += 1

        if evaluation["correct"]:
            self.session_correct += 1

        self.show_evaluation(
            evaluation,
            result["student_state"],
            result["adaptation"],
        )

        next_question = result[
            "next_question"
        ]

        if next_question is None:
            return None

        if next_question.get("error"):
            print(
                "\nTutivra could not generate "
                "the next question."
            )
            return None

        return next_question

    # --------------------------------------------------
    # EVALUATION DISPLAY
    # --------------------------------------------------

    def show_evaluation(
        self,
        evaluation,
        state,
        adaptation,
    ):

        print("\n" + "=" * 60)
        print("                  EVALUATION")
        print("=" * 60)

        print(
            f"\nCorrect: "
            f"{evaluation['correct']}"
        )

        print(
            f"Understanding: "
            f"{evaluation['understanding_level']}"
        )

        print(
            f"Misconception detected: "
            f"{evaluation['misconception_detected']}"
        )

        print(
            f"\nFeedback:\n"
            f"{evaluation['feedback']}"
        )

        print("\n" + "-" * 60)

        print("UPDATED PROGRESS")

        print(
            f"Mastery: "
            f"{state['mastery']:.1f}%"
        )

        print(
            f"Attempts: "
            f"{state['attempts']}"
        )

        print(
            f"Correct: "
            f"{state['correct_answers']}"
        )

        print(
            f"\nNext difficulty: "
            f"{adaptation['difficulty']}"
        )

    # --------------------------------------------------
    # SUMMARY
    # --------------------------------------------------

    def show_session_summary(self):

        final_mastery = (
            self.student.get_mastery(
                self.topic
            )
        )

        accuracy = (
            (
                self.session_correct
                / self.session_questions
            )
            * 100
            if self.session_questions
            else 0
        )

        print("\n\n" + "=" * 60)
        print("              SESSION COMPLETE")
        print("=" * 60)

        print(
            f"\nStudent: "
            f"{self.student.name}"
        )

        print(
            f"Topic: "
            f"{self.topic}"
        )

        print(
            f"\nStarting Mastery: "
            f"{self.starting_mastery:.1f}%"
        )

        print(
            f"Final Mastery: "
            f"{final_mastery:.1f}%"
        )

        print(
            f"\nQuestions Attempted: "
            f"{self.session_questions}"
        )

        print(
            f"Correct Answers: "
            f"{self.session_correct}"
        )

        print(
            f"Accuracy: "
            f"{accuracy:.1f}%"
        )

        misconceptions = (
            self.student.misconceptions.get(
                self.topic,
                [],
            )
        )

        print("\nAreas to improve:")

        if misconceptions:

            for item in misconceptions:
                print(f"- {item}")

        else:

            print("- No recorded misconceptions")

        print("\n" + "=" * 60)
        print("             END OF SESSION")
        print("=" * 60 + "\n")