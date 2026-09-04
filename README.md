# 🎓 Tutivra — Adaptive AI Learning Tutor

> An AI-powered adaptive learning platform that personalizes learning based on student performance and uploaded study materials.

Tutivra is designed to move beyond the traditional **one-size-fits-all learning approach**. It combines AI-powered content generation, adaptive questioning, student performance tracking, and Retrieval-Augmented Generation (RAG) to create a more personalized learning experience.

---

## 🚀 Features

### 🧠 Personalized Learning

Tutivra adapts the learning experience based on the student's:

- Learning level
- Current mastery
- Number of attempts
- Correct answers
- Recorded misconceptions

---

### 🎯 Adaptive Question Generation

The system dynamically determines the next learning challenge using an adaptive difficulty engine.

Based on student performance, Tutivra can determine:

- Question difficulty
- Learning strategy
- Question type

The learning cycle follows:

**Generate Question → Student Answer → AI Evaluation → Progress Update → Adaptation → Next Question**

---

### 🤖 AI Answer Evaluation

Tutivra evaluates student responses using AI instead of relying only on exact keyword matching.

The evaluator analyzes:

- Student answer
- Question
- Expected answer
- Topic
- Student level

It provides information such as:

- Correctness
- Feedback
- Understanding level
- Misconception detection

---

### 📊 Student Performance Tracking

Tutivra maintains a student learning profile containing information such as:

- Mastery
- Attempts
- Correct answers
- Misconceptions

This information is used to influence future adaptive learning decisions.

---

### 📖 Study Material Upload

Students can upload PDF study materials such as:

- Lecture notes
- Textbooks
- Study resources
- Educational documents

The material is processed and prepared for retrieval.

---

### 🔎 RAG-Based Learning

Tutivra uses a Retrieval-Augmented Generation pipeline to work with uploaded study material.

The general pipeline is:

```text
PDF Upload
    ↓
Document Processing
    ↓
Text Chunking
    ↓
Knowledge Base / Vector Storage
    ↓
Relevant Content Retrieval
    ↓
AI-Powered Learning Support
