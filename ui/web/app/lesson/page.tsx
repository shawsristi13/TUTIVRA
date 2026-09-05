"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { useSession } from "@/components/SessionProvider";
import { createLesson, setupStudent } from "@/lib/api";

export default function LessonPage() {
  const router = useRouter();
  const { session, update } = useSession();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!session.topic) { router.replace("/content"); return; }
    if (session.lessonText) return; // already generated
    generateLesson();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function generateLesson() {
    setLoading(true);
    setError("");
    try {
      // Register student so adaptive progress is tracked
      await setupStudent(session.studentName || "Student", session.studentLevel, session.topic);

      const res = await createLesson({
        topic: session.topic,
        student_level: session.studentLevel,
        language: session.language,
        goal: session.goal,
        material_context: session.materialContext,
        available_time_minutes: session.availableTimeMinutes,
        subject_area: session.subjectArea,
      });
      update({ lessonText: res.lesson });
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  const steps = [
    { icon: "🧠", label: "Analysing topic" },
    { icon: "📋", label: "Structuring lesson plan" },
    { icon: "🎯", label: "Personalising for your level" },
    { icon: "✍️", label: "Writing lesson content" },
  ];

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-0 w-96 h-96 rounded-full bg-indigo-900/15 blur-3xl" />
        <div className="absolute bottom-1/4 right-0 w-96 h-96 rounded-full bg-purple-900/15 blur-3xl" />
      </div>

      <div className="w-full max-w-3xl z-10">
        <div className="text-center mb-8">
          <div className="text-5xl mb-3">📋</div>
          <h1 className="text-3xl font-bold text-slate-100">
            {loading ? "Planning Your Lesson…" : session.lessonText ? "Your Lesson is Ready" : "Lesson Generation"}
          </h1>
          <p className="text-slate-400 mt-2">
            Topic: <span className="text-indigo-400 font-medium">{session.topic}</span>
            {" · "}{session.language}{" · "}{session.availableTimeMinutes} min{" · "}{session.studentLevel}
          </p>
        </div>

        {loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="bg-slate-900/60 border border-slate-700/40 rounded-2xl p-8 backdrop-blur-sm"
          >
            <div className="space-y-4">
              {steps.map((s, i) => (
                <motion.div
                  key={s.label}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.4 }}
                  className="flex items-center gap-3 text-slate-400"
                >
                  <span className="text-xl">{s.icon}</span>
                  <span className="text-sm">{s.label}</span>
                  <span className="ml-auto text-xs text-indigo-400 animate-pulse">…</span>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}

        {!loading && session.lessonText && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div className="bg-slate-900/60 border border-slate-700/40 rounded-2xl p-6 backdrop-blur-sm max-h-[55vh] overflow-y-auto">
              <div className="prose prose-invert prose-sm max-w-none whitespace-pre-wrap text-slate-300 leading-relaxed">
                {session.lessonText}
              </div>
            </div>

            <div className="flex gap-4">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={generateLesson}
                className="px-6 py-3 rounded-xl text-slate-300 border border-slate-700 bg-slate-800 hover:bg-slate-700 transition-all text-sm"
              >
                ↺ Regenerate
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => router.push("/teach")}
                className="flex-1 py-3 rounded-xl font-semibold text-white bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 transition-all shadow-lg shadow-purple-900/30"
              >
                Start AI Teaching Session →
              </motion.button>
            </div>
          </motion.div>
        )}

        {error && (
          <div className="bg-red-900/20 border border-red-800/40 rounded-2xl p-6 text-center">
            <p className="text-red-400 text-sm mb-4">{error}</p>
            <button
              onClick={generateLesson}
              className="px-6 py-2 rounded-xl bg-red-700/40 text-red-300 hover:bg-red-700/60 text-sm transition-all"
            >
              Retry
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
