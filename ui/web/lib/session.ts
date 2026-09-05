// Session state that flows across all pages
export interface TutivraSession {
  // Setup
  studentName: string;
  studentLevel: "beginner" | "intermediate" | "advanced";
  topic: string;
  goal: string;
  language: string;
  languageCode: string;
  availableTimeMinutes: number;
  subjectArea: string;

  // Content
  materialContext: string;
  ragReady: boolean;

  // Lesson
  lessonText: string;

  // Teach
  scenes: import("./api").Scene[];
  currentSceneIndex: number;
  sceneAssets: Record<string, { visualHtml?: string; audioUrl?: string; videoUrl?: string }>;

  // Q&A
  sessionInteractions: Array<{
    question: string;
    expectedAnswer: string;
    studentAnswer: string;
    evaluation: Record<string, unknown>;
  }>;
  sessionCorrect: number;
  misconceptions: string[];
  weakConcepts: string[];

  // Assessment
  assessmentQuestions: Record<string, unknown>[];
  assessmentAnswers: Record<string, string>;
  assessmentResult: Record<string, unknown> | null;

  // Report
  report: Record<string, unknown> | null;
}

export const DEFAULT_SESSION: TutivraSession = {
  studentName: "",
  studentLevel: "beginner",
  topic: "",
  goal: "",
  language: "English",
  languageCode: "en",
  availableTimeMinutes: 10,
  subjectArea: "",
  materialContext: "",
  ragReady: false,
  lessonText: "",
  scenes: [],
  currentSceneIndex: 0,
  sceneAssets: {},
  sessionInteractions: [],
  sessionCorrect: 0,
  misconceptions: [],
  weakConcepts: [],
  assessmentQuestions: [],
  assessmentAnswers: {},
  assessmentResult: null,
  report: null,
};

// ─── Language definitions ────────────────────────────────────
// Extend this list to add more languages trivially.
export const SUPPORTED_LANGUAGES: Array<{ label: string; value: string; code: string; flag: string }> = [
  { label: "English", value: "English", code: "en", flag: "🇬🇧" },
  { label: "Hindi", value: "Hindi", code: "hi", flag: "🇮🇳" },
  { label: "Bengali", value: "Bengali", code: "bn", flag: "🇧🇩" },
  { label: "Tamil", value: "Tamil", code: "ta", flag: "🇮🇳" },
  { label: "Telugu", value: "Telugu", code: "te", flag: "🇮🇳" },
  { label: "Marathi", value: "Marathi", code: "mr", flag: "🇮🇳" },
];

// ─── Subject area definitions ────────────────────────────────
export const SUBJECT_AREAS = [
  "General",
  "Mathematics",
  "Physics",
  "Chemistry",
  "Biology",
  "History",
  "Geography",
  "Computer Science",
  "Programming",
  "Economics",
  "Literature",
  "Science",
];
